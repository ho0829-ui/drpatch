# 마지막 갱신: 2026-11-18 16:03 / 작성: Claude Code

## 지금 하던 것
- 2일차 [C] LangGraph 흐름 + 재계획 상한 테스트 끝 (전체 테스트 169개 통과, 실제 GMS로 계획·사실 조회·되묻기 3경로 확인)
  - app/agent/graph.py: build_graph / run_agent(message, conditions, brain, today, emit) → intent·answer·conditions·plan·missing·tool_plan·tool_calls
  - app/agent/brain.py: AgentBrain 인터페이스 + GmsBrain (analyze·plan_tools·choose_replan·answer_fact·write_response·chat, 구조화 출력)
  - app/agent/state.py: Conditions(Memory), 빠진 입력·되묻는 문장(코드), 우분투 20→20.04·3.8.10→3.8
  - app/agent/runner.py: ToolRunner (동시 4개, 요청 안 캐시, tool_call/tool_result 이벤트)
  - app/agent/render.py: 계획 dict, LLM 실패 시 기본 문장
  - scripts/run_agent.py: 실제 GMS+API 확인 (예시: Tool 13번, 약 25~28초)

## 다음에 할 것
- 2일차 [C] 대화 맥락(Memory) F3010: 세션 조건을 SQLite sessions 표에 저장·불러오기 (run_agent는 이미 이전 조건 위에 바뀐 것만 덮어씀)
- 2일차 [C] 이벤트 버스 + 로깅 Agent(F3012~F3013): run_agent의 emit 자리에 EventBus.publish 연결

## 주의
- 응답 시간: 예시 한 건 25~28초. 대부분 LLM 4번(analyze·plan·replan·respond). judge의 목표 버전 재조회는 패키지마다 순서대로 → 3일차 측정 때 병렬화 후보
- 재계획 방식은 LLM이 고름(upgrade_python/hold), 실패하면 upgrade_python. 되묻기 문장은 코드 (spec v1.9)
- 사실 조회 경로도 조건(os 등)을 Memory에 남김
- 구조는 docs/architecture.md (v1). /chat ndjson 스트리밍은 아직 없음
- OSV는 없는 패키지도 200 {} → 0건. endoflife.date는 없는 제품·줄기 모두 같은 404
- LLM: GMS gpt-6-luna, Responses API, temperature 생략 (app/llm.py)
- docs/course/는 대외비 (.gitignore). requirements.txt 버전 고정 (packaging만 수업 목록 밖)
- .venv는 Python 3.14.7
