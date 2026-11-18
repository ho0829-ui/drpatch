"""실행 로그 (F3014): 세션 목록·상세(실행 순서대로)·삭제. 수정 주소는 두지 않는다."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_conn
from app.db import repo

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
def list_logs(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return repo.list_log_sessions(conn)


@router.get("/{session_id}")
def get_log(session_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    events = repo.get_events(conn, session_id)
    if not events:
        raise HTTPException(status_code=404, detail="그 세션의 실행 로그가 없어요.")
    return {"session_id": session_id, "events": events}


@router.delete("/{session_id}")
def delete_log(session_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    deleted = repo.delete_events(conn, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="그 세션의 실행 로그가 없어요.")
    return {"session_id": session_id, "deleted": deleted}
