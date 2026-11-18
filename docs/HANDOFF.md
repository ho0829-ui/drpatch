# 마지막 갱신: 2026-11-18 15:50 / 작성: Claude Code

## 지금 하던 것
- 2일차 [C] planner 순수 함수 끝 (전체 테스트 155개 통과, spec 예시 끝까지 재현)
  - app/agent/planner/versions.py: is_final·python_allows·pick_latest·is_major_change (packaging)
  - python_upgrade.py: plan_python_upgrade(현재 Python, 위반 패키지 versions, check_vulns, check_eol) → UpgradePlan(status·python·targets·attempts)
    check_vulns(name, version)->건수|None, check_eol("3.11")->{eol_date, is_eol}|None 를 넘겨받음. 같은 조회는 캐시
  - items.py: PackageResult → build_items → items / safe / unchecked / held
  - priority.py: sort_items(items, today) / rounds.py: split_rounds(items, N, 첫 날짜, 간격)

## 다음에 할 것
- 2일차 [C] LangGraph 흐름 (F3005~F3009, F3011) — docs/architecture.md 3절 노드 순서
  - judge 노드가 PackageResult를 만들고, replan 노드가 plan_python_upgrade에 레지스트리를 감싼 함수를 넘김
  - "호환 제약 위반 → Python 업그레이드 재계획 테스트(상한 3회)"는 planner 단위로는 이미 있음. 그래프 단위 테스트를 그 작업에서 추가

## 주의
- spec v1.8: 확인 못 함 목록, os 항목, flags. Python 항목은 항상 HIGH (전제 조건)
- 구조는 docs/architecture.md (v1): web/ + app/api·agent·events·db. /chat은 ndjson 스트리밍, Agent는 작업 스레드(동기), 병렬 4개
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- 세션 캐시·동시 호출 수 제한은 아직 없음 (runner.py에서)
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- 되묻기 프롬프트: spec 밖 정보까지 묻는 경향 → 빠진 것만 묻게
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정 (packaging만 수업 목록 밖: docs/decisions/2026-11-18-packaging.md)
- .venv는 Python 3.14.7
