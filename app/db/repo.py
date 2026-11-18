"""SQLite 읽기·쓰기 (표준 라이브러리 sqlite3). 연결은 쓰는 스레드마다 따로 연다.

이번 범위: 스키마 준비 + events. sessions·plans는 Memory·계획 CRUD 작업에서 채운다.
"""

import json
import os
import sqlite3
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


def init_db(path: str | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))


# ── events (실행 로그) ───────────────────────────────────
def insert_event(conn: sqlite3.Connection, event: dict) -> None:
    conn.execute(
        "INSERT INTO events (session_id, seq, type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (event["session_id"], event["seq"], event["type"],
         json.dumps(event["payload"], ensure_ascii=False, default=str), event["created_at"]),
    )
    conn.commit()


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
