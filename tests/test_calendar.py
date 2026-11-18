"""심화 캘린더 연동 (F3023): 로컬 구현체, Tool 2개, 겹치는 회차 이동, 확정 시 등록, API."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from test_agent_graph import EXAMPLE_FILE, EXAMPLE_MESSAGE, TODAY, FakeBrain, Transport, collect

from app.agent.brain import Analysis
from app.agent.graph import run_agent
from app.agent.planner.calendar_fit import find_free_date
from app.calendar.backend import LocalCalendar
from app.db import repo
from app.main import app
from app.tools import http
from app.tools.base import INVALID_INPUT
from app.tools.default import build_registry


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "cal.db")
    repo.init_db(path)
    return path


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(http, "transport", Transport())


def ev(day, start=None, end=None, source="user", title="회의"):
    return {"id": 1, "title": title, "date": day, "start": start, "end": end, "source": source}


# ── 다음 빈 날 찾기 (순수 함수) ──────────────────────────
D = date(2026, 11, 21)


@pytest.mark.parametrize(
    "events,start,end,expected",
    [
        ([], "22:00", "24:00", D),
        ([ev("2026-11-21", "22:30", "23:00")], "22:00", "24:00", date(2026, 11, 22)),
        ([ev("2026-11-21", "10:00", "11:00")], "22:00", "24:00", D),  # 시간대가 안 겹침
        ([ev("2026-11-21")], "22:00", "24:00", date(2026, 11, 22)),  # 하루 종일 일정
        ([ev("2026-11-21", "09:00", "10:00")], None, None, date(2026, 11, 22)),  # 회차에 시각 없음 = 하루 전체
        ([ev("2026-11-21", "22:00", "23:00", source="sudo-patch")], "22:00", "24:00", D),  # 내가 등록한 일정은 무시
        ([ev("2026-11-21"), ev("2026-11-22")], "22:00", "24:00", date(2026, 11, 23)),
        ([ev(f"2026-11-{d}") for d in range(21, 29)], "22:00", "24:00", None),  # 7일 안에 빈 날 없음
    ],
)
def test_find_free_date(events, start, end, expected):
    assert find_free_date(D, start, end, events) == expected


# ── Tool 2개 (로컬 구현체) ───────────────────────────────
def test_calendar_tools_registered_as_local(db):
    reg = build_registry(LocalCalendar(db), db)
    kinds = {n: reg.get_spec(n).kind for n in reg.names()}
    assert kinds["list_calendar_events"] == kinds["add_calendar_event"] == "local"
    assert "list_calendar_events" not in build_registry().names()  # 캘린더가 없으면 등록 안 함


def test_list_events_tool_and_input_checks(db):
    cal = LocalCalendar(db)
    cal.add_event("배포 회의", "2026-11-21", "22:30", "23:00")
    reg = build_registry(cal, db)
    r = reg.call("list_calendar_events", {"date_from": "2026-11-21", "date_to": "2026-11-28"})
    assert r["ok"] and r["data"]["events"][0]["title"] == "배포 회의"
    assert reg.call("list_calendar_events", {"date_from": "2026-11-28", "date_to": "2026-11-21"})["error"]["code"] == INVALID_INPUT
    assert reg.call("list_calendar_events", {"date_from": "2026-01-01", "date_to": "2026-12-31"})["error"]["code"] == INVALID_INPUT


def test_add_event_takes_plan_id_only_and_is_idempotent(db):
    with repo.connect(db) as conn:
        plan = repo.insert_plan(conn, {"session_id": "s", "round_no": 1, "date": "2026-11-21", "window_start": "22:00",
                                       "window_end": "24:00", "items": [{"name": "Python"}, {"name": "Ubuntu"}]})
    reg = build_registry(LocalCalendar(db), db)
    first = reg.call("add_calendar_event", {"plan_id": plan["id"]})
    assert first["ok"] and first["data"]["created"] is True
    assert first["data"]["title"] == "[패치] 1회차 Python, Ubuntu"
    assert (first["data"]["date"], first["data"]["start"], first["data"]["end"]) == ("2026-11-21", "22:00", "24:00")
    again = reg.call("add_calendar_event", {"plan_id": plan["id"]})
    assert again["data"]["created"] is False and again["data"]["event_id"] == first["data"]["event_id"]
    assert reg.call("add_calendar_event", {"plan_id": 999})["error"]["code"] == "PLAN_NOT_FOUND"
    assert reg.call("add_calendar_event", {"plan_id": 1, "title": "x"})["error"]["code"] == INVALID_INPUT


# ── 판단에 반영: 겹치는 회차는 다음 빈 날로 ──────────────
def test_round_moves_to_next_free_day(offline, db):
    cal = LocalCalendar(db)
    cal.add_event("서버실 점검", "2026-11-21", "23:00", "23:30")
    events, emit = collect()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=emit, calendar=cal, db_path=db)
    rounds = out["plan"]["rounds"]
    assert (rounds[0]["date"], rounds[0]["moved_from"]) == ("2026-11-22", "2026-11-21")
    assert (rounds[1]["date"], rounds[1]["moved_from"]) == ("2026-12-05", None)
    assert out["plan"]["calendar_check"] == "확인함"
    check = next(p for e, p in events if e == "calendar_check")
    assert check["rounds"][0]["moved_from"] == "2026-11-21"
    assert any(e == "tool_result" and p["tool"] == "list_calendar_events" for e, p in events)  # Tool로 조회 (로그에 남음)


def test_no_free_day_keeps_date_with_conflict_warning(offline, db):
    cal = LocalCalendar(db)
    for d in range(21, 29):
        cal.add_event(f"출장 {d}", f"2026-11-{d}")
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, calendar=cal, db_path=db)
    first = out["plan"]["rounds"][0]
    assert first["date"] == "2026-11-21" and first["moved_from"] is None
    assert first["calendar_conflicts"] == ["출장 21"]


def test_calendar_failure_keeps_dates(offline, db):
    class Broken(LocalCalendar):
        def list_events(self, date_from, date_to):
            raise RuntimeError("down")

    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, calendar=Broken(db), db_path=db)
    assert out["plan"]["calendar_check"] == "확인 못 함"
    assert [r["date"] for r in out["plan"]["rounds"]] == ["2026-11-21", "2026-12-05"]


def test_without_calendar_check_is_off(offline):
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    assert out["plan"]["calendar_check"] == "사용 안 함"


# ── API + 확정 시 등록 ───────────────────────────────────
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "api.db"))
    monkeypatch.setenv("CALENDAR_BACKEND", "local")
    monkeypatch.setattr(http, "transport", Transport())
    with TestClient(app) as c:
        app.state.brain = FakeBrain(EXAMPLE_MESSAGE)
        yield c


def lines(r):
    import json

    return [json.loads(x) for x in r.text.splitlines() if x.strip()]


def test_calendar_api_and_confirm_registers(client):
    created = client.post("/calendar/events", json={"title": "배포", "date": "2026-11-21", "start": "22:30", "end": "23:00"})
    assert created.status_code == 201
    assert client.post("/calendar/events", json={"title": "x", "date": "2026-11-21", "start": "23:00", "end": "22:00"}).status_code == 422

    sid = client.post("/upload", content=b"requests==2.19.0\ndjango==2.2.0\n").json()["session_id"]
    final = lines(client.post("/chat", json={"session_id": sid, "message": "계획 짜줘"}))[-1]
    assert final["plan"]["rounds"][0]["date"] == "2026-11-22"  # 배포 일정을 피해 이동

    app.state.brain = FakeBrain(Analysis(intent="confirm", intent_reason="확정"))
    confirm = lines(client.post("/chat", json={"session_id": sid, "message": "확정해줘"}))
    confirmed = confirm[-1]["confirmed"]
    assert all(p["calendar_event"]["created"] for p in confirmed)
    assert any(l["type"] == "tool_result" and l["tool"] == "add_calendar_event" for l in confirm)

    events = client.get("/calendar/events", params={"date_from": "2026-11-21", "date_to": "2026-12-31"}).json()
    assert [(e["title"], e["source"]) for e in events][:2] == [("배포", "user"), ("[패치] 1회차 Python, Ubuntu", "sudo-patch")]
    assert client.delete(f"/calendar/events/{created.json()['id']}").status_code == 204
    assert client.delete(f"/calendar/events/{created.json()['id']}").status_code == 404


def test_calendar_off(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "off.db"))
    monkeypatch.setenv("CALENDAR_BACKEND", "off")
    with TestClient(app) as c:
        r = c.get("/calendar/events")
        assert r.status_code == 404 and "CALENDAR_BACKEND" in r.json()["detail"]
