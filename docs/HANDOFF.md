# 마지막 갱신: 2026-11-18 14:48 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] F3002~F3004 끝: Tool 3종 구현 + fixture 테스트 (전체 68개 통과, 실제 API 9건 확인)
  - app/tools/http.py: User-Agent·타임아웃·상태 코드 → 실패 코드. 테스트는 http.transport를 가짜로 바꿈
  - app/tools/eol.py / vulns.py / package_versions.py, app/tools/default.py(build_registry)
  - 실패 응답 저장본: scripts/capture_failure_fixtures.py → tests/fixtures/ ({status, body, text} 형식)

## 다음에 할 것
- 1일차 [C] requirements.txt 파싱 (조회 제외 줄 포함) + 테스트
- 그다음: 예시 한 건(spec 맨 아래)을 Tool로 직접 따라가 보고 spec 수정

## 주의
- spec v1.4: F3002~F3004 ↔ Tool 짝짓기(get_vulns·get_package_versions·get_eol), 출력 필드 추가, 처리 규칙
- OSV는 없는 패키지도 200 {} → 0건. 패키지 존재 판단은 get_package_versions로
- endoflife.date는 없는 제품·없는 줄기 모두 같은 404 → PRODUCT_NOT_FOUND 하나
- 세션 캐시·동시 호출 수 제한은 아직 없음 (2~3일차 실행 흐름에서)
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- 되묻기 프롬프트는 2일차에 (spec 밖 정보까지 묻는 경향)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정, packaging 아직 없음
- .venv는 Python 3.14.7
