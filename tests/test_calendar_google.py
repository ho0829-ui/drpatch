"""F3023: 캘린더 구현체를 LocalCalendar → GoogleCalendar로 바꿔도 Tool 입출력 형식이 그대로인지 (네트워크 없음).

GoogleCalendar는 Google Calendar API v3를 흉내 낸 가짜 서버(FakeGoogle)에 붙인다.
같은 계획·같은 Tool 호출을 두 구현체에 보내고 결과를 나란히 비교한다.
"""

import itertools
from datetime import datetime
from urllib.parse import unquote

import pytest
import requests
from test_agent_graph import EXAMPLE_FILE, EXAMPLE_MESSAGE, TODAY, FakeBrain, Transport

from app.agent.graph import run_agent
from app.calendar.backend import LocalCalendar, make_calendar
from app.calendar.google import GoogleCalendar
from app.db import repo
from app.tools import http
from app.tools.default import build_registry

PREFIX = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


class FakeGoogle:
    """events.list(timeMin/timeMax/privateExtendedProperty) · insert · delete만 흉내 낸다."""

    def __init__(self):
        self.items: dict[str, dict] = {}
        self.ids = (f"g{n}abc" for n in itertools.count(1))
        self.calls: list[tuple[str, str]] = []
        self.status_override: int | None = None

    def __call__(self, method, url, params, body, headers):
        assert url.startswith(PREFIX) and headers["Authorization"] == "Bearer test-token"
        self.calls.append((method, url))
        if self.status_override:
            return self.status_override, {"error": {"code": self.status_override}}
        rest = unquote(url[len(PREFIX):].lstrip("/"))
        if method == "POST":
            event_id = next(self.ids)
            self.items[event_id] = {"id": event_id, "status": "confirmed", **body}
            return 200, self.items[event_id]
        if method == "DELETE":
            return (204, None) if self.items.pop(rest, None) else (404, None)
        items = list(self.items.values())
        if params.get("privateExtendedProperty"):
            key, value = params["privateExtendedProperty"].split("=")
            items = [g for g in items if g.get("extendedProperties", {}).get("private", {}).get(key) == value]
        if params.get("timeMin"):
            lo, hi = datetime.fromisoformat(params["timeMin"]), datetime.fromisoformat(params["timeMax"])

            def start(g):
                s = g["start"]
                return datetime.fromisoformat(s["dateTime"]) if "dateTime" in s else \
                    datetime.fromisoformat(s["date"] + "T00:00:00+09:00")

            items = sorted((g for g in items if lo <= start(g) < hi), key=start)
        return 200, {"items": items[: params.get("maxResults", 250)]}


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "cal.db")
    repo.init_db(path)
    return path


@pytest.fixture
def plan(db):
    with repo.connect(db) as conn:
        return repo.insert_plan(conn, {"session_id": "s", "round_no": 1, "date": "2026-11-21", "window_start": "22:00",
                                       "window_end": "24:00", "items": [{"name": "Python"}, {"name": "Ubuntu"}]})


def backends(db):
    fake = FakeGoogle()
    return {"local": LocalCalendar(db), "google": GoogleCalendar("test-token", "primary", "Asia/Seoul", send=fake)}, fake


def strip_id(d: dict, key: str) -> dict:
    return {k: v for k, v in d.items() if k != key}


def test_tools_have_same_input_output_on_local_and_google(db, plan):
    cals, _ = backends(db)
    out = {}
    for name, cal in cals.items():
        cal.add_event("배포 회의", "2026-11-21", "22:30", "23:00")
        cal.add_event("출장", "2026-11-23")  # 하루 종일
        reg = build_registry(cal, db)
        first = reg.call("add_calendar_event", {"plan_id": plan["id"]})
        again = reg.call("add_calendar_event", {"plan_id": plan["id"]})
        listed = reg.call("list_calendar_events", {"date_from": "2026-11-21", "date_to": "2026-11-28"})
        out[name] = (first, again, listed)

    (lf, la, ll), (gf, ga, gl) = out["local"], out["google"]
    # Tool 입력은 같은 모양(plan_id / date_from·date_to), 출력도 id만 빼면 같다
    assert strip_id(lf["data"], "event_id") == strip_id(gf["data"], "event_id") == {
        "title": "[패치] 1회차 Python, Ubuntu", "date": "2026-11-21", "start": "22:00", "end": "24:00", "created": True}
    assert la["data"]["created"] is ga["data"]["created"] is False  # 이미 등록된 계획은 새로 만들지 않음
    assert ga["data"]["event_id"] == gf["data"]["event_id"]
    local_events = [strip_id(e, "id") for e in ll["data"]["events"]]
    google_events = [strip_id(e, "id") for e in gl["data"]["events"]]
    assert sorted(local_events, key=str) == sorted(google_events, key=str)
    assert {e["source"] for e in google_events} == {"user", "sudo-patch"}
    assert next(e for e in google_events if e["title"] == "출장")["start"] is None


def test_google_failures_become_calendar_error_not_exceptions(db, plan):
    fake = FakeGoogle()
    reg = build_registry(GoogleCalendar("test-token", "primary", "Asia/Seoul", send=fake), db)
    fake.status_override = 401
    assert reg.call("list_calendar_events", {"date_from": "2026-11-21", "date_to": "2026-11-28"})["error"]["code"] == "CALENDAR_ERROR"
    assert reg.call("add_calendar_event", {"plan_id": plan["id"]})["error"]["code"] == "CALENDAR_ERROR"

    def down(*args):
        raise requests.ConnectionError("down")

    reg = build_registry(GoogleCalendar("test-token", "primary", "Asia/Seoul", send=down), db)
    assert reg.call("list_calendar_events", {"date_from": "2026-11-21", "date_to": "2026-11-28"})["error"]["code"] == "CALENDAR_ERROR"

    no_token = build_registry(GoogleCalendar("", send=fake), db)
    assert no_token.call("list_calendar_events", {"date_from": "2026-11-21", "date_to": "2026-11-28"})["error"]["code"] == "CALENDAR_ERROR"


def test_delete_event_same_result(db):
    cals, _ = backends(db)
    for cal in cals.values():
        ev = cal.add_event("회의", "2026-11-21", "10:00", "11:00")
        assert cal.delete_event(ev["id"]) is True
        assert cal.delete_event(ev["id"]) is False


def test_round_move_is_the_same_with_google(monkeypatch, db):
    monkeypatch.setattr(http, "transport", Transport())
    cals, _ = backends(db)
    plans = {}
    for name, cal in cals.items():
        cal.add_event("서버실 점검", "2026-11-21", "23:00", "23:30")
        out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, calendar=cal, db_path=db)
        plans[name] = [(r["date"], r["moved_from"]) for r in out["plan"]["rounds"]]
    assert plans["local"] == plans["google"] == [("2026-11-22", "2026-11-21"), ("2026-12-05", None)]


def test_make_calendar_picks_google(monkeypatch):
    monkeypatch.setenv("CALENDAR_BACKEND", "google")
    monkeypatch.setenv("GOOGLE_CALENDAR_TOKEN", "t")
    assert make_calendar().name == "google"
