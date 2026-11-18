# 마지막 갱신: 2026-11-18 17:44 / 작성: Claude Code

## 지금 하던 것
- 제출 기준선 정리 끝 → 태그 v1-submit (테스트 238개). README는 모든 기능을 끝낸 뒤 작성 (사용자 결정)
  - 대표 시나리오 5개·완료 기준: docs/scenario-check.md (scripts/run_scenarios.py, --big은 20개)
  - spec v1.14: 일정만 빠지면 우선순위(업그레이드 의존 반영) 먼저 + 일정만 되묻기 / "1회차 확정"은 그 회차만
  - 공부 노트: docs/study/ (큰 그림, 요청 따라가기, 설계 결정, 과제)

## 다음에 할 것 (사용자 결정, 2026-11-18)
- 캘린더 연동 F3023: 로컬 저장소 구현 먼저 → Google Calendar로 교체 가능하게. 기존 일정과 겹치는 회차는 다음 빈 날로 이동(최대 7일) + 표시
- Figma로 "보안 관제(SOC) 대시보드" 디자인 → Vite + Vue로 화면 다시 만들기 (frontend/ → 빌드 결과를 FastAPI가 제공)
- 심화 F3020~F3022도 가능하면 (이상 징후, Planner·Worker, RAG)
- 명세 밖 나만의 기능은 사용자가 더 고민 중
- [G·Carbon] 제출 전 대조 (agy-guide ③)는 사용자가 실행

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
