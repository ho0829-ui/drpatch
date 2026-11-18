# 마지막 갱신: 2026-11-18 17:19 / 작성: Claude Code

## 지금 하던 것
- 3일차 [C] 화면 끝 (테스트 233개 통과, 실제 서버+GMS로 브라우저에서 업로드→계획→확정→수정·삭제→로그까지 확인, 콘솔 오류 0)
  - web/index.html·style.css, web/js/: api.js(fetch·ndjson 읽기·세션 localStorage), render.js(escape 후 그리기, 간단 서식), chat.js, plans.js, logs.js, main.js
  - main.py가 web/을 "/"에 붙임 (API 라우터 뒤). 실행: preview "sudo-patch" (.claude/launch.json) 또는 uvicorn app.main:app
  - 실행 단계 패널: 단계·Tool(✓/✗·ms)·LLM 판단·재계획(주황)·회차 배정. 계획 수정은 바꾼 칸만 PUT (time 입력칸이 24:00을 못 보여 줌)

## 다음에 할 것
- [나] 대표 시나리오 5개를 화면에서 직접 돌려보기 (spec 완료 기준 체크)
- [나] 패키지 20개 파일로 응답 시간 재기 → 느리면 [C] 병렬·LLM 호출 줄이기 (지금 예시 2개 패키지로 약 24초, 대부분 LLM 4번)
- [G·Carbon] 제출 전: 전체 코드 vs spec 완료 기준 대조 (agy-guide ③)
- [나] 셀프 체크리스트 → 제출 (README 정리 필요)

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
