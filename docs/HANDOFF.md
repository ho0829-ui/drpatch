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
- 디자인 확정: **DR.PATCH 진료 책상** (docs/design.md가 유일한 기준). 이전 시안(SOC·Figma, 와펜·수집 패치, Carbon 1차)과 agy/design-* 브랜치·브리프는 모두 삭제
  - 시제품 prototype/drpatch-desk/index.html (Three.js, 예시 데이터). 보기: launch.json "drpatch-proto" → http://localhost:8010/drpatch-desk/
  - 사용자 피드백 받은 뒤: 명세에 보이는 이름(DR.PATCH)·말투 규칙 반영 → tasks.md를 작은 작업으로 쪼개기
  - 역할: 계획·검증·디자인은 Claude Code(Opus), 구현은 agy 하이드로젠 (agy/ 브랜치, 합치기 전 diff·pytest 확인). 첫 작업은 작게 시험
- 디자인 2차 (인터뷰): 팔레트 '병원 청록'(흰 가구·민트 벽·청록·코랄 강조, 코랄은 소품에만), 3D는 Blender 스크립트로 .glb
  - design/blender/common.py(팔레트·재질·도형) + 소품별 스크립트 → prototype/drpatch-desk/models/*.glb, 미리보기 design/blender/previews/
  - 실행: blender -b --factory-startup -P design/blender/doctor.py (Blender 5.3)
  - 완료: 닥터 패치(나이 든 박사님) + 소품 7종(capsule·blister·iv·bottle·chart·stamp·desk) → 시제품이 .glb 사용, 팔레트 병원 청록. docs/design.md 갱신함
  - 3차: 진료실(room.glb), 진짜 책상(나무 상판), 앉은 박사님, 줌, 블리스터 자동 조립(blister_cell/end), 곡반·다음 진료, 특별 알약(pills.glb), GTAO
  - 4차: 최적화(유리·합치기·AO 자동), 유격, 덮개 제거, 수액 관, 이름표·검사 결과 칩, 천장·줌 한계 → docs/design.md 4-2
  - 다음: 사용자 피드백 → 로고(캐릭터 기반) → 명세에 이름·말투 반영 → 하이드로젠용 작업 쪼개기
- 화면은 Vite + Vue (frontend/, 빌드 결과를 FastAPI가 제공) + Three.js 책상 장면
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
