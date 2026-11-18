# 4. 직접 해 보는 과제

쉬운 것부터. 고쳐 보는 과제는 **새 브랜치**에서 하고, 끝나면 `git checkout main`으로 돌아온다.
```bash
git switch -c study/연습
```

## A. 읽고 맞춰 보기 (코드 안 고침)
1. **로그와 코드 맞추기**: 화면에서 계획을 하나 만들고 실행 로그 탭을 연다. 이벤트마다 그 이벤트를 만든 코드 위치를 찾아 적어 본다.
   - 예: `replan` → graph.py `replan` 노드의 `emit("replan", ...)`
2. **테스트 이름 읽기**: `tests/test_planner.py`의 테스트 이름만 쭉 읽고, spec "판단 규칙"의 어느 문장을 지키는 테스트인지 짝지어 본다.
3. **저장본 열어 보기**: `tests/fixtures/osv_requests_2.19.0.json`을 열어 취약점 10건이 왜 5건으로 묶이는지 `aliases`를 보고 직접 세어 본다 (vulns.py `group_vulns`).

## B. 한 줄 바꿔 보고 결과 예상하기
각각 **바꾸기 전에 결과를 예상해서 적고**, 테스트를 돌려 맞는지 본다. 끝나면 되돌린다.
1. [runner.py](../../app/agent/runner.py) `MAX_WORKERS = 4` → `1`. `scripts/run_agent.py`를 돌리면 시간이 어떻게 변할까?
2. [rounds.py](../../app/agent/planner/rounds.py) `MAX_ROUNDS = 3` → `1`. `pytest -q tests/test_planner.py`에서 어떤 테스트가 깨질까? 왜?
3. [python_upgrade.py](../../app/agent/planner/python_upgrade.py) `MAX_REPLANS = 3` → `1`. spec 예시는 어떻게 될까? (힌트: 3.10이 종료라 2회 필요)
4. [priority.py](../../app/agent/planner/priority.py)에서 정렬 키의 순서를 (종료일, 등급)으로 바꾸면? 어떤 테스트가 깨지고, 그게 왜 잘못된 계획인지 말로 설명해 본다.

## C. 작은 기능 추가 (테스트부터 쓰기)
1. **회차 간격 "매월"을 30일 대신 실제 달력 한 달로** (11/21 → 12/21). rounds.py `split_rounds`의 날짜 계산. 먼저 테스트를 쓰고(빨강), 고치고(초록).
2. **조회 제외 이유 하나 추가**: `pkg==1.0 ; python_version < "3"`처럼 Python 2 전용 표시가 붙은 줄은 "Python 2 전용"으로 제외. parsing/requirements.py + 테스트.
3. **새 이벤트**: build 노드에서 "미배정이 생겼다"면 `warning` 이벤트를 하나 더 발행하고, 화면 실행 단계 패널에 노란 줄로 표시 (render.js `eventItem`).

## D. 설명해 보기 (말로)
- "LLM이 하는 일과 코드가 하는 일을 왜 나눴나요?" 를 1분 안에.
- "재계획은 언제, 몇 번까지 일어나나요?" 를 spec 예시로.
- "로깅이 멈춰도 대화가 되는 이유는?" 를 이벤트 버스 그림으로.
- 막히면 03-design-decisions.md의 표를 다시 본다.
