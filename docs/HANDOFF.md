# 마지막 갱신: 2026-11-18 16:25 / 작성: Claude Code

## 지금 하던 것
- 2일차 [C] 이벤트 버스 + 로깅 Agent 끝 (전체 테스트 183개 통과, 실제 GMS 한 건 → 이벤트 46개 SQLite 저장 확인)
  - app/events/bus.py: EventBus.publish(session_id, type, payload) — 큐에 넣고 바로 돌아옴, 예외 없음, 세션별 seq. emitter(session_id)를 run_agent(emit=)에 꽂음
  - app/events/logger.py: LoggingAgent(bus, db_path).start()/stop() — 별도 스레드, 원본 그대로 INSERT, LLM 안 씀, DB 실패해도 계속
  - app/db/schema.sql(sessions·plans·events) + repo.py(events: insert·list_log_sessions·get_events·delete_events, 수정 함수 없음)
  - app/main.py lifespan: init_db → EventBus → LoggingAgent 시작/정지 (app.state.bus, app.state.logger)
  - graph: step_end에 단계 요약 (analyze 종료 = 의도·이유)

## 다음에 할 것
- 2일차 [C] 대화 맥락(Memory) F3010: 세션 조건을 SQLite sessions 표에 저장·불러오기 (run_agent는 이미 이전 조건 위에 바뀐 것만 덮어씀. 표는 schema.sql에 있음)
- 그다음 [G·Carbon] 2일차 교차 리뷰 (agy-guide ②)

## 주의
- 응답 시간: 예시 한 건 25~28초. 대부분 LLM 4번(analyze·plan·replan·respond). judge의 목표 버전 재조회는 패키지마다 순서대로 → 3일차 측정 때 병렬화 후보
- 재계획 방식은 LLM이 고름(upgrade_python/hold), 실패하면 upgrade_python. 되묻기 문장은 코드 (spec v1.9)
- 사실 조회 경로도 조건(os 등)을 Memory에 남김
- 구조는 docs/architecture.md (v1). /chat ndjson 스트리밍은 아직 없음
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정 (packaging만 수업 목록 밖)
- .venv는 Python 3.14.7
