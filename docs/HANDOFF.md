# 마지막 갱신: 2026-11-18 14:01 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] LLM 호출 + Tool 선택 확인 끝 (4/4). 결과는 docs/planning-check.md "도구 연결 확인"

## 다음에 할 것
- 1일차 [C] 기획 검증 기록: 대표 요청별 "LLM만 답하면 틀리는 점", API 출처·이용 조건 (docs/planning-check.md에 이어서)
- 16:00 게이트: 세 API 호출([나] check_apis.py로 확인됨) + LLM 호출(확인됨)

## 주의
- LLM: GMS gpt-6-luna. temperature 보내면 400, chat/completions로 Tool 호출하면 400 → app/llm.py가 Responses API 사용, temperature 생략
- 되묻기 때 spec 밖 정보까지 묻는 경향 → 2일차 프롬프트에서 좁히기
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정, packaging 아직 없음
- .venv는 Python 3.14.7 (langsmith DeprecationWarning은 무시해도 됨)
- AGENTS.md: 데이터 API는 app/tools/, LLM은 app/llm.py에서만
