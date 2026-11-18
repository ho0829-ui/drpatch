# 2일차 교차 리뷰 (`app/` vs `docs/spec.md` v1.10)

검토 일시: 2026-11-18 · 대상 브랜치: `main` (`a830c7d`) · 기준: `docs/spec.md` "판단 규칙" · "완료 기준"

## 중점 확인 5개 항목 요약

1. **목표 버전 고르기 (`호환되는 최신 → 취약점 0건 확인`)**: 계획 수립(`plan`) 경로의 `pick_latest()` → `runner.vuln_count()` 흐름은 yanked·시험판 제외, `requires_python` 판정(비어 있으면 `호환 미확인`), 주 버전 변경(`큰 변경`), 취약점 잔존 시 위반 판정을 spec대로 수행한다. 다만 **사실 조회(`fact`) 경로(`brain.py:117-126`)에서는 이 규칙과 2차 취약점 확인이 누락**되어 있고, 현재 Python에서 후보 버전이 아예 없을 때(`target is None`, `graph.py:150-153`) 재계획으로 넘어가지 않는 문제가 있다.
2. **재계획 상한 3회**: `plan_python_upgrade()`(`python_upgrade.py:17, 89-110`)에서 `MAX_REPLANS = 3` 및 "재계획 1회 = Python 후보 줄기 1개를 `get_eol`로 확인(`get_vulns` 줄기 훑기는 제외)" 규칙은 정확히 지켜진다. 다만 `lower_bound_minors()`(`versions.py:61-74`)의 상한 계산 오류로 인해 `>3.9`·`~=3.10` 같은 조건에서는 3회를 채우기도 전에 탐색이 조기 중단되며, "모든 Tool이 같은 이유로 실패 시 재계획 안 함 → 바로 안내"(`spec.md:168`) 조기 종료 분기가 없다.
3. **LLM 계산 개입 여부**: 계획 수립(`plan`) 경로에서는 버전 비교(`versions.py`)·우선순위 정렬(`priority.py`)·회차 나누기(`rounds.py`) 모두 순수 코드가 수행한다. 그러나 **사실 조회(`fact`) 경로(`brain.py:117-126`)에서는 `get_package_versions`의 원시 버전 목록 전체를 LLM에 그대로 넘겨 버전 비교·시험판 제외·`requires_python` 판정을 LLM이 직접 수행**한다.
4. **API 미확인 값 생성 여부**: Tool 계층(`eol.py`, `vulns.py`, `package_versions.py`)은 미확인 값을 `None`·`UNKNOWN`(`심각도 미상`)으로 두어 지어내지 않는다. 그러나 **재계획 중 `get_vulns`가 실패(`None`)하면 `python_upgrade.py:63, 91-93`이 `"어떤 Python 줄기에서도 취약점 없는 버전을 찾지 못했습니다"`라고 단정해 `확인 못 함` 대신 `보류`에 넣으며**, `answer_fact()`(`brain.py:120-126`)도 Tool 호출 없이 `first.text`를 반환하거나 목표 버전 취약점 미확인 상태로 답할 수 있다.
5. **Tool 예외 전파 여부**: `ToolRegistry.call()`(`registry.py:97-121`)을 통하면 입력·실행·출력 단계 모두 `try/except`로 감싸져 예외가 밖으로 나가지 않는다. 다만 개별 Tool 함수(`get_eol`, `get_vulns`, `get_package_versions`)나 `http.fetch_json()`을 직접 호출할 때는 비정상 업스트림 JSON 구조에서 `AttributeError`·`TypeError` 등이 밖으로 전파될 수 있고, 레지스트리 경유 시에도 `UPSTREAM_ERROR` 대신 `INTERNAL_ERROR`가 된다.

---

## 상세 리뷰 표

| 심각도 | 파일:줄 | 문제 | 근거 |
|---|---|---|---|
| 높음 | `app/agent/planner/versions.py:61-74`<br>`app/agent/planner/python_upgrade.py:85, 90` | `lower_bound_minors()`가 `>=`·`>` 연산자의 `v.minor` 숫자만 뽑아 탐색 상한(`bound`)을 정한다. 그 결과 `requires_python`이 `>3.9`(실제 3.10 필요), `~=3.10`, `==3.11.*`, `>=3.10.1`, `>=3.8,!=3.8.*,!=3.9.*` 형태이면 안전한 버전이 열리는 Python 줄기까지 올라가 보지 못하고 즉시 `"어떤 Python 줄기에서도 취약점 없는 버전을 찾지 못했습니다"`로 보류(`hold`) 처리된다. | `docs/spec.md:159-163`("필요한 가장 낮은 Python 구하기"), `docs/spec.md:240`(완료 기준: "고칠 방법이 Python 업그레이드뿐이면, 업그레이드가 그 패키지보다 앞 회차에 들어간다"), `docs/spec.md:257`(`~=3.7`, `!=3.0.*` 판정을 위해 `packaging` 도입). |
| 높음 | `app/agent/planner/python_upgrade.py:63-64, 91-93`<br>`app/agent/planner/items.py:98-100` | 재계획(`find_safe_python`) 중 `check_vulns()`가 OSV 타임아웃·오류로 `None`을 반환하면 `!= 0`으로 처리되어 ① API로 확인하지 못한 상태를 `"어떤 Python 줄기에서도 취약점 없는 버전을 찾지 못했습니다"`라는 거짓 사유로 단정해 `확인 못 함`(`unchecked`)이 아닌 `보류`(`held`)에 넣고, ② 위반 패키지 중 하나만 조회 실패해도 루프 전체가 깨져 나머지 위반 패키지의 Python 업그레이드까지 모두 무산된다. | `docs/spec.md:113, 180, 243`(완료 기준: "한 Tool이 실패해도 나머지 항목은 결과가 나오고, 실패한 항목엔 '확인 못 함'이 보인다"), `AGENTS.md`("API로 확인하지 못한 값을 지어내지 않는다. 없으면 '미상' / '확인 못 함'으로 둔다"). |
| 높음 | `app/agent/brain.py:117-126`<br>`app/agent/graph.py:214-218` | 사실 조회(`intent="fact"`, 예: `"Python 3.8 서버인데 django 몇으로 올리면 돼?"`)를 처리하는 `answer_fact()`가 ① `get_package_versions`의 수백 개 원시 버전 목록을 코드(`pick_latest`)로 거르지 않고 LLM에 그대로 넘겨 버전 비교·시험판 제외·`requires_python` 판정을 LLM에게 맡기고, ② Tool 호출 루프가 1회(`first.tool_calls`)뿐이라 후보 버전의 취약점 0건 여부(`get_vulns`)를 연쇄 확인할 수 없으며, ③ `first.tool_calls`가 비면 Tool 근거 없이 `first.text`를 반환한다(세션 `conditions`도 전달되지 않음). | `docs/spec.md:139-142`("호환되는 최신 → get_vulns로 취약점 0건 확인"), `docs/spec.md:189`("버전 비교, 후보 거르기"는 코드 역할), `docs/spec.md:200`(대표 요청 2번), `docs/spec.md:239`(완료 기준: "현재 Python에서 설치 안 되는 버전은 절대 목표 버전으로 나오지 않는다"). |
| 중간 | `app/agent/graph.py:150-153`<br>`app/agent/planner/items.py:101-102` | 현재 Python에서 설치 가능한 비-yanked 정식 버전이 하나도 없을 때(`pick_latest(...) is None`, 예: 기존 버전이 취약점으로 yanked되었고 수정 정식 버전들은 모두 `requires_python >= 3.10`인 경우), `judge`가 `violation=True`로 표시하지 않아 `replan`이 실행되지 않고 `"설치 가능한 정식 버전이 없음"`으로 바로 보류된다(상위 Python에는 정식 버전이 있어도 사유가 사실과 다르게 표기되며, 다른 패키지 덕분에 Python이 올라가도 `upgrade.targets`에서 빠진다). | `docs/spec.md:144`("지금 Python으로는 안전한 버전에 갈 수 없다는 뜻 → 재계획"), `docs/spec.md:240`(완료 기준: Python 업그레이드로 해결 가능한 패키지의 선행 배치). |
| 중간 | `app/events/bus.py:50, 67-68`<br>`app/db/schema.sql:42`<br>`app/events/logger.py:59-62` | `EventBus._seq`는 프로세스 메모리에만(`0`부터 시작) 유지되는데 SQLite `events` 표에는 `UNIQUE (session_id, seq)` 제약이 있다. 서버 재시작(`uvicorn --reload` 포함) 뒤 기존 `session_id`로 후속 턴을 보내면 `seq=1..N`이 충돌(`IntegrityError`)하여 해당 턴의 실행 로그가 조용히 유실된다(`self.failed += 1`). | `docs/spec.md:62`(세션 Memory 유지), `docs/spec.md:245`(완료 기준: "로그 탭에서 왜 이 순서·이 버전으로 정했는지, 왜 재계획했는지 볼 수 있다"). |
| 중간 | `app/agent/graph.py:113-164` | 네트워크 장애 등으로 모든 Tool이 같은 이유(`UPSTREAM_ERROR`·`TIMEOUT`)로 실패해도 조기 종료·안내 분기가 없어, 남은 Tool 묶음까지 다 호출한 뒤 `judge` → `build`(`rounds: []`) → `respond`(LLM 호출, 실패 시 `"이번에 계획에 넣을 항목이 없어요."`)까지 진행한다. | `docs/spec.md:168`("재계획 안 함: 입력 부족, 모든 Tool이 같은 이유로 실패(네트워크 등) → 바로 안내"). |
| 중간 | `app/tools/eol.py:31, 42`<br>`app/tools/vulns.py:20, 50-51`<br>`app/tools/package_versions.py:19-28`<br>`app/tools/http.py:25-28, 45-50` | `ToolRegistry.call()` 밖에서 개별 Tool 함수나 `http.fetch_json()`을 직접 부를 경우, 비정상 업스트림 응답(예: `endoflife.date`의 `latest`가 문자열일 때 `eol.py:42` `AttributeError`, `OSV` `vulns` 원소나 `database_specific`이 dict가 아닐 때 `vulns.py:20, 51` `AttributeError`/`TypeError`, `PyPI` `files` 원소 이상 시 `package_versions.py:22` `AttributeError`, 잘못된 charset 헤더에서 `r.json()` `LookupError`)이 예외로 던져진다. 레지스트리 경유 시에도 업스트림 형식 오류가 `UPSTREAM_ERROR`가 아닌 `INTERNAL_ERROR`로 반환된다. | `docs/spec.md:74`("endoflife.date: 베타라 형식이 바뀔 수 있음"), `docs/spec.md:83, 99`("그 밖의 비정상·JSON 아님·연결 실패 → UPSTREAM_ERROR"), `app/tools/base.py:5`("Tool은 예외를 밖으로 던지지 않고 항상 이 둘 중 하나를 돌려준다"). |
| 중간 | `app/agent/graph.py:38-49, 163, 187-205` | `events` 표에 남는 이벤트는 위반 목록(`judgment`)과 재계획 시도(`replan`), LLM 결정(`llm_decision`)뿐이며, 일반 패키지의 확정 목표 버전·등급·플래그와 `build` 단계의 우선순위 정렬·회차 배정 근거(순서 제약으로 2회차 배치 등)는 이벤트에 실리지 않는다. 로그 탭이 `events` 표만 읽는 구조라면 "왜 이 순서·이 버전으로 정했는지"를 확인하기 어렵다. | `docs/spec.md:245`(완료 기준: "로그 탭에서 왜 이 순서·이 버전으로 정했는지, 왜 재계획했는지 볼 수 있다"), `docs/spec.md:216`(`events` 표). |
| 확인 필요 | `app/agent/graph.py:168-176`<br>`app/agent/brain.py:109-115` | `choose_replan()` 프롬프트에 언제 `upgrade_python` 대신 `hold`를 고를지 기준이 없는데, LLM이 `"hold"`를 반환하면 `plan_python_upgrade()`를 호출하지 않고 모든 위반 패키지를 바로 보류한다. | `docs/spec.md:191`("재계획이 필요할 때 어떤 방식으로 할지 선택")과 `docs/spec.md:153, 240`(완료 기준: "고칠 방법이 Python 업그레이드뿐이면, 업그레이드가 그 패키지보다 앞 회차에 들어간다")이 충돌할 수 있어 의도 확인 필요. |
| 확인 필요 | `app/agent/graph.py:127-130, 154` | `call_tools`가 취약점 0건(`safe`)인 패키지까지 포함해 전체 패키지에 대해 PyPI `get_package_versions`(수백 KB)를 호출하고, `judge`의 목표 버전 `runner.vuln_count()`는 `call_many` 병렬 호출 대신 순차 루프로 호출한다. 또한 `spec.md:81, 209`의 "세션 캐시" 문구와 달리 `ToolRunner` 캐시는 1회 요청 안에서만 유지된다(`spec.md:62` "API 결과는 매번 다시 조회"와는 일치). | `docs/spec.md:76, 80-81`("병렬 호출이 필수"), `docs/spec.md:247`(완료 기준: "패키지 20개짜리 파일도 응답이 사용에 지장 없는 시간 안에 나온다"). 3일차 성능 측정 후 조정할 계획인지 확인 필요. |
| 확인 필요 | `app/agent/state.py:65-70`<br>`app/agent/graph.py:55-60` | ① `normalize_python()`이 `3.x`만 허용해 사용자가 `"Python 2.7"`을 입력하면 `None`(빠진 입력)으로 처리되어 Python 버전을 반복해서 다시 묻는다. ② `merge_conditions()`에서 후속 턴에 OS 이름만 바꾸면(`"데비안으로 바꿀게"`) 이전 `os_version`(`"20.04"`)이 남아 `"debian 20.04"`로 조회된다. | `docs/spec.md:53`("빠진 것만 되묻기"), `docs/spec.md:62`("조건은 바뀐 값만 덮어씀"). Python 2.x를 지원 제외 안내로 처리할지, OS 변경 시 버전을 비울지 확인 필요. |
| 확인 필요 | `app/agent/planner/versions.py:41-53` | `pick_latest()`가 `current_version` 이상인지 확인하지 않으므로, 현재 버전이 yanked되었거나 현재 Python 조건과 맞지 않는 상위 버전이 적힌 파일에서는 `current_version`보다 낮은 버전(다운그레이드)이 별도 표시 없이 목표 버전으로 선택될 수 있다. | `docs/spec.md:139`("현재 Python에서 설치 가능하고 yanked가 아닌 정식 버전 중 가장 최신") 문구 그대로이나 다운그레이드 허용 의도인지 확인 필요. |
| 확인 필요 (3일차 범위) | `app/main.py:36-42`<br>`app/agent/graph.py:220-222` | 완료 기준 중 `POST /upload`, `POST /chat`, `/plans` CRUD·시간 겹침 경고, `/logs` 조회·삭제 API 및 3개 탭 화면은 아직 `app/`에 구현되지 않았다(3일차 예정). 또한 제안된 계획(`last_plan`)이 없는 상태에서 `"확정해줘"`라고 해도 `graph.py:221-222`는 `"제안한 계획을 확정할게요."`를 반환하므로 `/chat` 연결 시 `last_plan` 유무 확인이 필요하다. | `docs/spec.md:220-232, 238, 241, 244, 245`(완료 기준 전반). |

---

## 반영 결과 (Claude Code, 2026-11-18)

지적 13건 모두 코드와 대조했고 틀린 지적은 없었다. 높음 2건(#1·#2)은 직접 재현해 확인했다. 테스트 191개 → 217개, 모두 통과. spec v1.11에 규칙 반영.

| # | 지적 | 판단 | 반영 | 확인 테스트 |
|---|---|---|---|---|
| 1 | 줄기 탐색 상한이 `>=`만 봄 | 맞음 (재현: `>3.9`·`~=3.10`·`==3.11.*`·`>=3.10.1` 모두 보류) | `mentioned_minors()`: 연산자 무관 조건 줄기 + 1까지 탐색 | `test_planner.py::test_review_1_*` (5가지 조건) |
| 2 | 조회 실패를 "못 찾음"으로 단정, 하나가 전체를 막음 | 맞음 (재현) | 패키지별 최소 줄기 → 가장 높은 것. 조회 실패는 "확인 못 함", 나머지는 계속 | `test_review_2_*` |
| 3 | 사실 조회에서 LLM이 버전 비교 | 맞음 (대표 요청 2번이 이 경로) | `fact_tools.py`: 코드가 설치 가능한 최신·남은 취약점 수 계산해 전달, 원본 목록 안 줌. Tool 최소 1회 강제, 최대 3회 이어 부르기. 실제 GMS로 "django 4.2.30, 취약점 8건" 확인 | `test_review_3_*` |
| 4 | 설치 가능한 버전이 없으면 재계획 안 함 | 맞음 | 위반으로 보고 재계획 | `test_review_4_*` |
| 5 | 재시작 뒤 로그 순번 충돌로 유실 | 맞음 | 저장 순번은 DB 기준(MAX+1)으로 로깅 Agent가 매김 | `test_events.py::test_review_5_*` |
| 6 | 모든 Tool이 같은 이유로 실패해도 끝까지 진행 | 맞음 (spec 규칙) | call_tools 뒤 바로 안내하고 끝냄 | `test_review_6_*` |
| 7 | 이상한 응답 형식이 예외·INTERNAL_ERROR | 일부 맞음 (레지스트리 경유 시 예외는 안 남) | 해석 단계 `safe_parse` → UPSTREAM_ERROR, `r.json()` 모든 오류 처리 | `test_tools.py::test_malformed_*`, `test_bad_charset_*` |
| 8 | 로그로 "왜 이 버전·이 순서"를 알 수 없음 | 맞음 (완료 기준) | `judgment`에 패키지별 등급·목표·상태, 새 이벤트 `plan_built`에 정렬 규칙·순서·회차 | `test_review_8_*` |
| 9 | 보류 선택 기준 없음 | 확인 필요 → 결정 | 기본 업그레이드, 사용자가 명시적으로 거부할 때만 보류. 사용자 메시지 전달 | `test_review_9_*` |
| 10 | 안전 패키지도 버전 조회, 판단 단계 순차 호출, 캐시 문구 | 확인 필요 → 결정 | 취약점 있는 패키지만 버전 조회, 목표 재조회 병렬. 캐시는 요청 안에서만(spec 문구 수정) | `test_review_10_*` |
| 11 | Python 2.7 반복 질문, OS만 바꾸면 이전 버전 남음 | 확인 필요 → 결정 | 2.x 수용(3.0부터 탐색), OS 바뀌면 버전 비우고 다시 물음 | `test_review_11_*`, `test_python2_*` |
| 12 | 목표가 현재보다 낮을 수 있음 | 확인 필요 → 결정 | 현재보다 높지 않으면 위반 → 재계획 | `test_review_12_*` |
| 13 | 3일차 범위 / 계획 없이 확정 | 확인 필요 → 일부 지금 반영 | 직전 계획 없으면 "확정할 계획이 아직 없어요" | `test_session.py::test_review_13_*` |

반영 중 따로 발견한 것: 사실 조회 수정 때 `brain.py`가 중복으로 붙는 편집 실수가 있었고, 실제 GMS 실행에서 실패로 드러나 바로 고침(테스트는 가짜 LLM이라 못 잡음 → 실제 확인 스크립트가 필요한 이유).
