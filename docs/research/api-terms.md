# 외부 데이터 API 이용 조건 조사 (확인일: 2026-11-18)

> 작성: agy(Flash) 조사 → Claude Code가 공식 문서와 대조해 수정 (2026-11-18).
> 수정한 곳: PyPI 약관 URL(소문자 경로는 404), PyPI 연락처 "강력 권장" → "있으면 도움", endoflife.date 429 응답 추가, 아이콘 라이선스 범위.

## 1. endoflife.date API
- **호출 한도**: 수치 한도는 명시 없음. 단, OpenAPI 명세의 모든 경로에 `429 Too many requests, retry later`가 있고, `Retry-After` 헤더가 올 수 있으며 남용 방지·공정 사용을 위한 것이라고 적혀 있다. API는 베타이며 `304`(캐시) 사용을 권한다.
- **약관·라이선스**: 별도 이용 약관 명시 없음. 코드·API 명세는 MIT. README: 제품 설명은 영문 위키백과를 CC BY-SA 3.0으로 가져온 것. (CC-BY-SA-4.0은 사이트 자체 아이콘에 대한 것이고, 제품 아이콘 전체에 대한 것은 아님)
- **출처 표기 요구**: API 조회에 대한 출처 표기 규정은 명시 없음. 제품 설명 문장을 재사용하면 CC BY-SA 3.0 표기 조건이 붙는다. (우리는 날짜 값만 씀)
- **User-Agent 요구**: 명시 없음.
- **출처**: https://endoflife.date/docs/api/v1/ , https://endoflife.date/docs/api/v1/openapi.yml , https://github.com/endoflife-date/endoflife.date (README·LICENSE)

## 2. OSV.dev API
- **호출 한도**: FAQ에 현재 API 한도 없음이라고 명시. HTTP/1.1 응답 크기 상한 32MiB, HTTP/2는 상한 없음.
- **약관·라이선스**: 별도 이용 약관 명시 없음. 데이터는 원본 DB 라이선스를 따름 (PyPI·GitHub·PSF Advisory DB는 CC-BY 4.0, RustSec은 CC0 1.0 등).
- **출처 표기 요구**: OSV.dev 자체는 명시 없음. 우리가 쓰는 PyPI·GitHub 권고 데이터가 CC-BY 4.0이라 출처 표기가 필요.
- **User-Agent 요구**: 명시 없음.
- **출처**: https://google.github.io/osv.dev/api/ , https://google.github.io/osv.dev/faq/ , https://google.github.io/osv.dev/data/

## 3. PyPI JSON API
- **호출 한도**: 현재 엣지 단계의 호출 한도 없음(CDN 캐싱). 다만 몇 분 안에 수천 건 요청은 피하고, 직렬 호출을 권하며, 무책임한 사용은 막을 수 있다고 함. 캐시(ETag) 안내 있음.
- **약관**: 현행 Terms of Service(2025-02-25 시행)의 "API Terms": 남용·과도한 빈도의 요청은 API 접근의 일시·영구 정지 사유. Acceptable Use Policy: 과도한 자동 대량 활동 금지, 상당히 과도한 사용은 정지·속도 제한 가능.
- **출처 표기 요구**: 명시 없음.
- **User-Agent 요구**: 요청을 고유하게 식별하는 User-Agent를 설정하라고 안내. 연락처를 넣으면 도움이 된다고 함(필수 아님).
- **출처**: https://docs.pypi.org/api/ , https://docs.pypi.org/api/json/ , https://policies.python.org/pypi.org/Terms-of-Service/ , https://policies.python.org/pypi.org/Acceptable-Use-Policy/
