"""라우터가 같이 쓰는 것: 요청마다 DB 연결, 계획 저장 + 겹침 확인."""

import sqlite3
from collections.abc import Iterator

from fastapi import Request

from app.api.overlap import find_overlaps
from app.db import repo


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    conn = repo.connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


def with_overlaps(conn: sqlite3.Connection, plan: dict) -> dict:
    return {**plan, "overlaps": find_overlaps(plan, repo.plans_on_date(conn, plan["date"]))}


def save_confirmed_plan(conn: sqlite3.Connection, session_id: str, plan: dict) -> list[dict]:
    """직전 제안 계획을 회차마다 계획 1개로 저장한다. 같은 세션·회차·날짜·항목이 이미 있으면 다시 만들지 않는다."""
    existing = repo.list_plans(conn, session_id)
    saved = []
    for r in plan.get("rounds", []):
        row = {"session_id": session_id, "round_no": r["round_no"], "date": r["date"],
               "window_start": plan.get("window", {}).get("start"), "window_end": plan.get("window", {}).get("end"),
               "items": r["items"]}
        same = next((p for p in existing if (p["round_no"], p["date"], p["items"]) ==
                     (row["round_no"], row["date"], row["items"])), None)
        stored = same or repo.insert_plan(conn, row)
        saved.append(with_overlaps(conn, stored))
    return saved
