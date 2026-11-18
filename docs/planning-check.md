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

## API 출처·이용 조건
- (대기) agy(Flash)가 `docs/research/api-terms.md`에 조사 → 끝나면 여기에 출처 URL과 함께 요약
