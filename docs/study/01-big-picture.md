# 1. 큰 그림

## 이 서비스가 하는 일 (한 문장)
서버의 `pip freeze` 결과와 OS·Python 버전을 받아, **지원 종료일·취약점·설치 가능한 버전을 실제로 조회**하고, **위험한 것부터 회차별 패치 계획**을 세워 저장·관리하게 해 준다.

## 왜 "Agent"인가
LLM만으로 답하면 틀린다 (실측: [planning-check.md](../planning-check.md) "도메인 조건 확인").
- requests 2.19.0 취약점을 LLM은 "4건·Medium", 실제는 "5건·HIGH" → 우선순위가 바뀜
- "Python 3.8에서 django 몇까지?" → LLM은 "4.2 계열"까지만, 실제 답 "4.2.30, 그런데 취약점 8건 남음"은 조회해야 앎

그래서 **LLM은 판단·말하기**, **사실은 Tool(외부 API)**, **계산은 코드**로 나눴다.

## 역할 나누기 (이 프로젝트의 가장 중요한 규칙)
| 누가 | 하는 일 | 어디 |
|---|---|---|
| LLM | 의도 분류, 문장에서 조건 뽑기, Tool 종류·순서 고르기, 재계획 방식 고르기, 최종 문장 쓰기 | [app/agent/brain.py](../../app/agent/brain.py) |
| Tool (외부 API 3개) | 지원 종료일(endoflife.date), 취약점(OSV.dev), 버전 목록(PyPI) | [app/tools/](../../app/tools/) |
| 코드 | 파일 파싱, 버전 비교, Python 호환 판정, 우선순위, 회차 나누기, 저장, 되묻는 문장 | [app/agent/planner/](../../app/agent/planner/), [app/parsing/](../../app/parsing/) |

규칙의 원본: [AGENTS.md](../../AGENTS.md) "규칙", [spec.md](../spec.md) "LLM이 하는 일 / 코드가 하는 일".

> 생각해 볼 것: 왜 "버전 비교"를 LLM에게 맡기면 안 될까? (힌트: `4.2.30`과 `4.2.3` 중 어느 쪽이 큰가, `5.0rc1`은 정식 버전인가 — [versions.py](../../app/agent/planner/versions.py)의 `is_final`, `pick_latest`)

## 폴더 지도
```
app/
  main.py          서버 시작: DB 준비 → 이벤트 버스 → 로깅 Agent → LLM 준비, 라우터·화면 연결
  api/             HTTP 주소 (upload, chat, plans, logs) — 화면이 부르는 곳
  agent/
    session.py     대화 한 턴: 세션 불러오기 → run_agent → 저장 (Memory)
    graph.py       LangGraph 그래프: 노드 10개와 분기
    brain.py       LLM이 하는 판단만 모은 곳 (테스트는 가짜로 바꿔 끼움)
    runner.py      Tool 펼쳐 부르기 (동시 4개, 요청 안 캐시, 호출 이벤트)
    planner/       계산 (순수 함수): versions, python_upgrade, items, priority, rounds
    fact_tools.py  사실 질문용: Tool 결과를 코드가 먼저 계산해 LLM에 넘김
  tools/           외부 API 3개 + 공통 응답 모양(ok/fail) + 레지스트리
  parsing/         requirements.txt → 조회 / 제외(이유)
  events/          이벤트 버스(발행) + 로깅 Agent(구독·저장)
  db/              SQLite 표 3개 (sessions, plans, events)
web/               화면 (HTML·CSS·JS, 탭 3개)
tests/             테스트 + fixtures(실제 API 응답 저장본)
scripts/           실제 API·LLM으로 돌려 보는 확인 스크립트 (테스트 아님)
docs/              spec(명세), architecture(구조), 결정·리뷰·점검 기록
```

## 의존 방향 (위가 아래를 부른다, 거꾸로는 안 부른다)
```
web (화면)
  ↓ HTTP
api
  ↓
agent/session → agent/graph → brain (LLM) / runner → tools → 외부 API
                           ↘ planner (계산)
  ↘ events (발행만, 기다리지 않음) → 로깅 Agent → db
```
`tools`·`planner`·`parsing`은 FastAPI·LangGraph를 모른다 → 따로 떼어 테스트하기 쉽다 (NF3006 모듈 분리).

## 읽고 나서 답해 볼 질문
1. 사용자가 "확정해줘"라고 하면 Tool이 불리는가? (답: 아니다. [chat.py](../../app/api/chat.py)의 `stream` 안에서 `save_confirmed_plan`)
2. 외부 API를 부르는 코드는 몇 군데에 있는가? (답: `app/tools/` 안, 정확히는 [http.py](../../app/tools/http.py)의 `fetch_json` 한 곳)
3. LLM이 죽으면 서비스도 죽는가? (답: 아니다. 각 노드가 `except`로 기본값을 쓴다 — 02 문서에서 확인)
