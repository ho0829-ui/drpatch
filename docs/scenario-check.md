# 대표 시나리오·완료 기준 점검 (2026-11-18, 3일차)

실행: 서버(`uvicorn app.main:app`) + 실제 GMS(gpt-6-luna) + 실제 API, `scripts/run_scenarios.py` (HTTP로 /upload·/chat 호출).
입력 파일: 패키지 6개 + `-e git+…` + `celery>=4.0` (조회 제외 2줄).

## 대표 요청 (spec "대표 요청")
| # | 요청 | 결과 | 판정 |
|---|---|---|---|
| 1 | "Ubuntu 20.04, Python 3.8 서버야. 이 파일 기준으로 이번에 5개 올릴 계획 짜줘. 첫 점검은 11/21 22~24시, 격주로" | 27.6초, Tool 29번(실패 0), 재계획 2번(3.10 종료 → 3.11). 1회차 [pyyaml CRITICAL, Python 3.8→3.11, Ubuntu 20.04, jinja2] / 2회차 [django, requests, flask, urllib3] — Python 업그레이드가 필요한 패키지는 모두 2회차 | 통과 |
| 2 | "Python 3.8 서버인데 django 몇으로 올리면 돼?" (새 세션) | 사실 조회, Tool 2번. "3.8에서 설치 가능한 최신은 4.2.30, 취약점 8개" — 코드가 계산한 값 | 통과 |
| 3 | "Ubuntu 20.04, Python 3.8 서버인데 지금 뭐부터 해야 돼?" (파일 있음) | 처음엔 일정을 되묻기만 함(Tool 0번) → **고침 (spec v1.14)**: 29.4초, Tool 29번, 우선순위 [pyyaml, Python 3.8→3.11, Ubuntu, jinja2, django, requests, flask, urllib3] — Python 업그레이드가 필요한 것은 업그레이드 뒤 — 를 보여 주고 일정만 되물음 | 고친 뒤 통과 |
| 4 | "계획 짜줘" (파일 없음) | 빠진 6가지만 되물음, Tool 0번 | 통과 |
| 5 | "1회차 확정해줘" | 처음엔 1·2회차 모두 저장 → **고침**: 1회차만 저장 (Analysis.confirm_rounds) | 고친 뒤 통과 |

## 완료 기준 (spec "완료 기준")
| 기준 | 확인 | 근거 |
|---|---|---|
| "5개까지" → 위험한 것부터 회차, 현재→목표·이유 | ✅ | 시나리오 1, 화면 회차 카드 |
| 현재 Python에서 설치 안 되는 버전은 목표로 안 나옴 | ✅ | `test_planner.py`, 시나리오 1(Python 업그레이드 뒤 회차로) |
| 업그레이드뿐이면 업그레이드가 앞 회차 | ✅ | 시나리오 1, `test_spec_example_priority_and_rounds` |
| `-e`·`>=` 줄은 조회 제외, 오류 없음 | ✅ | 업로드 결과 "7번 줄 PyPI 출처 아님, 8번 줄 정확한 버전 아님" |
| 파일 없이 "계획 짜줘" → Tool 없이 묻기 | ✅ | 시나리오 4 |
| 한 Tool 실패해도 나머지 진행, "확인 못 함" | ✅ | `test_one_tool_failure_marks_only_that_package`, `test_review_2_*` |
| 겹치는 계획 저장 → 둘 다 저장 + 알림 | ✅ | 브라우저 확인(⚠ 경고), `test_overlap_warning_but_both_saved` |
| 로그 탭에서 순서·버전·재계획 이유 | ✅ | 브라우저 로그 탭: judgment·replan·plan_built |
| 로깅 멈춰도 대화 정상 | ✅ | `test_events.py` 4가지 경우 |
| 패키지 20개도 지장 없는 시간 | ✅ 기준 **60초 이내 + 실행 단계 실시간 표시** | 20개: 36.8초 → 재계획 후보 병렬 조회 후 35.2초 (Tool 65번, 실패 0) |

## 20개 응답 시간 내역 (개선 후)
| 단계 | 시간 | 비고 |
|---|---|---|
| analyze (LLM) | 4.3s | |
| plan_tools (LLM) | 4.5s | |
| call_tools | 5.5s | 동시 4개 |
| judge | 2.7s | 목표 버전 재조회 병렬 |
| replan | 8.3s (12.7s에서) | LLM 재계획 방식 선택 + 후보 버전 미리 병렬 조회 |
| respond (LLM) | 9.7s | |

남은 시간의 대부분(약 21초)은 LLM 4번. 더 줄이려면 LLM 호출 수를 줄여야 함 (예: 재계획 방식 선택을 사용자가 거부 표현을 했을 때만 LLM에 묻기) — 지금은 기준 안이라 그대로 둠.

---

# 대표 요청 5유형 재검증 (2026-11-20, 제출 전)

실행: 서버(`uvicorn app.main:app`, `CALENDAR_BACKEND=local`) + 실제 GMS + 실제 API. 요청마다 `/upload` 후 `/chat` 한 번. 처리 시간은 `/chat` 요청부터 마지막 줄(final)까지.
실행 로그 원본: [`docs/logs/`](logs/) — 요청마다 로깅 Agent가 저장한 이벤트 전체(`GET /logs/{session_id}`)와 최종 응답. 7건 모두 화면 스트림 이벤트와 저장 로그의 순서·종류가 같음(41/84/46/41/5/41/38건).

| # | 유형 | 요청 (파일) | 기대 | 실제 최종 응답 (요약) | 실행 로그 (단계 · Tool · 재계획) | 차이 · 원인 · 수정 | 처리 시간 |
|---|---|---|---|---|---|---|---|
| 1 | 한 번에 충족 | "Ubuntu 24.04, Python 3.12 … 한 번에 3개, 11/24 22~24시, 매주" (requests 2.19.0 · jinja2 2.10 · pyyaml 5.1) | 재계획 없이 1회차에 3개 | 1회차 11/24: pyyaml 5.1→6.0.3(CRITICAL), requests 2.19.0→2.34.2(HIGH), jinja2 2.10→3.1.6(HIGH) | analyze → plan_tools → call_tools → judge → build → respond · Tool 12회(실패 0) · 재계획 0 | 없음 | 17.1초 |
| 2 | 재계획 | "Ubuntu 20.04, Python 3.8 … 5개, 11/24 22~24시, 격주" (패키지 6 + 제외 2줄) | 3.8에서 안전 버전 불가 → Python을 올리는 재계획 | 재계획 2회(3.10 지원 종료 → 3.11 지원 중). 1회차 11/24: pyyaml·Python 3.8→3.11·Ubuntu 20.04(목표 미상)·jinja2 / 2회차 12/8: django 2.2.0→5.2.19 등 Python 3.11 뒤에 설치할 4개 | … judge → **replan** → build … · Tool 31회(실패 0) · llm_decision replan_strategy=upgrade_python · replan #1 3.10, #2 3.11 · 같은 인자 재호출 0건 | 없음 | 25.6초 |
| 3 | 상한 도달 | "Ubuntu 24.04, Python 3.7 … 3개, 11/24 22~24시, 매주" (idna 2.7) | 재계획 3회에서 멈추고 보류 + 사유 | Python 3.8·3.9·3.10이 모두 지원 종료라 목표를 정하지 못함 → "재계획 상한(3회)에 도달해 보류", idna 보류. Python 3.7 업그레이드 항목은 1회차에 남음(목표 미상) | … judge(violation: idna) → replan → build … · replan #1 3.8, #2 3.9, #3 3.10(모두 지원 종료), `{result: hold, reason: 재계획 상한(3회)에 도달했습니다}` · 무한 반복 없음 | 처음엔 jinja2 2.10으로 시도 → 3.7에서도 안전한 3.1.6이 설치돼 재계획이 일어나지 않음(기대가 틀림). 3.7에서 설치되는 최신 idna 3.10에도 취약점이 남는 idna로 바꿈. 1회차가 11/25로 옮겨진 것은 같은 서버에 넣어 둔 11/24 일정(아래 F3023) 때문 | 28.0초 |
| 4 | Tool 하나 실패 | 1번과 같은 요청, OS만 "Ubuntu 99.04" | get_eol(ubuntu 99.04) 실패, 나머지 계획은 정상 | 1번과 같은 3개 계획 + "OS EOL은 확인 못 했습니다" | Tool 12회 중 1회 실패: `get_eol {ubuntu, 99.04} → PRODUCT_NOT_FOUND` (로그에 error_code) · 다음 단계 계속 | 없음. 바로 이어 보낸 다른 요청("Python 3.8 서버인데 django 몇으로?")도 정상(2026-11-20 1차 확인) | 14.5초 |
| 5 | Tool 불필요 | "안녕하세요" (파일 없음) | Tool 호출 없이 응답 | 인사 + 파일·OS·Python을 알려 달라는 안내 | analyze(intent=other) → other · Tool 0회 | 없음 | 6.2초 |

처리 시간: 계획 요청 14~28초, Tool이 필요 없는 요청 6초. 기다리는 동안 단계 칩·실행 로그가 실시간으로 보여(화면 확인 2026-11-20) 사용에 지장 없음. 패키지 20개는 35.2초(위 1차 기록).

## 심화 F3023 ↔ 필수 결과 비교 (같은 요청, 캘린더 켬 / 끔)

요청: 1번과 같음 ("Ubuntu 24.04, Python 3.12 … 첫 점검 11/24 22~24시, 매주", requests·jinja2·pyyaml). 캘린더 켬 서버에는 내 일정 "정기 배포" 11/24 21:00~23:30을 넣어 둠.

| 항목 | 필수만 (`CALENDAR_BACKEND=off`) | 심화 F3023 (`local`, 일정 있음) |
|---|---|---|
| 1회차 날짜 | 2026-11-24 (요청 그대로) | **2026-11-25** (`moved_from: 2026-11-24`, 일정과 시간 겹침 → 다음 빈 날) |
| 회차 항목·목표 버전 | pyyaml 5.1→6.0.3, requests 2.19.0→2.34.2, jinja2 2.10→3.1.6 | 같음 (캘린더는 날짜만 바꿈) |
| Tool 호출 | 11회 | 12회 (+ `list_calendar_events` 1회, local Tool) |
| `calendar_check` 이벤트 | "사용 안 함" | "확인함", 회차별 `moved_from`·`conflicts` |
| 응답 문장 | "1회차는 2026-11-24에 진행합니다" | "1회차, 2026-11-25 … 2026-11-24에서 옮겨졌군요" |
| 처리 시간 | 15.1초 | 16.6초 |
| 확정 시 | plans 저장만 | plans 저장 + 회차마다 `add_calendar_event`(plan_id만 입력) — 같은 계획을 다시 확정해도 새로 만들지 않음 |

로그: [`logs/F3023_캘린더끔.json`](logs/F3023_캘린더끔.json) · [`logs/F3023_캘린더켬.json`](logs/F3023_캘린더켬.json)

### 구현체 교체 (로컬 → Google Calendar)

- `app/calendar/google.py`: `GoogleCalendar` — `CalendarBackend`와 같은 메서드·같은 일정 모양. Google Calendar API v3를 `requests`로 부르고(새 라이브러리 없음), 이 서비스가 넣은 일정은 `extendedProperties.private`에 `source`·`plan_id`를 남긴다. `.env`: `CALENDAR_BACKEND=google`, `GOOGLE_CALENDAR_TOKEN`(OAuth access token), `GOOGLE_CALENDAR_ID`, `GOOGLE_CALENDAR_TZ`.
- `tests/test_calendar_google.py`(5개): Google API를 흉내 낸 가짜 서버에 붙여, **같은 Tool 호출을 로컬·Google 두 구현체에 보내 결과를 나란히 비교** — `add_calendar_event`·`list_calendar_events` 출력이 id만 빼고 같음, 재확정 시 `created: false`, 일정 삭제 결과 같음, 겹치는 회차 이동 결과 같음(11/21 → 11/22), Google 실패(401·연결 실패·토큰 없음)는 `CALENDAR_ERROR`.
- 한계: 실제 Google 계정 연결(OAuth 토큰 발급)은 하지 않아, 실제 Google 서버와의 왕복은 확인하지 않았다.
