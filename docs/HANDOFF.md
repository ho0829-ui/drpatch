# 마지막 갱신: 2026-11-18 17:03 / 작성: Claude Code

## 지금 하던 것
- 2일차 끝. 마지막: agy 교차 리뷰 13건 반영 (전체 테스트 217개 통과, 실제 GMS로 계획·사실 조회 재확인) — docs/review-day2.md 아래 "반영 결과"
  - planner: 패키지별 최소 Python, 탐색 상한(조건 줄기+1), 조회 실패는 확인 못 함 / UpgradePlan.unresolved
  - graph: 설치 불가·다운그레이드도 위반, 모두 실패 시 바로 안내(tools_down), judgment·plan_built 이벤트, 판단 재조회 병렬, 안전 패키지 버전 조회 생략
  - brain: answer_fact는 fact_tools.run_fact_tool로 코드가 계산한 값만 LLM에 전달 (tool_choice=required, 최대 3회)
  - tools: safe_parse(형식 오류 → UPSTREAM_ERROR) / repo.insert_event는 DB 기준 순번

## 다음에 할 것
- 3일차 [C] 계획 CRUD + 겹침 경고, 로그 조회·삭제 API (F3014~F3017) — /chat(ndjson)·/upload도 chat_turn·save_upload로 연결
- 3일차 [C] 화면 탭 3개 + 실행 단계 표시 + 오류 안내 (F3018~F3019)

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
