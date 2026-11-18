# 마지막 갱신: 2026-11-18 14:37 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] 기획 검증 기록 끝 (docs/planning-check.md): LLM만 답한 결과 실측 + API 이용 조건
- agy 이용 조건 조사(docs/research/api-terms.md)를 공식 문서와 대조해 4곳 수정. spec v1.2 반영

## 다음에 할 것
- 1일차 [C] Tool 공통 응답 형식 + 레지스트리 (F3001) — app/tools/specs.py에 명세는 있음, 구현·레지스트리 붙이기
- 16:00 게이트 줄 체크는 사용자 확인 후

## 주의
- spec v1.2: 대표 요청 표 실측 근거로 교체(v1.1), API 이용 조건 확정·동시 호출 수 제한·출처 표기(v1.2)
- Tool 구현 시: 고유 User-Agent, endoflife 429 → UPSTREAM_ERROR, 세션 캐시, 동시 호출 수 제한
- LLM: GMS gpt-6-luna. temperature 보내면 400, chat/completions로 Tool 호출하면 400 → app/llm.py가 Responses API 사용, temperature 생략
- 시스템 프롬프트 없이 "계획 짜줘"하면 엉뚱하게 되물음 / 프롬프트가 있으면 spec 밖 정보까지 되물음 → 2일차 되묻기 프롬프트에서 다루기
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정, packaging 아직 없음
- .venv는 Python 3.14.7 (langsmith DeprecationWarning은 무시해도 됨)
- AGENTS.md: 데이터 API는 app/tools/, LLM은 app/llm.py에서만
