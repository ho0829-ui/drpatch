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
