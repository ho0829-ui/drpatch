# 마지막 갱신: 2026-11-18 14:41 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] F3001 끝: Tool 공통 응답 형식 + 레지스트리 (테스트 26개 통과, 실제 LLM Tool 선택 4/4 재확인)
  - app/tools/base.py: ok()/fail(), 실패 코드 상수
  - app/tools/registry.py: ToolSpec(이름·설명·종류·입력/출력 pydantic 모델·실패 코드), ToolRegistry.register/specs/call
    call()은 UNKNOWN_TOOL → INVALID_INPUT → 실행(예외는 INTERNAL_ERROR) → 응답 모양·data 구조 확인 순서. 예외를 던지지 않음
  - app/tools/specs.py: Tool 3종 명세 (함수는 아직 없음). llm_tool_specs()는 명세만으로 LLM 형식 생성

## 다음에 할 것
- 1일차 [C] get_eol / get_vulns / get_package_versions 구현 + fixture 테스트 (F3002~F3004)
  - 함수는 params(입력 모델)를 받아 ok(data)/fail(code)를 돌려주고, registry.register(GET_EOL, 함수)로 등록
  - data는 specs.py의 출력 모델과 맞아야 함 (안 맞으면 레지스트리가 INTERNAL_ERROR)

## 주의
- spec v1.3: Tool 종류(external/local), 공통 실패 코드, pydantic 입력 모델 등록
- Tool 구현 시: 고유 User-Agent, endoflife 429 → UPSTREAM_ERROR, 세션 캐시, 동시 호출 수 제한
- LLM: GMS gpt-6-luna. temperature 보내면 400, chat/completions로 Tool 호출하면 400 → app/llm.py가 Responses API 사용, temperature 생략
- 시스템 프롬프트 없이 "계획 짜줘"하면 엉뚱하게 되물음 / 프롬프트가 있으면 spec 밖 정보까지 되물음 → 2일차 되묻기 프롬프트에서 다루기
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정, packaging 아직 없음
- .venv는 Python 3.14.7 (langsmith DeprecationWarning은 무시해도 됨)
- AGENTS.md: 데이터 API는 app/tools/, LLM은 app/llm.py에서만
