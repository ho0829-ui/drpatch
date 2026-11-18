# 마지막 갱신: 2026-11-18 14:51 / 작성: Claude Code

## 지금 하던 것
- 1일차 [C] requirements.txt 파싱 끝 (전체 테스트 113개 통과, 실제 pip freeze 112줄 → 조회 112·제외 0)
  - app/parsing/requirements.py: decode(bytes) / parse(text) / parse_bytes(raw) → packages[{name, version, line_no, marker}], excluded[{line_no, text, reason}]
  - 제외 이유: PyPI 출처 아님 / 정확한 버전 아님 / 옵션 줄 / 버전 없음 / 중복 / 형식 오류

## 다음에 할 것
- 1일차 [C] 예시 한 건(spec 맨 아래)을 Tool로 직접 따라가 보고 spec 수정
  - 파싱 → get_eol ×2 → get_vulns ×2 → get_package_versions ×2 → 목표 버전 재조회. requests의 "[값 확인]" 채우기
  - 버전 비교에 packaging이 필요한 지점이 나오면 기록 (허용 여부 아직 미확인)

## 주의
- spec v1.5: 파싱 규칙(환경 표시는 떼고 조회해 marker로 남김, 중복은 처음 줄만, UTF-16 BOM 처리)
- OSV는 없는 패키지도 200 {} → 0건. 패키지 존재 판단은 get_package_versions로
- endoflife.date는 없는 제품·없는 줄기 모두 같은 404 → PRODUCT_NOT_FOUND 하나
- 세션 캐시·동시 호출 수 제한은 아직 없음 (2~3일차 실행 흐름에서)
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- 되묻기 프롬프트는 2일차에 (spec 밖 정보까지 묻는 경향)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정, packaging 아직 없음
- .venv는 Python 3.14.7
