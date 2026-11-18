"""대화 한 턴 = 세션 불러오기 → run_agent → 저장 (F3010 Memory). /chat·/upload가 이 함수들만 부른다.

- 세션 ID가 없으면 새로 만든다 (uuid).
- 저장되는 것: 조건(바뀐 값만 갱신된 결과), 직전 메시지·답, 직전 제안 계획. API 결과는 저장하지 않는다.
- DB 읽기·쓰기가 실패해도 그 턴의 답은 돌려준다 (기억만 못 함).
"""

import uuid
from datetime import date

from app.agent.brain import AgentBrain
from app.agent.graph import run_agent
from app.agent.runner import ToolRunner, no_emit
from app.agent.state import Conditions
from app.db import repo
from app.events.bus import EventBus


NO_PLAN_TO_CONFIRM = "확정할 계획이 아직 없어요. 먼저 requirements.txt와 OS·Python 버전으로 계획을 세워 주세요."


def new_session_id() -> str:
    return uuid.uuid4().hex


def load_session(session_id: str, db_path: str | None = None) -> dict:
    """{conditions: Conditions, last_turn: dict|None, last_plan: dict|None}. 없거나 읽기 실패면 빈 세션."""
    try:
        with repo.connect(db_path) as conn:
            row = repo.get_session(conn, session_id)
    except Exception:
        row = None
    if row is None:
        return {"conditions": Conditions(), "last_turn": None, "last_plan": None}
    last_turn = {"message": row["last_message"], "answer": row["last_answer"]} if row["last_message"] else None
    return {"conditions": Conditions(**row["conditions"]), "last_turn": last_turn, "last_plan": row["last_plan"]}


def save_upload(session_id: str, packages: list[dict], excluded: list[dict], db_path: str | None = None) -> bool:
    """파일 업로드 결과를 세션 조건에 넣는다 (다른 조건은 그대로). 성공 여부를 돌려준다."""
    conditions = load_session(session_id, db_path)["conditions"]
    conditions = conditions.model_copy(update={"packages": packages, "excluded": excluded})
    try:
        with repo.connect(db_path) as conn:
            repo.save_session(conn, session_id, conditions.model_dump(mode="json"))
        return True
    except Exception:
        return False


def chat_turn(
    session_id: str | None,
    message: str,
    brain: AgentBrain,
    *,
    bus: EventBus | None = None,
    db_path: str | None = None,
    today: date | None = None,
    runner: ToolRunner | None = None,
    calendar=None,
) -> dict:
    """run_agent 결과 + session_id, last_plan(확정 대상), saved(기억 저장 성공 여부)."""
    session_id = session_id or new_session_id()
    session = load_session(session_id, db_path)
    emit = bus.emitter(session_id) if bus else no_emit
    if runner is not None:
        runner.emit = emit

    out = run_agent(message, session["conditions"], brain, today=today, emit=emit,
                    runner=runner, last_turn=session["last_turn"], calendar=calendar, db_path=db_path)

    # 새 계획을 만들었을 때만 확정 대상을 바꾼다 (사실 질문 뒤에 "확정해줘"해도 직전 계획이 남게)
    # 회차가 없는 결과(우선순위만)는 확정할 대상이 아니므로 직전 계획을 그대로 둔다
    last_plan = out["plan"] if out["plan"] and out["plan"]["rounds"] else session["last_plan"]
    if out["intent"] == "confirm" and last_plan is None:
        out = {**out, "answer": NO_PLAN_TO_CONFIRM}  # 리뷰 #13
    saved = True
    try:
        with repo.connect(db_path) as conn:
            repo.save_session(conn, session_id, out["conditions"].model_dump(mode="json"),
                              last_message=message, last_answer=out["answer"], last_plan=last_plan)
    except Exception:
        saved = False
        emit("error", {"step": "save_session", "kind": "db"})
    return {**out, "session_id": session_id, "last_plan": last_plan, "saved": saved}
