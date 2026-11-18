# 마지막 갱신: 2026-11-18 13:53 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] LLM 호출 + Tool 선택 확인 (명세서 2.7 도구 연결 확인) — 코드 준비 끝, 실제 호출만 남음
  - app/llm.py: .env의 GMS_KEY·GMS_BASE_URL·LLM_MODEL로 ChatOpenAI 생성
  - app/tools/specs.py: Tool 3개 명세(이름·설명·입력)만. 구현·레지스트리는 F3001~F3004에서
  - scripts/check_llm.py: 실제 호출 확인 스크립트 (① 한 번 호출 ② 대표 요청 4개로 Tool 선택)
  - tests/test_llm_setup.py: 네트워크 없는 테스트 4개 통과

## 다음에 할 것
- .env에 GMS_KEY·GMS_BASE_URL·LLM_MODEL 채우고 `.venv/bin/python scripts/check_llm.py` 실행
- 결과를 docs/planning-check.md "도구 연결 확인"에 기록 → tasks.md 체크

## 주의
- docs/course/는 대외비라 .gitignore로 빠져 있음. PDF와 pdftotext 변환본(.txt)이 여기 있음
- requirements.txt는 수업 명세 버전 고정. packaging은 허용 확인 전이라 아직 없음
- .venv는 Python 3.14.7. requirements 설치 완료 (langsmith가 3.16 대비 DeprecationWarning을 냄, 동작엔 문제 없음)
- AGENTS.md 규칙 변경: 데이터 API는 app/tools/, LLM은 app/llm.py에서만
