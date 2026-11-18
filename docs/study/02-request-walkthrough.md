# 2. 요청 하나 따라가기

예시: 파일을 올린 세션에서 "우분투 20 서버, 파이썬 3.8이야. 이번에 2개까지, 첫 점검은 11/21 22~24시, 격주로 계획 짜줘"를 보낸다.
결과: 1회차 [Python 3.8→3.11, Ubuntu 20.04] / 2회차 [django 2.2.0→5.2.19, requests 2.19.0→2.34.2], 재계획 2번.

> 옆에 띄워 둘 것: 화면 **실행 로그 탭**에서 이 요청의 세션. 아래 단계 번호 옆의 `[로그]`가 그 탭에 보이는 줄이다.

---

## 0단계. 파일 올리기 — `POST /upload`
- 화면: [web/js/api.js](../../web/js/api.js) `upload` → `fetch("/upload", {body: file})` (파일 내용을 본문 그대로)
- 서버: [app/api/upload.py](../../app/api/upload.py) `upload`
  1. `parse_bytes(raw)` — [parsing/requirements.py](../../app/parsing/requirements.py): 인코딩 판단(UTF-16도) → 줄마다 조회/제외(이유)
  2. `save_upload(session_id, packages, excluded)` — [agent/session.py](../../app/agent/session.py): sessions 표에 패키지 목록 저장
- 핵심: 파싱은 **Tool이 아니다**. 계산이라 코드가 한다.

## 1단계. 메시지 보내기 — `POST /chat`
- 화면: [web/js/chat.js](../../web/js/chat.js) `send` → [api.js](../../web/js/api.js) `chat`이 응답 본문을 **줄 단위로 읽는다** (ndjson 스트리밍).
- 서버: [app/api/chat.py](../../app/api/chat.py) `chat`
  1. 이벤트 버스에 구독 큐를 하나 붙인다 (`bus.subscribe()`).
  2. **작업 스레드**에서 `chat_turn`을 돌린다 (`work`).
  3. `stream`이 큐에서 이 세션의 이벤트를 꺼내는 대로 한 줄씩 보낸다 → 화면 오른쪽 "실행 단계"가 실시간으로 쌓인다.
- 왜 스레드? Tool이 `requests`(동기)라서 Agent 전체를 동기로 돌리고, 기다리는 동안 스트림은 계속 내보내야 하기 때문 ([architecture.md](../architecture.md) 5절).

## 2단계. 세션 불러오기 — `chat_turn`
- [agent/session.py](../../app/agent/session.py) `chat_turn`: `load_session` → `run_agent(..., last_turn=직전 대화)` → `save_session`
- Memory(F3010): 조건 + 직전 메시지·답·제안 계획을 저장. **API 결과는 저장하지 않는다** (매번 다시 조회).

## 3단계. 그래프 시작 — `run_agent` / `build_graph`
- [agent/graph.py](../../app/agent/graph.py) `run_agent`가 `ToolRunner`를 만들고 `build_graph(...).invoke(...)`.
- 노드마다 `step()`이 `step_start`/`step_end` 이벤트를 앞뒤로 붙인다 → `[로그] 요청 분석 #1`.

## 4단계. analyze (LLM) `[로그] LLM 판단 · 의도: plan`
- `brain.analyze` → [brain.py](../../app/agent/brain.py) `GmsBrain.analyze`: `with_structured_output(Analysis)`로 **정해진 모양(JSON)**으로 받는다 (intent, os_name, os_version="20", python_version, capacity=2, first_date, window, interval_days=14).
- `merge_conditions`(코드): 이번에 나온 값만 덮어쓰기. "20" → `normalize_os_version` → "20.04".
- `missing_inputs`(코드): 빠진 필수값이 있으면 → `ask` 노드 → 고정 문장으로 되묻고 끝 (Tool 0번).
- 생각해 볼 것: 되묻는 문장은 왜 LLM이 아니라 코드가 만들까? ([spec](../spec.md) v1.9, LLM이 spec 밖 정보까지 물었던 실측)

## 5단계. plan_tools (LLM) `[로그] Tool 순서: get_eol → get_vulns → get_package_versions`
- LLM은 **Tool 이름과 순서만** 고른다. 빠뜨린 Tool은 코드가 붙인다(`added_by_code`).
- F3006 "계획을 세운다"를 지키는 자리.

## 6단계. call_tools (코드) `[로그] get_eol(ubuntu 20.04) ✓ 805ms …`
- 패키지마다 펼치는 건 코드: `runner.call_many([...])` — 동시 4개 ([runner.py](../../app/agent/runner.py)).
- `runner.call` → `registry.call` ([tools/registry.py](../../app/tools/registry.py)): 이름 확인 → 입력 검사(pydantic) → 실행 → 출력 모양 검사. **어떤 경우에도 예외를 던지지 않고** `{ok:false, error:{code}}`.
- 실제 HTTP는 [tools/http.py](../../app/tools/http.py) `fetch_json` 한 곳. 404/429/5xx/타임아웃 → 실패 코드.
- 같은 호출은 요청 안에서 캐시 → 같은 버전을 두 번 묻지 않는다 (F3009).
- 취약점이 0건인 패키지는 버전 목록을 받지 않는다 (시간 절약).
- 모든 Tool이 같은 이유로 실패하면 → 판단으로 가지 않고 바로 안내 (`tools_down`).

## 7단계. judge (코드) `[로그] 판단: 지금 Python으로는 안전한 버전이 없음 → requests, django`
- 패키지마다: 현재 등급(`top_severity`) → Python 3.8에서 설치 가능한 최신 정식 버전(`pick_latest`) → 그 버전을 다시 조회.
  - requests: 2.32.4 → 취약점 1건 남음 → **위반**
  - django: 4.2.30 → 8건 남음 → **위반**
- "위반" = 지금 Python으로는 안전한 버전에 갈 수 없다 → 재계획으로.

## 8단계. replan (LLM + 코드) `[로그] 재계획 1회 · Python 3.10 / 2회 · Python 3.11`
1. LLM: 업그레이드할지 보류할지(`choose_replan`). 사용자가 거부하지 않았으니 upgrade_python.
2. 코드: 후보 버전 취약점을 미리 병렬 조회(`candidate_versions`) → `plan_python_upgrade`
   - 패키지마다 Python 줄기를 올려 보며 0건이 처음 나오는 줄기: django 3.10(5.2.19), requests 3.10(2.34.2) → 후보 **3.10**
   - get_eol(python 3.10) → 2026-10-01 이미 종료 → 재계획 1회 → 다음 줄기
   - 3.11 → 2027-10-31까지 지원 → 재계획 2회, 확정
- 공부 포인트: "재계획 1회"를 무엇으로 세는지 ([spec](../spec.md) "재계획"), 상한 3회.

## 9단계. build (코드) `[로그] 회차 배정: 1회차 [Python, Ubuntu] · 2회차 [django, requests]`
- `build_items` → 항목 만들기 (Python 항목 하나로 합치기, 안전·확인 못 함·보류 목록 나누기)
- `sort_items` → CRITICAL > HIGH > … , 같으면 지원 종료가 빠른 순 → django, Python, Ubuntu, requests
- `split_rounds` → **순서 제약이 먼저**: django는 CRITICAL이어도 Python 업그레이드 다음 회차 → 2회차
- 공부 포인트: 왜 정렬 순서(django 첫째)와 회차 순서(django 2회차)가 다를까?

## 10단계. respond (LLM) → 최종 줄
- `write_response`: 계산 결과를 바꾸지 말고 설명만 하라고 시킨다. 실패하면 `fallback_text`(코드 문장).
- [chat.py](../../app/api/chat.py) `stream`이 마지막 줄 `{"type":"final", answer, plan, ...}`을 보내고, 화면이 회차 카드를 그린다 ([render.js](../../web/js/render.js) `planView`).

## 옆에서 계속 일어나는 일: 이벤트와 로깅
- 노드·runner가 `emit(...)` → [events/bus.py](../../app/events/bus.py) `publish`: 구독자 큐에 넣고 **바로 돌아온다**.
- 구독자 1: 이 요청의 스트림(화면). 구독자 2: [events/logger.py](../../app/events/logger.py) 로깅 Agent(별도 스레드) → SQLite events 표.
- 로깅이 멈춰도 대화는 계속 (`tests/test_events.py`의 4가지 경우).

## 확정 — "1회차 확정해줘"
- analyze가 `intent=confirm`, `confirm_rounds=[1]` → 그래프는 Tool 없이 끝.
- [chat.py](../../app/api/chat.py)가 `save_confirmed_plan`으로 1회차만 plans 표에 저장, 겹치는 계획(`find_overlaps`)을 같이 돌려준다.
