"""계획 관리 (F3015~F3016): 저장·목록·상세·수정·삭제. 저장·수정 응답에 겹침 경고(overlaps)."""

from datetime import datetime, timezone
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_conn, with_overlaps
from app.api.schemas import PlanIn, PlanOut, PlanUpdate, _check_window
from app.db import repo
from app.public import owner_of

NO_SESSION = "허허, 먼저 파일을 올리거나 예시를 골라 주시죠."

router = APIRouter(prefix="/plans", tags=["plans"])
NOT_FOUND = "그런 계획이 없어요."


@router.get("", response_model=list[PlanOut])
def list_plans(request: Request, session_id: str | None = None, conn: sqlite3.Connection = Depends(get_conn)):
    owner = owner_of(request)
    if owner is not None:  # 공개 모드: 내 세션 것만 (쿼리의 session_id는 무시)
        if not owner:
            return []
        session_id = owner
    return [with_overlaps(conn, p, owner is not None) for p in repo.list_plans(conn, session_id)]


def _mine(request: Request, plan: dict | None) -> dict:
    """없거나 (공개 모드에서) 남의 계획이면 똑같이 404 — 있는지도 알리지 않는다."""
    owner = owner_of(request)
    if plan is None or (owner is not None and plan.get("session_id") != owner):
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return plan


@router.post("", response_model=PlanOut, status_code=201)
def create_plan(request: Request, body: PlanIn, conn: sqlite3.Connection = Depends(get_conn)):
    data = body.model_dump(mode="json")
    owner = owner_of(request)
    if owner is not None:
        if not owner:
            raise HTTPException(status_code=400, detail=NO_SESSION)
        data["session_id"] = owner
    plan = repo.insert_plan(conn, data)
    return with_overlaps(conn, plan, owner is not None)


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(request: Request, plan_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    plan = _mine(request, repo.get_plan(conn, plan_id))
    return with_overlaps(conn, plan, owner_of(request) is not None)


@router.put("/{plan_id}", response_model=PlanOut)
def update_plan(request: Request, plan_id: int, body: PlanUpdate, conn: sqlite3.Connection = Depends(get_conn)):
    current = _mine(request, repo.get_plan(conn, plan_id))
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

    return with_overlaps(conn, repo.update_plan(conn, plan_id, changes), owner_of(request) is not None)


@router.delete("/{plan_id}", status_code=204)
def delete_plan(request: Request, plan_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    _mine(request, repo.get_plan(conn, plan_id))
    if not repo.delete_plan(conn, plan_id):
        raise HTTPException(status_code=404, detail=NOT_FOUND)
