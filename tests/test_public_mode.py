"""공개 모드 (spec v1.24): 내 데이터만 보기, 호출 상한, 로컬 기본은 그대로. 네트워크 없음."""

import pytest
from fastapi.testclient import TestClient
from test_agent_graph import EXAMPLE_MESSAGE, FakeBrain, Transport

from app.db import repo
from app.main import app
from app.public import PublicGuard, PublicSettings, RateLimiter
from app.tools import http

FREEZE = b"requests==2.19.0\ndjango==2.2.0\n"


def _plan(session_id: str, date: str = "2026-12-01") -> dict:
    return {"session_id": session_id, "round_no": 1, "date": date, "window_start": "22:00", "window_end": "23:00",
            "items": [{"name": "requests", "current_version": "2.19.0"}]}


@pytest.fixture
def public_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "public.db"))
    monkeypatch.setenv("PUBLIC_MODE", "1")
    monkeypatch.setenv("PUBLIC_CHAT_PER_HOUR", "2")
    monkeypatch.setenv("PUBLIC_UPLOAD_PER_HOUR", "3")
    monkeypatch.setattr(http, "transport", Transport())
    with TestClient(app) as c:
        app.state.brain = FakeBrain(EXAMPLE_MESSAGE)
        yield c


@pytest.fixture
def local_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "local.db"))
    monkeypatch.delenv("PUBLIC_MODE", raising=False)
    with TestClient(app) as c:
        yield c


def H(sid: str) -> dict:
    return {"X-Session-Id": sid}


def test_health_tells_public(public_client):
    assert public_client.get("/health").json() == {"ok": True, "public": True}


def test_plans_only_mine_in_public(public_client):
    a, b = "a" * 32, "b" * 32
    with repo.connect(app.state.db_path) as conn:
        pa = repo.insert_plan(conn, _plan(a))
        pb = repo.insert_plan(conn, _plan(b))
    # 목록: 쿼리로 남의 세션을 달라고 해도 내 것만
    mine = public_client.get(f"/plans?session_id={b}", headers=H(a)).json()
    assert [p["id"] for p in mine] == [pa["id"]]
    assert public_client.get("/plans").json() == []  # 세션 없으면 빈 목록
    # 남의 계획은 없는 것처럼 404 (보기·고치기·지우기)
    assert public_client.get(f"/plans/{pb['id']}", headers=H(a)).status_code == 404
    assert public_client.put(f"/plans/{pb['id']}", json={"status": "done"}, headers=H(a)).status_code == 404
    assert public_client.delete(f"/plans/{pb['id']}", headers=H(a)).status_code == 404
    assert public_client.get(f"/plans/{pb['id']}", headers=H(b)).status_code == 200
    # 같은 날 같은 시각이어도 남의 계획과는 겹침으로 보지 않는다
    assert mine[0]["overlaps"] == []


def test_create_plan_forces_owner(public_client):
    a = "a" * 32
    body = {**_plan("z" * 32)}
    r = public_client.post("/plans", json=body, headers=H(a))
    assert r.status_code == 201 and r.json()["session_id"] == a
    assert public_client.post("/plans", json=body).status_code == 400


def test_logs_only_mine_in_public(public_client):
    a, b = "a" * 32, "b" * 32
    with repo.connect(app.state.db_path) as conn:
        for sid in (a, b):
            conn.execute("INSERT INTO events (session_id, seq, type, payload_json, created_at) "
                         "VALUES (?, 1, 'step_start', '{}', '2026-11-19T00:00:00+00:00')", (sid,))
        conn.commit()
    assert [r["session_id"] for r in public_client.get("/logs", headers=H(a)).json()] == [a]
    assert public_client.get("/logs").json() == []
    assert public_client.get(f"/logs/{b}", headers=H(a)).status_code == 404
    assert public_client.delete(f"/logs/{b}", headers=H(a)).status_code == 404
    assert public_client.get(f"/logs/{b}", headers=H(b)).status_code == 200


def test_calendar_events_scoped_by_owner(public_client):
    a, b = "a" * 32, "b" * 32
    ev = {"title": "배포", "date": "2026-12-01", "start": "21:00", "end": "23:00"}
    ea = public_client.post("/calendar/events", json=ev, headers=H(a)).json()
    public_client.post("/calendar/events", json={**ev, "title": "회의"}, headers=H(b))
    q = "/calendar/events?date_from=2026-12-01&date_to=2026-12-01"
    assert [e["title"] for e in public_client.get(q, headers=H(a)).json()] == ["배포"]
    assert public_client.get(q).json() == []
    assert public_client.post("/calendar/events", json=ev).status_code == 400  # 세션 없으면 못 넣음
    assert public_client.delete(f"/calendar/events/{ea['id']}", headers=H(b)).status_code == 404
    assert public_client.delete(f"/calendar/events/{ea['id']}", headers=H(a)).status_code == 204


def test_chat_and_upload_rate_limited(public_client):
    sid = public_client.post("/upload", content=FREEZE).json()["session_id"]
    for _ in range(2):
        public_client.post("/upload", content=FREEZE, params={"session_id": sid})
    r = public_client.post("/upload", content=FREEZE, params={"session_id": sid})
    assert r.status_code == 429 and "잠시 뒤" in r.json()["detail"]

    for _ in range(2):
        assert public_client.post("/chat", json={"session_id": sid, "message": "안녕"}).status_code == 200
    r = public_client.post("/chat", json={"session_id": sid, "message": "안녕"})
    assert r.status_code == 429


def test_local_mode_unchanged(local_client):
    a, b = "a" * 32, "b" * 32
    with repo.connect(app.state.db_path) as conn:
        repo.insert_plan(conn, _plan(a))
        repo.insert_plan(conn, _plan(b))
    assert len(local_client.get("/plans").json()) == 2  # 로컬은 전체 (지금과 같음)
    assert local_client.get("/health").json() == {"ok": True, "public": False}


def test_rate_limiter_window_and_ip_key():
    t = [0.0]
    lim = RateLimiter(2, 60, clock=lambda: t[0])
    assert lim.allow("x") and lim.allow("x") and not lim.allow("x")
    assert lim.allow("y")  # 키마다 따로
    t[0] = 61
    assert lim.allow("x")  # 창이 지나면 다시
    assert RateLimiter(0, 60).allow("x")  # 0이면 상한 없음


def test_ip_limit_does_not_eat_daily_budget():
    t = [0.0]
    g = PublicGuard(PublicSettings(enabled=True, chat_per_hour=1, chat_per_day=3), clock=lambda: t[0])

    class Req:
        def __init__(self, ip):
            self.headers = {"x-forwarded-for": f"{ip}, 10.0.0.1"}
            self.client = None

    g.check_chat(Req("1.1.1.1"))
    for _ in range(3):  # 같은 IP가 막힌 시도는 하루 횟수를 깎지 않는다
        with pytest.raises(Exception):
            g.check_chat(Req("1.1.1.1"))
    g.check_chat(Req("2.2.2.2"))
    g.check_chat(Req("3.3.3.3"))
    with pytest.raises(Exception):
        g.check_chat(Req("4.4.4.4"))  # 하루 3회 다 씀


def test_init_db_wal_and_indexes(tmp_path):
    path = str(tmp_path / "w.db")
    repo.init_db(path)
    with repo.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        names = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert {"idx_plans_session", "idx_calendar_owner"} <= names


def test_init_db_old_calendar_without_owner(tmp_path):
    """owner 칸이 없던 옛 DB도 칸을 더한 뒤 색인을 만든다."""
    import sqlite3
    path = str(tmp_path / "old.db")
    with sqlite3.connect(path) as c:
        c.execute("CREATE TABLE calendar_events (id INTEGER PRIMARY KEY, title TEXT NOT NULL, date TEXT NOT NULL, "
                  "start_time TEXT, end_time TEXT, source TEXT NOT NULL DEFAULT 'user', plan_id INTEGER, "
                  "created_at TEXT NOT NULL)")
    repo.init_db(path)
    with repo.connect(path) as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(calendar_events)")}
    assert "owner" in cols


def test_purge_older_than(tmp_path):
    from datetime import datetime, timezone
    path = str(tmp_path / "p.db")
    repo.init_db(path)
    old, new = "o" * 32, "n" * 32
    with repo.connect(path) as conn:
        for sid, ts in ((old, "2026-11-01T00:00:00+00:00"), (new, "2026-11-19T00:00:00+00:00")):
            conn.execute("INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)", (sid, ts, ts))
            conn.execute("INSERT INTO events (session_id, seq, type, payload_json, created_at) "
                         "VALUES (?, 1, 'x', '{}', ?)", (sid, ts))
            conn.execute("INSERT INTO calendar_events (title, date, created_at, owner) VALUES ('t', '2026-12-01', ?, ?)",
                         (ts, sid))
            repo.insert_plan(conn, {**_plan(sid)})
        # 세션 없이 남은 오래된 로그
        conn.execute("INSERT INTO events (session_id, seq, type, payload_json, created_at) "
                     "VALUES ('ghost', 1, 'x', '{}', '2026-11-01T00:00:00+00:00')")
        conn.commit()
        counts = repo.purge_older_than(conn, 7, now=datetime(2026, 11, 19, tzinfo=timezone.utc))
        assert counts == {"sessions": 1, "plans": 1, "events": 2, "calendar_events": 1}
        assert [r["id"] for r in conn.execute("SELECT id FROM sessions")] == [new]
        assert repo.purge_older_than(conn, 0) == {"sessions": 0, "plans": 0, "events": 0, "calendar_events": 0}


def test_cors_allows_pages_origin_only(local_client):
    pre = {"Origin": "https://ho0829-ui.github.io", "Access-Control-Request-Method": "POST",
           "Access-Control-Request-Headers": "content-type,x-session-id",
           "Access-Control-Request-Private-Network": "true"}
    r = local_client.options("/chat", headers=pre)
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "https://ho0829-ui.github.io"
    assert "x-session-id" in r.headers["access-control-allow-headers"].lower()
    assert r.headers.get("access-control-allow-private-network") == "true"
    bad = local_client.options("/chat", headers={**pre, "Origin": "https://evil.example"})
    assert bad.status_code == 400 and "access-control-allow-origin" not in bad.headers  # 브라우저가 막음
