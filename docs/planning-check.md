# 기획 검증 기록 (요구사항 2.7)

## 도구 연결 확인 (2026-11-18)

실행: `.venv/bin/python scripts/check_llm.py` · LLM: SSAFY GMS(OpenAI 호환) `gpt-6-luna`, Responses API

### ① LLM 한 번 호출 — 통과
- `.env`의 `GMS_KEY`·`GMS_BASE_URL`·`LLM_MODEL` 로딩 → 응답 받음
- 처음 실패한 두 가지와 조치
  | 증상 | 원인 | 조치 |
  |---|---|---|
  | 400 `temperature does not support 0` | 추론형 모델은 temperature 기본값만 허용 | temperature를 보내지 않음 |
  | 400 `Function tools with reasoning_effort are not supported ... in /v1/chat/completions` | 이 모델은 chat/completions에서 Tool 호출 불가 | Responses API(`/v1/responses`) 사용 |

### ② Tool 명세를 넘겼을 때 Tool 선택 — 4/4 통과
| 요청 | 예상 | LLM 선택 (인자) |
|---|---|---|
| Ubuntu 20.04 언제까지 지원돼? | get_eol | get_eol(product=ubuntu, cycle=20.04) |
| requests 2.19.0 버전 써도 안전해? | get_vulns | get_vulns(name=requests, version=2.19.0) |
| Python 3.8 서버인데 django 몇 버전까지 설치할 수 있어? | get_package_versions | get_package_versions(name=django) |
| 계획 짜줘 (파일 없음) | 호출 없음 | 호출 없음 → OS·Python 버전, requirements.txt를 되물음 |

- 관찰: "계획 짜줘"에 되물을 때 spec에 없는 정보(운영 중인 서비스 등)도 함께 물었다. 2일차 되묻기 단계에서 "빠진 것만 묻기"를 프롬프트로 좁혀야 함.

## 도메인 조건 확인: Tool 없이 LLM만 답하면 (2026-11-18)

실행: `.venv/bin/python scripts/check_llm_only.py` · LLM: `gpt-6-luna`, Tool 없음
비교 기준: `tests/fixtures/`의 실제 API 응답 (2026-11-18 저장본)

| # | 요청 | LLM만 답한 것 | 실제 API | 판정 |
|---|---|---|---|---|
| 1 | Ubuntu 20.04 언제까지 지원돼? | 일반 지원 2025-05-31, ESM "2030년 4월(정확한 일자 없음)" | 일반 2025-05-31, ESM 2030-04-23 | 거의 맞음. ESM 일자만 모름 |
| 2 | Python 3.8 서버인데 django 몇으로? | "4.2 LTS 계열", 정확한 패치 번호는 안 줌 | 3.8에서 설치 가능한 최신 4.2.30 (전체 최신 6.1.3) | 줄기는 맞음. 정확한 목표 버전·그 버전의 취약점 0건 여부는 답 못 함 |
| 3 | requests 2.19.0 취약점 몇 건, 최고 등급은? | 4건, 최고 Medium | 5건(중복 묶은 뒤), 최고 HIGH | **틀림.** 2026년 CVE(CVE-2026-25645) 누락, CVE-2018-18074 등급을 낮게 답함 |
| 4 | Python 3.8 언제 지원 종료? | 2024-10-07 | 2024-10-07 | 맞음 |
| 5 | 계획 짜줘 (파일 없음) | 공부·운동 계획 등으로 오해하고 목표·기간을 물음 | 파일·OS·Python 버전을 되물어야 함 | 틀림(도메인 맥락 없음). Tool 문제가 아니라 시스템 프롬프트로 해결 |

### 해석
- **이미 지난 날짜(지원 종료일)는 LLM도 대체로 맞힌다.** "Ubuntu 20.04 언제까지?"만으로는 "Tool 없이 틀린다"를 보여주기 약하다.
- **확실히 틀리는 곳은 취약점(3번)이다.** 학습 시점 뒤에 나온 취약점을 모르고, 등급도 틀린다. 계획의 우선순위가 이 값으로 정해지므로 Tool이 꼭 필요하다.
- **2번은 "정확한 목표 버전"에서 갈린다.** LLM은 줄기(4.2)만 말하고, 그 줄기의 최신 패치가 무엇인지, 그 버전에 취약점이 없는지는 확인하지 못한다. spec의 목표 버전 규칙(호환되는 최신 → 취약점 0건 확인)은 Tool 결과 두 개를 조합해야만 나온다.
- 요구사항 기준("적지 못하면 요청을 다시 정한다")에 비추면, 1번은 대표 요청으로 약하다 → spec 대표 요청 표를 고침(아래, spec v1.1).

### spec 대표 요청 표 수정 (spec v1.1에 반영함)
| 요청 | LLM만 답하면 (실측 근거) |
|---|---|
| "이 파일 기준으로 이번에 5개 올릴 계획 짜줘" | 취약점 건수·등급이 틀려 우선순위가 바뀜 (3번: 5건 HIGH → 4건 Medium) |
| "Python 3.8 서버인데 django 몇으로 올리면 돼?" | 줄기만 말하고 정확한 목표 버전(4.2.30)과 그 버전의 취약점 0건 여부를 확인 못 함 (2번) |
| "Ubuntu 20.04 언제까지 지원돼?" → **"Ubuntu 20.04, Python 3.8 서버인데 지금 뭐부터 해야 돼?"로 교체** | 지원 종료일 자체는 맞혀도, 종료 상태를 취약점 등급과 같은 기준으로 줄 세우는 건 Tool 결과가 있어야 가능 |
| "계획 짜줘" (파일 없음) | Tool 호출 없이 되묻기 (5번: 도메인 맥락이 없으면 엉뚱하게 되물음 → 시스템 프롬프트 필요) |

## API 출처·이용 조건 (2026-11-18)

조사: agy(Flash) → Claude Code가 공식 문서와 대조·수정. 상세와 출처 URL은 `docs/research/api-terms.md`.

| API | 호출 한도 | 약관·라이선스 | 출처 표기 | User-Agent | 우리 구현에 미치는 영향 |
|---|---|---|---|---|---|
| endoflife.date | 수치 없음. 429(Retry-After) 응답 있음, 베타 | 별도 약관 없음. 코드·명세 MIT | API 조회는 규정 없음 | 요구 없음 | 429 → `UPSTREAM_ERROR`로 처리. 베타라 형식 변경 대비(fixture 테스트). 화면에 출처 표기 |
| OSV.dev | 현재 한도 없음 (HTTP/1.1 응답 32MiB 상한) | 별도 약관 없음. 데이터는 원본 DB 라이선스(PyPI·GitHub 권고 CC-BY 4.0) | CC-BY 4.0 데이터라 출처 표기 필요 | 요구 없음 | 화면에 "취약점 정보: OSV.dev (원본 PyPI·GitHub Advisory, CC-BY 4.0)" 표기 |
| PyPI JSON API | 엣지 한도 없음. 몇 분에 수천 건 자제, 남용 시 정지 가능 | ToS API 조항·AUP: 과도한 자동 요청 금지 | 규정 없음 | 고유한 User-Agent 설정 안내(연락처는 선택) | 고유 User-Agent 설정. 세션 캐시로 같은 패키지 재조회 안 함. 병렬 호출 수 제한 |

- 대량 수집이 아니라 사용자가 올린 패키지(20개 안팎)만 조회하므로 세 API 모두 이용 조건 안에 든다.
- spec의 "패키지 20개 병렬 호출"과 PyPI의 "직렬 호출 권장"이 부딪힌다 → 동시 호출 수를 작게(예: 4) 제한하고 캐시를 쓴다. 정확한 값은 3일차 응답 시간 측정 때 정한다.

## Tool 설계 확인: 결과 없음·빈 값의 실제 응답 (2026-11-18)

수집: `scripts/capture_failure_fixtures.py` → `tests/fixtures/` · 확인: `scripts/check_tools.py`(실제 API), `tests/test_tools.py`(저장본)

| 경우 | 실제 응답 | 실패 코드 반영 |
|---|---|---|
| endoflife.date 없는 제품 / 없는 줄기 | 둘 다 HTTP 404 HTML 페이지 (구분 안 됨) | PRODUCT_NOT_FOUND 하나로, 메시지에 "제품 이름이나 버전 확인" |
| endoflife.date ESM 없음 (python 3.8, 3.14) | `eoesFrom` 키가 null이거나 아예 없음 | 실패 아님. `esm_date: null` |
| OSV 취약점 0건 (requests 2.34.2) | HTTP 200 `{}` | 실패 아님. `count: 0` |
| OSV 없는 패키지 | HTTP 200 `{}` (0건과 같음) | 실패 아님. 패키지 존재는 get_package_versions가 판단 |
| OSV 같은 취약점 GHSA·PYSEC 2건, 한쪽만 등급 | requests 2.32.5: MODERATE + 등급 없음 | aliases로 묶어 1건, 있는 등급 사용 |
| OSV 수정 버전에 커밋 해시 | GIT 범위의 `fixed`가 커밋 해시 | ECOSYSTEM 범위만 사용 (테스트로 발견) |
| PyPI 없는 패키지 | HTTP 404 `{"message": "Not Found"}` | PACKAGE_NOT_FOUND |
| PyPI 파일 없는 버전 (django 1.0.1 등) | `releases`에 빈 목록 | 설치 불가라 목록에서 뺌 |
| PyPI requires_python 비어 있음 (옛 requests) | `requires_python: null` | null 그대로 = "호환 미확인", 채우지 않음 |

실제 호출 시간(2026-11-18): 0.2~1.2초 (django OSV 43건이 가장 느림).

## 설계 시험: 예시 한 건 따라가기 (2026-11-18)

실행: `.venv/bin/python scripts/walk_example.py` (실제 API). 입력: requests==2.19.0, django==2.2.0, `-e git+…` / Ubuntu 20.04, Python 3.8 / N=2
※ 4단계의 버전 비교·requires_python 판정은 스크립트 안의 임시 계산(숫자 비교, `>=3.N` 위주).

| 단계 | spec 예상 | 실제 | 차이 |
|---|---|---|---|
| 1 파싱 | 조회 2, 제외 1 | 조회 2, 제외 1(3번째 줄, PyPI 출처 아님) | 같음 |
| 2 get_eol | Ubuntu 2025-05-31 종료·ESM 2030-04-23 / Python 3.8 2024-10-07 종료 | 같음 | 같음 |
| 3 get_vulns(현재) | django 43건 CRITICAL / requests 5건 HIGH | 같음 | 같음 |
| 4 Python 3.8에서 설치 가능한 최신 | django 4.2.x / requests `[값 확인]` | django **4.2.30**, requests **2.32.4** | 값 채움 |
| 5 get_vulns(목표) | django는 0건 가정 | **django 4.2.30: 8건(최고 HIGH), requests 2.32.4: 1건(MODERATE)** | **둘 다 호환 제약 위반** |
| 6 Python 업그레이드 | 3.12 (2028-10-31까지) | 안전한 버전이 생기는 가장 낮은 Python = **3.10**(django 5.2.19, requests 2.34.2 모두 0건) → 3.10은 **2026-10-01 이미 종료** → 다음 **3.11**(2027-10-31까지, 같은 두 버전 0건) | 3.12 아니고 3.11. 재계획 2번 |
| 7 우선순위 | Python 3.8 항목과 Python 업그레이드 항목이 따로 | 같은 일(Python 3.8 → 3.11)이라 **한 항목으로 합쳐야** 함 | 규칙 없음 |
| 8 회차 (N=2) | 4개 → 2회차 | 항목 4개(Python 3.8→3.11, Ubuntu 20.04, django 2.2.0→5.2.19, requests 2.19.0→2.34.2). 순서 제약 때문에 django가 CRITICAL이어도 1회차에 못 들어감 → 1회차 Python·Ubuntu, 2회차 django·requests | 우선순위보다 순서 제약이 먼저 |

### 따라가며 발견한 구멍
1. **목표 버전 재조회에서 둘 다 위반** → 예시의 "django 4.2.x면 끝" 가정이 틀림. 재계획 경로가 대표 시나리오의 핵심이 됨.
2. **"요구하는 가장 낮은 Python"을 구하는 방법이 없음** → Python 줄기를 하나씩 올려 보며(3.9, 3.10, …) 그 Python에서 설치 가능한 최신 버전을 get_vulns로 확인, 0건이 처음 나오는 줄기를 고르는 규칙 필요. 이 과정의 get_eol·get_vulns 호출이 재계획 횟수(상한 3)에 어떻게 세는지도 정해야 함.
3. **정식 버전이 아닌 버전(rc·a·b·dev)** 을 목표에서 빼는 규칙 없음 (django는 56개). 
4. **Python EOL 항목과 Python 업그레이드 항목이 겹침** → 한 항목으로 합치는 규칙 필요.
5. **회차 나누기에서 순서 제약 > 우선순위** 명시 필요. Python 업그레이드가 N을 차지하는지도 명시.
6. **큰 변경**: django 2 → 5 (주 버전 3단계). 표시 규칙은 있음.
7. **packaging 필요성 근거**: 버전 정렬(4.2.30 > 4.2.3, 1!2.0, post·dev), 정식 버전 판별(rc 56개), requires_python 조건(`>=3.8`, `!=3.0.*`, `~=` 등) 판정을 직접 짜야 함. 스크립트의 임시 계산은 `>=3.N` 정도만 맞음.
