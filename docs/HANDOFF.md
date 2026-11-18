# 마지막 갱신: 2026-11-18 / 작성: Claude Code

## 지금 하던 것
- 심화 F3023 캘린더 연동 끝 (테스트 255개, 실제 서버+GMS: 11/21 23시 일정 → 1회차 11/22로 이동, 확정 시 캘린더 등록)
  - app/calendar/backend.py: CalendarBackend 인터페이스 + LocalCalendar(SQLite calendar_events), make_calendar(.env CALENDAR_BACKEND=local|google|off)
  - app/tools/calendar_tools.py: list_calendar_events(date_from, date_to), add_calendar_event(plan_id) — kind local, build_registry(calendar, db_path)일 때만 등록
  - app/agent/planner/calendar_fit.py: find_free_date (7일 안, 내가 등록한 일정 무시) / graph build의 fit_to_calendar → rounds의 moved_from·calendar_conflicts, plan.calendar_check, calendar_check 이벤트
  - /chat 확정 → register_on_calendar (Tool 경유), /calendar/events GET·POST·DELETE
  - app/timewindow.py: 시각 구간 계산 공용 (planner가 app.api를 부르지 않게)
  - 기준선 태그 v1-submit은 캘린더 전 상태

## 다음에 할 것
- 디자인 방향 변경 (v2): 와펜 패치 + 버전 세 자리 로고, 네온·3D 팝·움직임, 수집 패치(PATCH/MINOR/MAJOR). 브리프 docs/design-brief-carbon.md → Carbon이 agy/design-v2 브랜치, docs/design-v2/에 시안. 받으면 Claude Code가 확인 후 design.md 갱신 → Vue
- 수집 패치 기능은 명세(spec) 추가가 먼저 (획득 조건은 코드가 계산)
- Figma 디자인 끝: docs/design.md (토큰·컴포넌트·화면 4개, Figma 링크). Figma MCP는 Starter 요금제 호출 한도에 걸림 → Vue는 docs/design.md 기준으로
- Figma "보안 관제(SOC) 대시보드" 디자인 → Vite + Vue (frontend/, 빌드 결과를 FastAPI가 제공). 캘린더 화면은 Vue에서
- (선택) GoogleCalendar 구현체: app/calendar/google.py — 같은 인터페이스, OAuth 키는 사용자가 준비

## 주의
- spec v1.11 (리뷰 반영 규칙). 이벤트 종류에 plan_built 추가
- 가짜 LLM 테스트는 GmsBrain 자체를 검사하지 않음 → brain.py를 고치면 scripts/run_agent.py로 실제 확인할 것
- 응답 시간: 예시 한 건 25~28초. 대부분 LLM 4번(analyze·plan·replan·respond). judge의 목표 버전 재조회는 패키지마다 순서대로 → 3일차 측정 때 병렬화 후보
- 재계획 방식은 LLM이 고름(upgrade_python/hold), 실패하면 upgrade_python. 되묻기 문장은 코드 (spec v1.9)
- 사실 조회 경로도 조건(os 등)을 Memory에 남김
- 구조는 docs/architecture.md (v1). /chat ndjson 스트리밍은 아직 없음
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정 (packaging만 수업 목록 밖)
- .venv는 Python 3.14.7
