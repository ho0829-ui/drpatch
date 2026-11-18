# 대표 시나리오·완료 기준 점검 (2026-11-18, 3일차)

실행: 서버(`uvicorn app.main:app`) + 실제 GMS(gpt-6-luna) + 실제 API, `scripts/run_scenarios.py` (HTTP로 /upload·/chat 호출).
입력 파일: 패키지 6개 + `-e git+…` + `celery>=4.0` (조회 제외 2줄).

## 대표 요청 (spec "대표 요청")
| # | 요청 | 결과 | 판정 |
|---|---|---|---|
| 1 | "Ubuntu 20.04, Python 3.8 서버야. 이 파일 기준으로 이번에 5개 올릴 계획 짜줘. 첫 점검은 11/21 22~24시, 격주로" | 27.6초, Tool 29번(실패 0), 재계획 2번(3.10 종료 → 3.11). 1회차 [pyyaml CRITICAL, Python 3.8→3.11, Ubuntu 20.04, jinja2] / 2회차 [django, requests, flask, urllib3] — Python 업그레이드가 필요한 패키지는 모두 2회차 | 통과 |
| 2 | "Python 3.8 서버인데 django 몇으로 올리면 돼?" (새 세션) | 사실 조회, Tool 2번. "3.8에서 설치 가능한 최신은 4.2.30, 취약점 8개" — 코드가 계산한 값 | 통과 |
| 3 | "Ubuntu 20.04, Python 3.8 서버인데 지금 뭐부터 해야 돼?" (파일 있음) | 처음엔 일정을 되묻기만 함(Tool 0번) → **고침 (spec v1.14)**: 29.4초, Tool 29번, 우선순위 [pyyaml, Python 3.8→3.11, Ubuntu, jinja2, django, requests, flask, urllib3] — Python 업그레이드가 필요한 것은 업그레이드 뒤 — 를 보여 주고 일정만 되물음 | 고친 뒤 통과 |
| 4 | "계획 짜줘" (파일 없음) | 빠진 6가지만 되물음, Tool 0번 | 통과 |
| 5 | "1회차 확정해줘" | 처음엔 1·2회차 모두 저장 → **고침**: 1회차만 저장 (Analysis.confirm_rounds) | 고친 뒤 통과 |

## 완료 기준 (spec "완료 기준")
| 기준 | 확인 | 근거 |
|---|---|---|
| "5개까지" → 위험한 것부터 회차, 현재→목표·이유 | ✅ | 시나리오 1, 화면 회차 카드 |
| 현재 Python에서 설치 안 되는 버전은 목표로 안 나옴 | ✅ | `test_planner.py`, 시나리오 1(Python 업그레이드 뒤 회차로) |
| 업그레이드뿐이면 업그레이드가 앞 회차 | ✅ | 시나리오 1, `test_spec_example_priority_and_rounds` |
| `-e`·`>=` 줄은 조회 제외, 오류 없음 | ✅ | 업로드 결과 "7번 줄 PyPI 출처 아님, 8번 줄 정확한 버전 아님" |
| 파일 없이 "계획 짜줘" → Tool 없이 묻기 | ✅ | 시나리오 4 |
| 한 Tool 실패해도 나머지 진행, "확인 못 함" | ✅ | `test_one_tool_failure_marks_only_that_package`, `test_review_2_*` |
| 겹치는 계획 저장 → 둘 다 저장 + 알림 | ✅ | 브라우저 확인(⚠ 경고), `test_overlap_warning_but_both_saved` |
| 로그 탭에서 순서·버전·재계획 이유 | ✅ | 브라우저 로그 탭: judgment·replan·plan_built |
| 로깅 멈춰도 대화 정상 | ✅ | `test_events.py` 4가지 경우 |
| 패키지 20개도 지장 없는 시간 | ✅ 기준 **60초 이내 + 실행 단계 실시간 표시** | 20개: 36.8초 → 재계획 후보 병렬 조회 후 35.2초 (Tool 65번, 실패 0) |

## 20개 응답 시간 내역 (개선 후)
| 단계 | 시간 | 비고 |
|---|---|---|
| analyze (LLM) | 4.3s | |
| plan_tools (LLM) | 4.5s | |
| call_tools | 5.5s | 동시 4개 |
| judge | 2.7s | 목표 버전 재조회 병렬 |
| replan | 8.3s (12.7s에서) | LLM 재계획 방식 선택 + 후보 버전 미리 병렬 조회 |
| respond (LLM) | 9.7s | |

남은 시간의 대부분(약 21초)은 LLM 4번. 더 줄이려면 LLM 호출 수를 줄여야 함 (예: 재계획 방식 선택을 사용자가 거부 표현을 했을 때만 LLM에 묻기) — 지금은 기준 안이라 그대로 둠.
