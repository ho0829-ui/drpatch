"""캘린더 구현체: 인터페이스 + 로컬(SQLite). Google Calendar 구현체는 같은 인터페이스로 교체한다.

일정 모양: {id, title, date(YYYY-MM-DD), start(HH:MM|None), end(HH:MM|None), source, plan_id}
"""

import os
from datetime import datetime, timezone
from typing import Protocol

from dotenv import load_dotenv

from app.db import repo

SOURCE_USER = "user"
SOURCE_APP = "sudo-patch"


class CalendarBackend(Protocol):
    name: str

    def list_events(self, date_from: str, date_to: str) -> list[dict]: ...
    def add_event(self, title: str, date: str, start: str | None = None, end: str | None = None,
                  source: str = SOURCE_USER, plan_id: int | None = None) -> dict: ...
    def find_by_plan(self, plan_id: int) -> dict | None: ...
    def delete_event(self, event_id: int) -> bool: ...


def _row(r) -> dict:
    return {"id": r["id"], "title": r["title"], "date": r["date"], "start": r["start_time"], "end": r["end_time"],
            "source": r["source"], "plan_id": r["plan_id"]}


class LocalCalendar:
    """SQLite calendar_events 표. 요청마다 연결을 새로 연다 (스레드 안전).

    owner가 None이면 모든 일정(로컬 기본). 문자열이면 그 주인(세션)의 일정만 보고·넣고·지운다 (공개 모드, spec v1.24).
    """

    name = "local"

    def __init__(self, db_path: str | None = None, owner: str | None = None):
        self.db_path = db_path
        self.owner = owner

    def for_owner(self, owner: str | None) -> "LocalCalendar":
        return LocalCalendar(self.db_path, owner)

    def _where_owner(self) -> tuple[str, tuple]:
        return ("", ()) if self.owner is None else (" AND owner = ?", (self.owner,))

    def list_events(self, date_from: str, date_to: str) -> list[dict]:
        extra, args = self._where_owner()
        with repo.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM calendar_events WHERE date BETWEEN ? AND ?" + extra +
                " ORDER BY date, COALESCE(start_time, '00:00'), id",
                (date_from, date_to, *args)).fetchall()
        return [_row(r) for r in rows]

    def add_event(self, title, date, start=None, end=None, source=SOURCE_USER, plan_id=None) -> dict:
        with repo.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO calendar_events (title, date, start_time, end_time, source, plan_id, created_at, owner) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, date, start, end, source, plan_id, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 self.owner))
            conn.commit()
            row = conn.execute("SELECT * FROM calendar_events WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row(row)

    def find_by_plan(self, plan_id: int) -> dict | None:
        extra, args = self._where_owner()
        with repo.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM calendar_events WHERE plan_id = ?" + extra + " ORDER BY id LIMIT 1",
                               (plan_id, *args)).fetchone()
        return _row(row) if row else None

    def delete_event(self, event_id: int) -> bool:
        extra, args = self._where_owner()
        with repo.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM calendar_events WHERE id = ?" + extra, (event_id, *args))
            conn.commit()
        return cur.rowcount > 0


def scoped(calendar, owner: str | None):
    """공개 모드면 그 주인 것만 다루는 캘린더로. 주인 구분을 못 하는 구현체는 그대로."""
    if calendar is None or owner is None:
        return calendar
    return calendar.for_owner(owner) if hasattr(calendar, "for_owner") else calendar


def make_calendar(db_path: str | None = None) -> CalendarBackend | None:
    """.env의 CALENDAR_BACKEND로 고른다. off면 None (캘린더 판단을 건너뜀)."""
    load_dotenv()
    kind = (os.getenv("CALENDAR_BACKEND") or "local").strip().lower()
    if kind == "local":
        return LocalCalendar(db_path)
    if kind == "google":
        from app.calendar.google import GoogleCalendar  # GOOGLE_CALENDAR_TOKEN(OAuth access token) 필요

        return GoogleCalendar()
    return None
