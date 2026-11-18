# 마지막 갱신: 2026-11-18 14:21 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] 기획 검증 기록 (docs/planning-check.md) — 절반 끝
  - 끝: "Tool 없이 LLM만 답하면" 실측 (scripts/check_llm_only.py, 5개 요청). 취약점은 확실히 틀림, 지원 종료일은 대체로 맞음
  - 남음: API 출처·이용 조건 — agy(Flash)가 docs/research/api-terms.md 조사 중(agy-guide ①). 끝나면 planning-check.md에 요약
  - 사용자 결정 대기: planning-check.md의 "spec 대표 요청 표 수정 제안"을 spec.md에 반영할지

## 다음에 할 것
- api-terms.md 나오면 planning-check.md 요약 → tasks.md 기획 검증 항목 체크
- 그다음: Tool 공통 응답 형식 + 레지스트리 (F3001)

## 주의
- LLM: GMS gpt-6-luna. temperature 보내면 400, chat/completions로 Tool 호출하면 400 → app/llm.py가 Responses API 사용, temperature 생략
- 시스템 프롬프트 없이 "계획 짜줘"하면 공부·운동 계획으로 오해함 / 프롬프트가 있으면 spec 밖 정보까지 되물음 → 2일차 되묻기 프롬프트에서 다루기
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정, packaging 아직 없음
- .venv는 Python 3.14.7 (langsmith DeprecationWarning은 무시해도 됨)
- AGENTS.md: 데이터 API는 app/tools/, LLM은 app/llm.py에서만
