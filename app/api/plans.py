"""계획 관리 (F3015~F3016): 저장·목록·상세·수정·삭제. 저장·수정 응답에 겹침 경고(overlaps)."""

from datetime import datetime, timezone
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_conn, with_overlaps
from app.api.schemas import PlanIn, PlanOut, PlanUpdate, _check_window
from app.db import repo

router = APIRouter(prefix="/plans", tags=["plans"])
NOT_FOUND = "그런 계획이 없어요."


@router.get("", response_model=list[PlanOut])
def list_plans(session_id: str | None = None, conn: sqlite3.Connection = Depends(get_conn)):
    return [with_overlaps(conn, p) for p in repo.list_plans(conn, session_id)]


@router.post("", response_model=PlanOut, status_code=201)
def create_plan(body: PlanIn, conn: sqlite3.Connection = Depends(get_conn)):
    plan = repo.insert_plan(conn, body.model_dump(mode="json"))
    return with_overlaps(conn, plan)


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    plan = repo.get_plan(conn, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return with_overlaps(conn, plan)


@router.put("/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, body: PlanUpdate, conn: sqlite3.Connection = Depends(get_conn)):
    current = repo.get_plan(conn, plan_id)
    if current is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    changes = body.model_dump(mode="json", exclude_unset=True)
    try:  # 바꾼 뒤의 시작·종료 시각으로 검사 (하나만 바꿔도)
        _check_window(changes.get("window_start", current["window_start"]),
                      changes.get("window_end", current["window_end"]))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if "items" in changes and "status" not in changes:
        items = changes["items"] or []
        if items and all(it.get("done_at") for it in items):
            changes["status"] = "done"
            changes["done_at"] = current.get("done_at") or now_iso
        elif current.get("status") == "done" and any(not it.get("done_at") for it in items):
            changes["status"] = "planned"
            changes["done_at"] = None
    elif "status" in changes:
        if changes["status"] == "done":
            done_at = changes.get("done_at") or current.get("done_at") or now_iso
            changes["done_at"] = done_at
            if "items" not in changes and current.get("items"):
                changes["items"] = [{**it, "done_at": it.get("done_at") or done_at} for it in current["items"]]
        else:
            changes["done_at"] = None
            if "items" not in changes and current.get("items"):
                changes["items"] = [{**it, "done_at": None} for it in current["items"]]

    return with_overlaps(conn, repo.update_plan(conn, plan_id, changes))


@router.delete("/{plan_id}", status_code=204)
def delete_plan(plan_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    if not repo.delete_plan(conn, plan_id):
        raise HTTPException(status_code=404, detail=NOT_FOUND)
