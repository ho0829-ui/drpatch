# 프로젝트: sudo-patch
서버 패치·EOL 점검 플래너. freeze로 만든 requirements.txt + OS·Python 버전을 받아 회차별 패치 계획을 만드는 Agent 서비스.
Python 3.10+, FastAPI, SQLite, LangGraph + langchain-openai, 화면은 HTML/CSS/JS. 명세는 docs/spec.md.

## 명령어
- 설치: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- 테스트: `pytest -q`
- 실행: `uvicorn app.main:app --reload` → 화면은 http://localhost:8000

## 규칙 (이 프로젝트에서만 해당되는 것)
- LLM은 Tool의 종류와 순서만 계획한다. 패키지마다 Tool을 반복 호출하는 건 코드가 펼친다.
- 버전 비교, requires_python 판정, 우선순위 정렬, 회차 나누기는 코드로 계산한다. LLM에게 맡기지 않는다.
- 외부 API는 `app/tools/` 안에서만 호출한다. 모든 Tool은 예외를 던지지 않고 `{ok:false, error:{code, message}}`로 반환한다.
- API로 확인하지 못한 값(심각도, 지원 종료일 등)을 지어내지 않는다. 없으면 "미상" / "확인 못 함"으로 둔다.
- 테스트는 네트워크를 쓰지 않는다. 외부 응답은 `tests/fixtures/`의 저장본을 쓴다.
- requirements.txt의 라이브러리 버전은 수업 명세서 버전으로 고정한다. 새 라이브러리를 추가하기 전에 먼저 물어본다.
- 메인 Agent는 이벤트를 큐에 넣기만 하고 로깅을 기다리지 않는다.
- `docs/course/`는 대외비 수업 자료다. 읽기만 하고, 커밋하거나 내용을 코드·문서·웹 검색어에 옮기지 않는다. 요구사항은 번호(F3001 등)로만 참조한다.
- agy가 코드를 바꿀 때는 `agy/` 로 시작하는 브랜치에서만 작업하고, main에 합치기 전 Claude Code가 diff와 테스트를 확인한다.
- API 키는 `.env`에만 둔다. 화면에는 오류 상세 대신 짧은 안내만 보여준다.

## 작업 방식
- docs/tasks.md의 작업을 하나씩 진행하고, 끝나면 체크
- 완료 = 테스트 통과
- 구현 전에 계획을 먼저 보여주기
- 방법이 여러 가지면 2~3개 선택지를 장단점과 함께 제안하기
- spec과 다르게 구현해야 하면, 코드보다 spec 변경을 먼저 제안하기

## 세션 인수인계 (Claude Code ↔ agy 공용)
- 시작 시: docs/HANDOFF.md와 `git log -5`를 먼저 읽고 이어서 진행
- 작업 단위가 끝날 때마다: 커밋하고 HANDOFF.md 갱신
- "인수인계" 요청 시: 진행 중이던 작업은 WIP 커밋 후 HANDOFF.md 갱신
