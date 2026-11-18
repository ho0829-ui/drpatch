# 아키텍처 (v1 · 2026-11-18)

> 기준: docs/spec.md v1.7. 이 문서는 "어디에 무엇을 두고, 요청 하나가 어떻게 흐르는지"만 정한다. 규칙(목표 버전·재계획·회차)은 spec이 원본.


## 1. 전체 모양

```
브라우저 (web/: HTML·CSS·JS, 탭 3개)
   │  fetch · /chat은 스트리밍(ndjson)
   ▼
FastAPI (app/main.py) ── 화면 파일도 같은 서버(8000)가 내보냄 → CORS 없음
   ├─ app/api/upload.py   POST /upload            → app/parsing (파일 → 조회·제외 목록)
   ├─ app/api/chat.py     POST /chat               → app/agent (LangGraph)
   ├─ app/api/plans.py    /plans CRUD + 겹침 경고  → app/db
   └─ app/api/logs.py     /logs 조회·삭제          → app/db
                                   │
app/agent (메인 Agent)             │ 이벤트 발행 (기다리지 않음)
   ├─ graph.py   분석→되묻기→계획→Tool 호출→판단→재계획→응답
   ├─ planner/   순수 함수: 목표 버전·우선순위·회차 나누기·Python 구하기 (LLM 안 씀)
   └─ app/tools  Tool 3종 + 레지스트리 (완료)
                                   ▼
app/events  EventBus ──► 로깅 Agent (별도 스레드, 큐 구독 → SQLite events 표)
                    └──► 그 요청의 화면 스트림 (실행 단계 실시간 표시)
```

## 2. 폴더

```
app/
  main.py            앱 생성, 라우터 연결, web/ 정적 파일 연결, 시작 시 DB·로깅 Agent 기동
  llm.py             (완료) GMS LLM 생성
  api/               라우터 4개. 요청·응답 형식은 pydantic (schemas.py)
  agent/
    state.py         그래프 상태 (조건·Tool 결과·판단·재계획 횟수)
    graph.py         LangGraph 노드와 연결
    prompts.py       의도 분류·조건 추출·Tool 계획·되묻기·응답 문장
    planner/         versions.py · priority.py · rounds.py · python_upgrade.py (순수 함수 + 테스트)
    runner.py        Tool 펼쳐 부르기: 패키지별 반복, 동시 호출 수 제한, 요청 안 캐시
  tools/             (완료) http·eol·vulns·package_versions·registry
  parsing/           (완료) requirements.txt
  events/
    bus.py           publish()는 큐에 넣고 바로 돌아옴. 구독자별 큐
    logger.py        로깅 Agent: 큐에서 꺼내 SQLite 저장. LLM 안 씀
  db/
    schema.sql       sessions · plans · events
    repo.py          sqlite3 (표준 라이브러리) 읽기·쓰기
web/
  index.html  style.css
  js/api.js  chat.js  plans.js  logs.js   (탭별 파일, 프레임워크 없음)
```

의존 방향: `api → agent → (planner, tools)` / `agent → events` / `api → db`. tools·planner·parsing은 FastAPI·LangGraph를 모른다 (NF3006 모듈 분리).

## 3. POST /chat 한 번의 흐름

| 단계 (그래프 노드) | 누가 | 하는 일 | 발행 이벤트 |
|---|---|---|---|
| analyze | LLM | 의도 분류(계획 수립/사실 조회/확정/그 밖), OS·Python·N·날짜·간격 추출 → 세션 조건에 **바뀐 것만** 덮어씀 (F3005, F3010) | step_start/end, llm_decision |
| ask | LLM | 빠진 입력이 있으면 Tool 부르지 않고 빠진 것만 되물음 → 끝 | step |
| plan | LLM | 부를 Tool **종류와 순서**만 정함 (예: get_eol → get_vulns → get_package_versions) (F3006) | llm_decision(계획·이유) |
| call_tools | 코드 | 계획을 패키지별로 펼쳐 병렬 호출(동시 4개), 실패는 "확인 못 함"으로 두고 진행 (F3007) | tool_call/tool_result(소요 시간) |
| judge | 코드 | planner 순수 함수: 목표 버전, 위반 여부, 우선순위 (F3008) | step, judgment |
| replan | 코드+LLM | 위반 있으면 Python 줄기 올려 get_eol·get_vulns. **이미 받은 결과 재사용**(요청 안 캐시). 상한 3회 (F3009) | replan(횟수·이유) |
| respond | LLM | 회차별 계획 + 근거(Tool 결과) + 제외 사유 문장 (F3011) | step |

- "확정해줘"는 그래프가 아니라 api가 직접 plans 표에 저장 (Tool 아님).
- 세션 조건(패키지 목록·OS·Python·N·날짜·간격)은 sessions 표에 저장, API 결과는 저장 안 함 (spec Memory).

## 4. 이벤트와 로깅 Agent (F3012~F3013)

- 이벤트 모양: `{session_id, seq, type, payload, created_at}`. seq는 세션 안 순번.
- `bus.publish()`는 구독자 큐에 `put_nowait`만 한다. 큐가 가득 차거나 로깅 Agent가 죽어도 메인은 기다리지 않음 → "로깅 꺼도 대화 정상" 테스트.
- 로깅 Agent = 앱 시작 때 뜨는 스레드 하나. 큐 → events 표 INSERT. UPDATE 없음 (로그 수정 불가, F3014).
- 구현 (2026-11-18): `app/events/bus.py`(EventBus, 큐 10,000개, 넘치면 버리고 `dropped`로 셈), `app/events/logger.py`(LoggingAgent), `app/db/`(schema.sql·repo.py, DB 파일은 `.env`의 `DB_PATH`, 기본 `data/sudo_patch.db`).
- 이벤트 종류: `step_start` / `step_end`(단계 요약 포함: analyze 종료에 의도·이유) / `tool_call` / `tool_result`(ms·error_code) / `llm_decision`(intent·tool_plan·replan_strategy와 이유) / `judgment` / `replan`(회차·Python·이유) / `error`.

## 5. 동기·비동기 방식

- Tool은 `requests`(동기)라서 **Agent 실행 전체를 작업 스레드에서 동기로** 돌린다. 병렬 호출은 `ThreadPoolExecutor(max_workers=4)`.
- FastAPI 엔드포인트는 그 스레드를 띄우고, 이벤트 큐를 읽어 화면에 흘려보낸다.
- 이유: async로 다 바꾸면 Tool·테스트를 다시 짜야 함. 3일 일정엔 스레드가 단순하다.

## 6. 화면 (F3018~F3019)

- 대화 탭: 파일 올리기 → 조회·제외 목록 표시 → 채팅. 옆 패널에 실행 단계·Tool 호출이 순서대로 쌓이고, 재계획 지점은 색으로 구분. 처리 중 표시.
- 계획 관리 탭: 회차 목록(날짜순), 항목별 현재 → 목표 버전·이유, 겹침 경고, 수정·삭제 후 목록 다시 불러오기.
- 실행 로그 탭: 세션 목록 → 이벤트 순서대로.
- 오류: 화면엔 짧은 안내만 (예: "취약점 정보를 확인하지 못했어요"). API 키 누락은 "서버 설정(키)을 확인하세요" (NF3002).
- 하단: "참고용 정보" + 세 API 출처 표기 (NF3007).

## 7. 실행 단계를 화면에 보여주는 방법 — 스트리밍 응답 (2026-11-18 결정)

- `POST /chat`은 `application/x-ndjson`(JSON 한 줄 = 이벤트 하나)으로 응답을 흘려보낸다. 마지막 줄은 `{"type": "final", ...}`(최종 답·회차 계획·조회 제외 목록).
- 서버: 요청마다 EventBus에 구독 큐를 하나 붙이고, Agent 스레드가 발행하는 이벤트를 꺼내는 대로 내보낸다. 같은 이벤트가 로깅 Agent 큐에도 들어간다.
- 화면: `fetch()` 응답 본문을 줄 단위로 읽어 실행 단계 패널에 쌓는다. `replan` 이벤트는 색으로 구분. 스트림이 끊기면 "연결이 끊겼어요" 안내.
- 화면에 보내는 이벤트에는 오류 상세·키를 넣지 않는다 (NF3002). 상세는 로그 표에만.
- 버린 선택지: 한 번에 응답(기다리는 동안 단계가 안 보임), 폴링(요청 수·끝 판단 코드).
