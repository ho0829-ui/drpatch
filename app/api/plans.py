"""계획 관리 (F3015~F3016): 저장·목록·상세·수정·삭제. 저장·수정 응답에 겹침 경고(overlaps)."""

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
    return with_overlaps(conn, repo.update_plan(conn, plan_id, changes))


@router.delete("/{plan_id}", status_code=204)
def delete_plan(plan_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    if not repo.delete_plan(conn, plan_id):
        raise HTTPException(status_code=404, detail=NOT_FOUND)
