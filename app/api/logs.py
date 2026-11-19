"""실행 로그 (F3014): 세션 목록·상세(실행 순서대로)·삭제. 수정 주소는 두지 않는다."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_conn
from app.db import repo
from app.public import owner_of

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
def list_logs(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    rows = repo.list_log_sessions(conn)
    owner = owner_of(request)
    return rows if owner is None else [r for r in rows if owner and r["session_id"] == owner]


def _check_owner(request: Request, session_id: str) -> None:
    owner = owner_of(request)
    if owner is not None and session_id != owner:  # 공개 모드: 남의 로그는 없는 것처럼
        raise HTTPException(status_code=404, detail="그 세션의 실행 로그가 없어요.")


@router.get("/{session_id}")
def get_log(request: Request, session_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    _check_owner(request, session_id)
    events = repo.get_events(conn, session_id)
    if not events:
        raise HTTPException(status_code=404, detail="그 세션의 실행 로그가 없어요.")
    return {"session_id": session_id, "events": events}


@router.delete("/{session_id}")
def delete_log(request: Request, session_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    _check_owner(request, session_id)
    deleted = repo.delete_events(conn, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="그 세션의 실행 로그가 없어요.")
    return {"session_id": session_id, "deleted": deleted}
