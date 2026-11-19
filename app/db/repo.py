"""SQLite 읽기·쓰기 (표준 라이브러리 sqlite3). 연결은 쓰는 스레드마다 따로 연다.

범위: 스키마 준비, sessions(Memory), events(실행 로그). plans는 계획 CRUD 작업에서 채운다.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

SCHEMA = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = "data/sudo_patch.db"


def db_path() -> str:
    load_dotenv()
    return os.getenv("DB_PATH") or DEFAULT_DB_PATH


def connect(path: str | None = None) -> sqlite3.Connection:
    path = path or db_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


# 나중에 추가한 칸: 예전에 만든 DB 파일에도 붙인다 (CREATE TABLE IF NOT EXISTS는 칸을 추가하지 않음)
ADDED_COLUMNS = {
    "sessions": [
        "last_message TEXT",
        "last_answer TEXT",
        "last_plan_json TEXT",
        "weekdays TEXT",
        "weekly_count INTEGER",
        "week_interval INTEGER",
    ],
    "plans": ["status TEXT NOT NULL DEFAULT 'planned'", "done_at TEXT"],
}


def init_db(path: str | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        for table, columns in ADDED_COLUMNS.items():
            existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            for column in columns:
                if column.split()[0] not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── sessions (Memory) ────────────────────────────────────
CONDITION_COLUMNS = {  # Conditions 필드 → 표 칸
    "os_name": "os", "os_version": "os_version", "python_version": "python_version", "capacity": "capacity_n",
    "first_date": "first_date", "window_start": "window_start", "window_end": "window_end",
    "interval_days": "interval_days", "weekdays": "weekdays", "weekly_count": "weekly_count",
    "week_interval": "week_interval",
}


def _decode_weekdays(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    nums = [int(p) for p in raw.split(",") if p.strip().isdigit()]
    return nums or None


def _encode_weekdays(raw) -> str | None:
    if not raw:
        return None
    if isinstance(raw, str):
        return raw or None
    return ",".join(str(int(d)) for d in raw)


def get_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    """{conditions: dict, last_message, last_answer, last_plan} 또는 없으면 None."""
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        return None
    conditions = {field: row[column] for field, column in CONDITION_COLUMNS.items()}
    conditions["weekdays"] = _decode_weekdays(conditions["weekdays"])
    conditions["packages"] = json.loads(row["packages_json"])
    conditions["excluded"] = json.loads(row["excluded_json"])
    return {
        "conditions": conditions,
        "last_message": row["last_message"],
        "last_answer": row["last_answer"],
        "last_plan": json.loads(row["last_plan_json"]) if row["last_plan_json"] else None,
    }


def save_session(conn: sqlite3.Connection, session_id: str, conditions: dict, **last) -> None:
    """조건을 통째로 저장한다. last_message·last_answer·last_plan은 넘긴 것만 바꾼다."""
    values = {column: conditions.get(field) for field, column in CONDITION_COLUMNS.items()}
    values["weekdays"] = _encode_weekdays(values["weekdays"])
    values["packages_json"] = json.dumps(conditions.get("packages", []), ensure_ascii=False)
    values["excluded_json"] = json.dumps(conditions.get("excluded", []), ensure_ascii=False)
    for key in ("last_message", "last_answer"):
        if key in last:
            values[key] = last[key]
    if "last_plan" in last:
        values["last_plan_json"] = None if last["last_plan"] is None else json.dumps(last["last_plan"], ensure_ascii=False)
    now = _now()
    columns = ", ".join(values)
    marks = ", ".join("?" for _ in values)
    updates = ", ".join(f"{c} = excluded.{c}" for c in values)
    conn.execute(
        f"INSERT INTO sessions (id, {columns}, created_at, updated_at) VALUES (?, {marks}, ?, ?) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}, updated_at = excluded.updated_at",
        (session_id, *values.values(), now, now),
    )
    conn.commit()


# ── events (실행 로그) ───────────────────────────────────
def insert_event(conn: sqlite3.Connection, event: dict) -> int:
    """세션의 다음 순번으로 저장하고 그 순번을 돌려준다.

    버스의 순번은 프로세스 메모리에만 있어 서버를 다시 켜면 1부터 다시 시작한다. 그대로 저장하면
    UNIQUE(session_id, seq)에 걸려 로그가 사라지므로(2일차 리뷰 #5), 저장 순번은 DB 기준으로 매긴다.
    쓰는 곳이 로깅 Agent 스레드 하나라 순번이 겹치지 않고, 저장 순서 = 큐에 들어온 순서다.
    """
    seq = conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE session_id = ?",
                       (event["session_id"],)).fetchone()[0]
    conn.execute(
        "INSERT INTO events (session_id, seq, type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (event["session_id"], seq, event["type"],
         json.dumps(event["payload"], ensure_ascii=False, default=str), event["created_at"]),
    )
    conn.commit()
    return seq


def list_log_sessions(conn: sqlite3.Connection) -> list[dict]:
    """세션별 로그 목록 (최근 것부터)."""
    rows = conn.execute(
        "SELECT session_id, COUNT(*) AS events, MIN(created_at) AS started_at, MAX(created_at) AS last_at "
        "FROM events GROUP BY session_id ORDER BY last_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_events(conn: sqlite3.Connection, session_id: str) -> list[dict]:
    """한 세션의 이벤트를 발생 순서대로."""
    rows = conn.execute(
        "SELECT session_id, seq, type, payload_json, created_at FROM events WHERE session_id = ? ORDER BY seq",
        (session_id,),
    ).fetchall()
    return [
        {"session_id": r["session_id"], "seq": r["seq"], "type": r["type"],
         "payload": json.loads(r["payload_json"]), "created_at": r["created_at"]}
        for r in rows
    ]


def delete_events(conn: sqlite3.Connection, session_id: str) -> int:
    cur = conn.execute("DELETE FROM events WHERE session_id = ?", (session_id,))
    conn.commit()
    return cur.rowcount


# ── plans (회차 1개 = 계획 1개) ──────────────────────────
def _plan_row(row: sqlite3.Row) -> dict:
    keys = row.keys()
    return {
        "id": row["id"], "session_id": row["session_id"], "round_no": row["round_no"], "date": row["date"],
        "window_start": row["window_start"], "window_end": row["window_end"],
        "items": json.loads(row["items_json"]),
        "status": row["status"] if "status" in keys and row["status"] else "planned",
        "done_at": row["done_at"] if "done_at" in keys else None,
        "created_at": row["created_at"], "updated_at": row["updated_at"],
    }


def insert_plan(conn: sqlite3.Connection, plan: dict) -> dict:
    now = _now()
    cur = conn.execute(
        "INSERT INTO plans (session_id, round_no, date, window_start, window_end, items_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (plan.get("session_id") or "", plan.get("round_no") or 0, plan["date"], plan.get("window_start"),
         plan.get("window_end"), json.dumps(plan.get("items", []), ensure_ascii=False), now, now),
    )
    conn.commit()
    return get_plan(conn, cur.lastrowid)


def get_plan(conn: sqlite3.Connection, plan_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    return _plan_row(row) if row else None


def list_plans(conn: sqlite3.Connection, session_id: str | None = None) -> list[dict]:
    """날짜순 (같은 날이면 시작 시각, 없으면 앞으로)."""
    sql = "SELECT * FROM plans"
    args: tuple = ()
    if session_id:
        sql += " WHERE session_id = ?"
        args = (session_id,)
    sql += " ORDER BY date, COALESCE(window_start, '00:00'), id"
    return [_plan_row(r) for r in conn.execute(sql, args).fetchall()]


def plans_on_date(conn: sqlite3.Connection, day: str) -> list[dict]:
    return [_plan_row(r) for r in conn.execute("SELECT * FROM plans WHERE date = ? ORDER BY id", (day,)).fetchall()]


def update_plan(conn: sqlite3.Connection, plan_id: int, changes: dict) -> dict | None:
    """날짜·시각·항목·상태·완료시각을 바꾼다 (넘긴 것만)."""
    allowed = {
        "date": "date",
        "window_start": "window_start",
        "window_end": "window_end",
        "items": "items_json",
        "status": "status",
        "done_at": "done_at",
    }
    sets, args = [], []
    for key, column in allowed.items():
        if key in changes:
            value = changes[key]
            sets.append(f"{column} = ?")
            args.append(json.dumps(value, ensure_ascii=False) if key == "items" else value)
    if sets:
        conn.execute(f"UPDATE plans SET {', '.join(sets)}, updated_at = ? WHERE id = ?", (*args, _now(), plan_id))
        conn.commit()
    return get_plan(conn, plan_id)


def delete_plan(conn: sqlite3.Connection, plan_id: int) -> bool:
    cur = conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    conn.commit()
    return cur.rowcount > 0
