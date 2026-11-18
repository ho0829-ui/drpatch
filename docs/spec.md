# sudo-patch: 서버 패치·EOL 점검 플래너 (v1.2 · 2026-11-18)

> v1.1 → v1.2 (2026-11-18): 세 API 이용 조건 확정(docs/research/api-terms.md), 동시 호출 수 제한·출처 표기 추가.


> v1.0 → v1.1 (2026-11-18): 대표 요청 표를 실측(LLM만 답한 결과) 근거로 고침. "Ubuntu 20.04 언제까지?"를 "지금 뭐부터?"로 교체.

> v0.2 → v1.0: 실제 호출 결과(2026-11-18) 반영. 목표 버전 규칙을 "호환되는 최신 버전"으로 변경,
> OSV 중복 제거·등급 이름(MODERATE) 반영, 필드 이름 확정.

> v0.1 → v0.2 바뀐 점: Python 호환 제약(requires_python)을 재계획의 핵심으로 추가, freeze 파일 기준 입력,
> 미정 항목을 추천값으로 확정, 구현 방식·테스트 방식 추가.
> `[호출 확인]` = 실제 API 응답을 보고 확정할 부분.

## 목표
`pip freeze`로 만든 requirements.txt와 OS·Python 버전을 알려주면, 지원 종료일·취약점·
**지금 Python에서 설치 가능한 안전한 버전**을 조회해서 회차별 패치 계획을 만들고, 저장·수정·삭제할 수 있는 Agent 서비스.

## 사용자와 하는 일 (일상어)
1. 대화 탭에서 `pip freeze > requirements.txt`로 만든 파일을 올리고, "Ubuntu 20.04, Python 3.8"이라고 적는다.
2. "이번에 5개까지, 첫 점검은 11/21 22~24시, 격주로"라고 말한다.
3. Agent가 단계(분석 → 계획 → 조회 → 판단 → 재계획 → 응답)를 보여주며 회차별 계획을 제안한다.
   - 예: "django를 고치려면 Python 3.10이 필요해서, 1회차에 Python 업그레이드를 먼저 넣었어요."
4. "확정해줘"라고 하면 회차 하나하나가 계획으로 저장된다.
5. 계획 관리 탭에서 날짜·시간·항목을 고치거나 지운다. 시간이 겹치면 경고가 뜬다(저장은 됨).
6. 실행 로그 탭에서 Agent가 무슨 Tool을 왜 불렀고, 왜 재계획했는지 본다.

## 확정한 결정
| 주제 | 결정 |
|---|---|
| 입력 | freeze로 만든 requirements.txt 업로드 + OS·Python 버전은 대화 문장 |
| 파일 처리 | `이름==버전` 줄만 조회. `-e`, `@ file://`, `>=` 등은 "조회 제외" 목록으로 보여주고 되묻지 않음 |
| 점검 용량 | 사용자가 "이번에 N개까지"라고 말함. 소요 시간은 다루지 않음 |
| 우선순위 | 취약점 심각도 높은 순 → 같으면 지원 종료가 빠른 순 |
| 핵심 제약 | 고칠 버전이 **현재 Python에서 설치 가능해야 함** (PyPI의 requires_python) |
| 재계획 | ① 호환 제약 위반 → 다른 버전 재조회 또는 Python 업그레이드를 계획에 추가 ② N 초과 → 다음 회차로 나눔. 상한 3회 |
| 빠진 입력 | Tool 부르기 전에 빠진 것만 되묻기 (기본값 쓰지 않음) |
| 저장 단위 | 점검 회차 1개 = 계획 1개 |
| 겹침 | 계획에 날짜 + 시작·종료 시각(선택). 시각이 없으면 하루 전체로 보고, 같은 날 시간이 겹치면 경고 |
| Ubuntu 지원 종료 | 일반 지원 종료일 기준. 확장 지원(ESM) 종료일은 참고로 함께 표시 |
| 지원 종료된 OS·Python | 심각도 HIGH와 같은 순위 |
| 심각도 | OSV `database_specific.severity` 글자 등급(CRITICAL / HIGH / MODERATE / LOW)을 그대로 씀 |
| 중복 취약점 | OSV는 같은 취약점을 GHSA·PYSEC 두 건으로 줄 수 있음 → `aliases`로 묶어 1건으로 세고, 등급은 있는 쪽 사용 |
| 심각도 미상 취약점 | 묶은 뒤에도 등급이 없으면 LOW 다음 "심각도 미상" 칸. 임의로 등급을 매기지 않음 |
| 회차 간격 | "매주 / 격주 / 매월" 또는 "N일" → 일 수로 바꿔 저장 |
| Memory | 패키지 목록, OS·Python, N, 첫 점검 날짜·시각, 회차 간격 (API 결과는 매번 다시 조회) |
| 화면 | 탭 3개: 대화 / 계획 관리 / 실행 로그 |
| 심화 | 필수 기능 끝난 뒤 정함 |

## 범위 / 하지 않을 것
- 하는 것: PyPI 패키지 취약점·호환 버전 조회, OS·Python 지원 종료일 조회, 회차 계획, 계획 CRUD, 실행 로그.
- 하지 않는 것: 실제 서버 접속·패치 실행, 소요 시간 추정, 패키지끼리의 의존성 충돌 판단, OS 패키지(nginx 등) 취약점, Python 업그레이드 방법 안내(필요하다는 사실만 표시), 로그인.
- 위험 도메인 아님 → 면책 문구 없음. 화면 하단에 "참고용 정보" 한 줄.

## 외부 API (3종)
| API | 쓰는 정보 | 키 | 이용 조건 |
|---|---|---|---|
| endoflife.date | `GET /api/v1/products/{product}/releases/{cycle}` → eolFrom(일반 지원 종료), eoesFrom(ESM 종료), isEol, isLts, latest | 불필요 | 베타라 형식이 바뀔 수 있음. 수치 한도 없음, 429(Retry-After) 응답 있음. 출처 표기 |
| OSV.dev | `POST /v1/query` → 취약점, 등급, 수정 버전, aliases | 불필요 | 현재 한도 없음. 데이터는 원본 라이선스(PyPI·GitHub 권고 CC-BY 4.0) → 출처 표기 |
| PyPI JSON API | `GET /pypi/{name}/json` 한 번 → 최신 버전, 버전별 requires_python·yanked | 불필요 | 엣지 한도 없음. 몇 분에 수천 건 자제·직렬 권장, 과도한 자동 요청은 정지 가능(ToS·AUP). 고유 User-Agent 설정 |

이용 조건 상세·출처: `docs/research/api-terms.md` (2026-11-18 확인). 화면 하단에 세 API 출처를 표기한다.

실측(2026-11-18): 호출당 0.1~0.7초. django OSV 응답 297KB(75건), PyPI 전체 616KB.
→ 패키지 20개를 순서대로 부르면 30초 안팎이라 **병렬 호출이 필수**. 단, PyPI 직렬 권장을 고려해 **동시 호출 수를 작게 제한**하고(값은 3일차 측정 때 결정) 세션 캐시로 같은 호출을 반복하지 않는다.

## Tool 명세 (모두 `{ok, data}` 또는 `{ok:false, error:{code, message}}`)
| Tool | 언제 쓰나 (Agent에게 주는 설명) | 입력 | data | 실패 코드 |
|---|---|---|---|---|
| get_eol | OS나 Python이 언제까지 지원되는지 알아야 할 때 | product, cycle | eol_date, esm_date(없으면 null), is_eol, lts, latest_patch | PRODUCT_NOT_FOUND, NO_EOL_DATE, UPSTREAM_ERROR, TIMEOUT |
| get_vulns | 특정 패키지 버전이 위험한지, 몇 버전에서 고쳐졌는지 알아야 할 때 | name, version | count, vulns[{id, severity, fixed_versions}] | UPSTREAM_ERROR, TIMEOUT |
| get_package_versions | 업그레이드할 버전이 지금 Python에서 설치되는지 알아야 할 때 | name | latest, versions[{version, requires_python, yanked}] | PACKAGE_NOT_FOUND, UPSTREAM_ERROR, TIMEOUT |

- 취약점 0건은 실패가 아니라 `ok:true, count:0`.
- Tool 하나가 실패해도 그 항목만 "확인 못 함"으로 두고 나머지는 진행.
- 파일 파싱, 버전 비교 계산, 회차 나누기, 계획 저장은 Tool이 아니라 실행 흐름(코드)이 직접 한다.

## 판단 규칙
### 목표 버전 고르기 (패키지마다)
1. get_package_versions로 **현재 Python에서 설치 가능하고 yanked가 아닌 버전 중 가장 최신**을 고른다.
   requires_python이 비어 있는 버전은 후보로 두되 "호환 미확인"으로 표시한다.
2. 그 버전을 get_vulns로 다시 조회해 취약점 0건인지 확인한다.
3. 0건이면 목표 버전 확정. 주 버전이 바뀌면(예: 2.x → 4.x) "큰 변경" 표시.
4. 0건이 아니면 **호환 제약 위반**: 지금 Python으로는 안전한 버전에 갈 수 없다는 뜻 → 재계획.

> 왜 바꿨나: 실측에서 django 2.2.0의 수정 버전이 `2.2.28 / 3.2.13 / 4.0.4`처럼 줄기별로 여러 개 나왔고,
> 낮은 수정 버전은 그 뒤에 나온 취약점을 또 갖고 있어요. "가장 낮은 수정 버전부터 시도"하면 시도 횟수만 쓰고 실패해요.
> "호환되는 최신 버전 하나를 확인"하면 패키지당 추가 호출이 1번이고, 실제 운영 관행과도 맞아요.

### 재계획
| 상황 | 하는 일 | 다시 부르는 Tool |
|---|---|---|
| 호환 제약 위반 패키지가 있음 | 그 패키지들이 요구하는 가장 낮은 Python 버전을 구하고, 그 Python이 지원 중인지 확인한 뒤 "Python 업그레이드"를 앞 회차에 넣고 해당 패키지를 그 뒤 회차로 | get_eol(python, 새 버전), get_package_versions |
| 새 Python도 지원 종료됐거나 없음 | 그 다음 버전으로 한 번 더 시도. 그래도 안 되면 "보류(사유)"로 표시 | get_eol |
| 우선 항목 수 > N | 넘친 항목을 다음 회차로 | 없음 |
| 회차 날짜가 그 항목의 지원 종료일 뒤 | "종료 이후 처리" 경고 | 없음 |

- 상한: 재계획 3회, 회차 최대 3개. 넘친 것은 "미배정" 목록.
- 재계획 안 함: 입력 부족, 모든 Tool이 같은 이유로 실패(네트워크 등) → 바로 안내.
- 순서 제약: Python 업그레이드 항목은 그걸 필요로 하는 패키지보다 항상 앞 회차.

### 우선순위
CRITICAL > HIGH(지원 종료된 OS·Python 포함) > MODERATE > LOW > 심각도 미상 (패키지의 등급 = 가진 취약점 중 가장 높은 등급) → 같으면 지원 종료까지 남은 일수가 적은 순. 취약점 0건 항목은 계획에 넣지 않고 "안전" 목록으로.

## LLM이 하는 일 / 코드가 하는 일
| LLM | 코드 |
|---|---|
| 의도 분류(계획 수립 / 사실 조회 / 계획 확정 / 그 밖의 대화)와 이유 | 파일 파싱 |
| 문장에서 OS·Python·N·날짜·시각·간격 추출 ("우분투 20" → ubuntu 20.04) | 버전 비교, 후보 거르기, 정렬, 회차 나누기 |
| 어떤 Tool을 어떤 순서로 부를지 계획 (Tool 종류 단위. 패키지별 반복 호출은 코드가 펼침) | 패키지별 Tool 반복 호출 |
| 재계획이 필요할 때 어떤 방식으로 할지 선택하고 이유를 남김 | 재계획 상한 관리 |
| 되묻는 문장, 근거를 붙인 최종 응답 | 계획 저장, 겹침 확인 |

## 대표 요청과 "Tool 없이 LLM만 답하면 틀리는 점" (명세서 2.7)
근거: 2026-11-18 실측 (docs/planning-check.md "도메인 조건 확인", `scripts/check_llm_only.py`)

| 요청 | LLM만 답하면 (실측 근거) |
|---|---|
| "이 파일 기준으로 이번에 5개 올릴 계획 짜줘" | 취약점 건수·등급이 틀려 우선순위가 바뀜 (requests 2.19.0: 실제 5건·HIGH → LLM 4건·Medium, 2026년 취약점 누락) |
| "Python 3.8 서버인데 django 몇으로 올리면 돼?" | 줄기(4.2)만 말하고 정확한 목표 버전(4.2.30)과 그 버전의 취약점 0건 여부를 확인 못 함 |
| "Ubuntu 20.04, Python 3.8 서버인데 지금 뭐부터 해야 돼?" | 지원 종료일 자체는 대체로 맞히지만, 종료 상태를 취약점 등급과 같은 기준으로 줄 세우는 건 Tool 결과가 있어야 가능 |
| "계획 짜줘" (파일 없음) | Tool 호출 없이 되묻기. 도메인 맥락이 없으면 공부·운동 계획으로 오해함 → 시스템 프롬프트 필요 |
| "1회차 확정해줘" | Tool 아님. 실행 흐름이 저장 |

## 구현 방식
- 백엔드: FastAPI + SQLite. Agent: LangGraph 상태 그래프, LLM은 OpenAI(langchain-openai). 화면: HTML/CSS/JS.
- 버전 비교·requires_python 판정은 `packaging` 라이브러리 사용 `[필수 목록에 없음, 추가 가능한지 확인]`
- 로깅 Agent 분리: 메인 Agent는 이벤트를 큐에 넣기만 하고, 로깅 Agent가 따로 꺼내 저장. 로깅이 죽어도 메인은 기다리지 않음.
- 같은 세션 안에서 같은 API 호출 결과는 캐시해서 재사용.

## DB (SQLite)
| 표 | 주요 필드 |
|---|---|
| sessions | id, packages_json, excluded_json, os, os_version, python_version, capacity_n, first_date, window_start, window_end, interval_days |
| plans | id, session_id, round_no, date, window_start, window_end, items_json, created_at, updated_at |
| events | id, session_id, seq, type, payload_json, created_at |

items_json 항목: name, current_version, target_version, severity, eol_date, reason, kind(package / python_upgrade)

## 백엔드 API (FastAPI)
| 메서드·경로 | 하는 일 |
|---|---|
| POST /upload | 파일 파싱 → 조회 대상·조회 제외 목록 반환 |
| POST /chat | 메시지 처리, 응답 + 실행 단계 반환 |
| GET·POST /plans, GET·PUT·DELETE /plans/{id} | 계획 CRUD. 저장·수정 응답에 겹침 경고 필드 |
| GET /logs, GET·DELETE /logs/{session_id} | 실행 로그 목록·상세·삭제 |

## 화면 (탭 3개)
- 대화: freeze 안내 문구, 파일 올리기, 조회 제외 목록, 채팅, 옆에 실행 단계·Tool 호출 진행 표시, 오류 안내
- 계획 관리: 회차 목록(날짜순), 항목별 현재→목표 버전과 이유, 겹침 경고, 수정·삭제
- 실행 로그: 세션 목록 → 이벤트 순서대로 상세 (재계획 이유가 보이게)

## 테스트 방식
- 세 API의 실제 응답을 한 번 저장해 두고(tests/fixtures), 테스트는 저장본으로 돌린다. 네트워크 없이 `pytest` 한 번으로 판정.
- 꼭 있어야 할 테스트: 파싱(제외 줄 포함), 목표 버전 고르기, 호환 제약 위반 → Python 업그레이드 재계획, N 초과 회차 나누기, 겹침 경고, Tool 실패 시 나머지 진행, 로깅 꺼도 대화 정상.

## 완료 기준 (일상어)
- freeze 파일을 올리고 "5개까지"라고 하면 위험한 것부터 회차로 나뉜 계획이 나오고, 항목마다 "현재 → 목표 버전"과 이유가 보인다.
- 현재 Python에서 설치 안 되는 버전은 절대 목표 버전으로 나오지 않는다.
- 고칠 방법이 Python 업그레이드뿐이면, 업그레이드가 그 패키지보다 앞 회차에 들어간다.
- `-e`나 `>=` 줄은 조회 제외 목록에 보이고 오류가 나지 않는다.
- 파일 없이 "계획 짜줘"라고 하면 Tool을 부르지 않고 먼저 묻는다.
- 한 Tool이 실패해도 나머지 항목은 결과가 나오고, 실패한 항목엔 "확인 못 함"이 보인다.
- 같은 날 시간이 겹치는 계획을 저장하면 둘 다 저장되고 겹친다는 알림이 뜬다.
- 로그 탭에서 왜 이 순서·이 버전으로 정했는지, 왜 재계획했는지 볼 수 있다.
- 로깅이 멈춰도 대화는 정상 응답한다.
- 패키지 20개짜리 파일도 응답이 사용에 지장 없는 시간 안에 나온다 `[기준 시간 정하기]`

## 남은 확인
- [x] 세 API 실제 호출 (2026-11-18, 모두 200)
- [x] PyPI 버전별 requires_python 있음 (django 4.2 `>=3.8`, 5.0 `>=3.10`)
- [x] OSV 중복 제거 후 등급 없음 0건 (django 75→43건, requests 2.19.0 10→5건, 2.32.3 4→2건). "심각도 미상" 칸은 대비용으로만 유지
- [x] PyPI 이용 정책 (ToS API 조항·AUP 확인, 2026-11-18 → 외부 API 표)
- [ ] `packaging` 라이브러리 추가 가능 여부

## 예시 한 건 따라가기
입력: requests==2.19.0, django==2.2.0, `-e git+...` / "Ubuntu 20.04, Python 3.8" / N=2 / 11/21 22~24시 / 격주
1. 파싱: 조회 2개, 제외 1개(`-e`)
2. get_eol(ubuntu 20.04) → 일반 지원 2025-05-31 종료(is_eol), ESM 2030-04-23 / get_eol(python 3.8) → 2024-10-07 종료 → 둘 다 HIGH 취급
3. get_vulns: django 2.2.0 → 43건(묶은 뒤), 최고 CRITICAL / requests 2.19.0 → 5건, 최고 HIGH
4. get_package_versions: Python 3.8에서 설치 가능한 최신 → django 4.2.x, requests `[값 확인]`
5. get_vulns(목표 버전) 재조회 → 0건이면 확정 / 아니면 호환 제약 위반
6. (위반 시) 필요한 Python 버전 → get_eol(python 3.12) → 2028-10-31까지 지원 → "Python 3.12 업그레이드"를 1회차에 넣고 그 패키지를 2회차로
7. 우선순위: django(CRITICAL) > HIGH 셋(Python 3.8, Ubuntu 20.04, requests) 중 지원 종료일이 빠른 순 → Python 3.8(2024-10-07) > Ubuntu 20.04(2025-05-31) > requests(종료일 없음 → 뒤로)
8. N=2 → 4개 항목이 11/21, 12/5 두 회차로 → Ubuntu·Python은 이미 지원 종료라 "종료 이후 처리" 경고
9. 응답

> 따라가며 발견한 구멍: **Ubuntu·Python 자체 업그레이드도 계획 항목**인데, 이 둘은 "목표 버전"을 어떻게 정할지 규칙이 없었어요.
> → 규칙: OS는 "지원 중인 다음 LTS로 올림 필요"만 표시하고 목표 버전은 정하지 않음(범위 밖). Python은 재계획에서 정한 버전, 아니면 "지원 중인 버전으로 올림 필요"만 표시.
