"""대화 (F3017·F3019): POST /chat → ndjson 스트리밍 (docs/architecture.md 7절).

줄 하나 = JSON 하나:
  {"type": "session", "session_id": ...}           첫 줄
  {"type": "step_start" | "tool_result" | ... }    실행 이벤트 (이 세션 것만, 발생 순서대로)
  {"type": "final", "answer": ..., "plan": ...}     마지막 줄
"확정해줘"면 API가 직전 제안 계획을 회차마다 저장하고 final의 confirmed에 담는다 (Tool 아님).
"""

import json
import threading

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.agent.session import chat_turn, new_session_id
from app.api.deps import save_confirmed_plan
from app.api.schemas import ChatIn
from app.db import repo
from app.events.bus import Event

router = APIRouter(tags=["chat"])

KEY_MISSING = "서버 설정(API 키)을 확인해 주세요. 지금은 대화를 처리할 수 없어요."
FAILED = "처리 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요."
POLL_SECONDS = 0.1


def _line(obj: dict) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, default=str) + "\n").encode("utf-8")


def public_event(e: Event) -> dict:
    """화면에 보내는 이벤트. 오류는 단계와 종류만 (상세는 로그 표에만, NF3002)."""
    payload = e.payload
    if e.type == "error":
        payload = {"step": payload.get("step"), "kind": payload.get("kind")}
    return {"type": e.type, "seq": e.seq, **payload}


def _final(session_id: str, out: dict | None, answer: str | None = None, confirmed=None) -> dict:
    if out is None:
        return {"type": "final", "session_id": session_id, "intent": "error", "answer": answer,
                "plan": None, "missing": [], "conditions": None, "confirmed": None, "saved": False}
    conditions = out["conditions"].model_dump(mode="json")
    return {
        "type": "final", "session_id": session_id, "intent": out["intent"], "answer": out["answer"],
        "plan": out["plan"], "missing": out["missing"], "conditions": conditions,
        "confirmed": confirmed, "saved": out["saved"],
    }


@router.post("/chat")
def chat(body: ChatIn, request: Request):
    app = request.app
    session_id = body.session_id or new_session_id()
    brain = app.state.brain
    if brain is None:  # API 키 누락 (F3019 안내)
        return StreamingResponse(iter([_line({"type": "session", "session_id": session_id}),
                                       _line(_final(session_id, None, KEY_MISSING))]),
                                 media_type="application/x-ndjson")

    bus = app.state.bus
    sub = bus.subscribe()
    box: dict = {}

    def work() -> None:
        try:
            box["out"] = chat_turn(session_id, body.message, brain, bus=bus, db_path=app.state.db_path)
        except Exception as e:
            box["error"] = type(e).__name__
            bus.publish(session_id, "error", {"step": "chat", "kind": type(e).__name__})

    worker = threading.Thread(target=work, name=f"chat-{session_id[:8]}", daemon=True)
    worker.start()

    def stream():
        try:
            yield _line({"type": "session", "session_id": session_id})
            while True:
                event = sub.get(timeout=POLL_SECONDS)
                if event is not None:
                    if event.session_id == session_id:
                        yield _line(public_event(event))
                    continue
                if not worker.is_alive():
                    while (event := sub.get(0)) is not None:  # 남은 것까지
                        if event.session_id == session_id:
                            yield _line(public_event(event))
                    break
            out = box.get("out")
            if out is None:
                yield _line(_final(session_id, None, FAILED))
                return
            confirmed = None
            if out["intent"] == "confirm" and out["last_plan"]:
                conn = repo.connect(app.state.db_path)
                try:
                    confirmed = save_confirmed_plan(conn, session_id, out["last_plan"], out.get("confirm_rounds"))
                finally:
                    conn.close()
            yield _line(_final(session_id, out, confirmed=confirmed))
        finally:
            sub.close()

    return StreamingResponse(stream(), media_type="application/x-ndjson")
