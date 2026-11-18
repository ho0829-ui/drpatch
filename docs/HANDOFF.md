# 마지막 갱신: 2026-11-18 17:12 / 작성: Claude Code

## 지금 하던 것
- 3일차 [C] 백엔드 API 끝 (전체 테스트 232개 통과, 실제 서버+GMS로 업로드→스트리밍→확정→계획·로그 조회 curl 확인)
  - app/api/: upload.py(본문 그대로), chat.py(ndjson: session → 이벤트 → final, 확정 저장), plans.py(CRUD+overlaps), logs.py(목록·상세·삭제)
  - app/api/overlap.py(같은 날·구간 겹침, 시각 없으면 하루 전체, 24:00 허용), deps.py(DB 연결, save_confirmed_plan)
  - main.py: app.state.db_path·bus·logger·brain(키 없으면 None), 입력 오류 422 짧은 안내
  - 요청·응답 형식은 spec v1.12 "백엔드 API"

## 다음에 할 것
- 3일차 [C] 화면 탭 3개 + 실행 단계 표시 + 오류 안내 (F3018~F3019) — web/를 FastAPI가 같은 주소로 내보냄
  - 대화: fetch('/upload', {body: file}), /chat 응답 본문을 줄 단위로 읽어 실행 단계 패널에 쌓기, replan 색 구분
  - 계획 관리: GET/PUT/DELETE /plans, overlaps 경고 / 실행 로그: /logs
  - 하단 "참고용 정보" + 세 API 출처 표기 (NF3007)
- [나] 대표 시나리오 5개 화면에서 돌려보기, 패키지 20개 응답 시간 재기

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
