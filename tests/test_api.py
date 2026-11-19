"""백엔드 API (F3014~F3017, F3019). TestClient + 가짜 LLM + 저장된 API 응답 + 임시 DB."""

import json

import pytest
from fastapi.testclient import TestClient
from test_agent_graph import EXAMPLE_MESSAGE, FakeBrain, Transport

from app.agent.brain import Analysis
from app.main import app
from app.tools import http

FREEZE = b"requests==2.19.0\ndjango==2.2.0\n-e git+https://github.com/me/tool.git#egg=tool\n"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "api.db"))
    monkeypatch.setattr(http, "transport", Transport())
    with TestClient(app) as c:
        app.state.brain = FakeBrain(EXAMPLE_MESSAGE)
        yield c


def stream_lines(response) -> list[dict]:
    return [json.loads(line) for line in response.text.splitlines() if line.strip()]


def chat(client, message, session_id=None, brain=None):
    if brain is not None:
        app.state.brain = brain
    r = client.post("/chat", json={"session_id": session_id, "message": message})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/x-ndjson")
    return stream_lines(r)


# ── 업로드 ───────────────────────────────────────────────
def test_upload_parses_and_creates_session(client):
    r = client.post("/upload", content=FREEZE)
    body = r.json()
    assert r.status_code == 200 and len(body["session_id"]) == 32 and body["saved"]
    assert [p["name"] for p in body["packages"]] == ["requests", "django"]
    assert body["excluded"][0]["reason"] == "PyPI 출처 아님"


def test_upload_utf16_and_errors(client):
    assert client.post("/upload", content=FREEZE.decode().encode("utf-16")).json()["packages"][0]["name"] == "requests"
    assert client.post("/upload", content=b"").status_code == 400
    too_big = client.post("/upload", content=b"a==1\n" * 300_000)
    assert too_big.status_code == 413 and "1MB" in too_big.json()["detail"]


# ── 대화 스트리밍 → 확정 → 계획 관리 ─────────────────────
def test_chat_stream_then_confirm_saves_rounds(client):
    sid = client.post("/upload", content=FREEZE).json()["session_id"]
    lines = chat(client, "우분투 20, 파이썬 3.8, 2개, 11/21 22~24시, 격주", sid)

    assert lines[0] == {"type": "session", "session_id": sid}
    final = lines[-1]
    assert final["type"] == "final" and final["intent"] == "plan" and final["saved"]
    assert [[i["name"] for i in r["items"]] for r in final["plan"]["rounds"]] == [["Python", "Ubuntu"], ["django", "requests"]]
    middle = [l["type"] for l in lines[1:-1]]
    assert middle[0] == "step_start" and "tool_result" in middle and "replan" in middle and "plan_built" in middle
    seqs = [l["seq"] for l in lines[1:-1]]
    assert seqs == sorted(seqs)  # 발생 순서대로

    confirm = chat(client, "확정해줘", sid, FakeBrain(Analysis(intent="confirm", intent_reason="확정")))[-1]
    assert [(p["round_no"], p["date"], p["window_start"], p["window_end"]) for p in confirm["confirmed"]] == [
        (1, "2026-11-21", "22:00", "24:00"), (2, "2026-12-05", "22:00", "24:00")]

    plans = client.get("/plans", params={"session_id": sid}).json()
    assert [p["round_no"] for p in plans] == [1, 2]
    assert plans[1]["items"][0]["target_version"] == "5.2.19"

    again = chat(client, "확정해줘", sid)[-1]  # 같은 계획을 또 확정해도 중복 저장 안 함
    assert [p["id"] for p in again["confirmed"]] == [p["id"] for p in plans]
    assert len(client.get("/plans").json()) == 2


def test_confirm_without_plan(client):
    final = chat(client, "확정해줘", None, FakeBrain(Analysis(intent="confirm", intent_reason="확정")))[-1]
    assert final["confirmed"] is None and "도장은 처방이 나온 뒤에" in final["answer"]


def test_missing_input_stream_has_no_tool_events(client):
    lines = chat(client, "계획 짜줘", None, FakeBrain(Analysis(intent="plan", intent_reason="계획")))
    assert "tool_call" not in [l["type"] for l in lines]
    assert lines[-1]["missing"][0] == "packages"


def test_missing_api_key_shows_short_notice(client):
    app.state.brain = None
    lines = chat(client, "계획 짜줘")
    assert lines[-1]["intent"] == "error" and "API 키" in lines[-1]["answer"]


def test_error_event_on_screen_has_no_detail(client):
    lines = chat(client, "안녕", None, FakeBrain(EXAMPLE_MESSAGE, fail=["analyze"]))
    errors = [l for l in lines if l["type"] == "error"]
    assert errors and set(errors[0]) == {"type", "seq", "step", "kind"}


# ── 계획 CRUD + 겹침 ─────────────────────────────────────
def plan(date="2026-11-21", start=None, end=None, **extra):
    return {"date": date, "window_start": start, "window_end": end, "items": [{"name": "x"}], **extra}


def test_overlap_warning_but_both_saved(client):
    first = client.post("/plans", json=plan(start="22:00", end="24:00")).json()
    assert first["overlaps"] == []
    second = client.post("/plans", json=plan(start="23:00", end="23:30"))
    assert second.status_code == 201
    assert [o["id"] for o in second.json()["overlaps"]] == [first["id"]]
    touching = client.post("/plans", json=plan(start="21:00", end="22:00")).json()
    assert touching["overlaps"] == []  # 끝과 시작이 맞닿으면 겹침 아님
    all_day = client.post("/plans", json=plan()).json()  # 시각 없음 = 하루 전체
    assert len(all_day["overlaps"]) == 3
    other_day = client.post("/plans", json=plan(date="2026-11-22", start="22:00", end="24:00")).json()
    assert other_day["overlaps"] == []
    assert len(client.get("/plans").json()) == 5


def test_plan_list_is_date_ordered_and_update_delete_reflected(client):
    late = client.post("/plans", json=plan(date="2026-12-05")).json()
    early = client.post("/plans", json=plan(date="2026-11-21")).json()
    assert [p["id"] for p in client.get("/plans").json()] == [early["id"], late["id"]]

    updated = client.put(f"/plans/{late['id']}", json={"date": "2026-11-21", "window_start": "09:00"}).json()
    assert updated["date"] == "2026-11-21" and updated["window_start"] == "09:00"
    assert [o["id"] for o in updated["overlaps"]] == [early["id"]]  # 수정 응답에도 겹침
    assert client.get(f"/plans/{late['id']}").json()["updated_at"] >= late["created_at"]

    assert client.delete(f"/plans/{early['id']}").status_code == 204
    assert [p["id"] for p in client.get("/plans").json()] == [late["id"]]
    assert client.get(f"/plans/{early['id']}").status_code == 404
    assert client.delete(f"/plans/{early['id']}").json()["detail"] == "그런 계획이 없어요."


@pytest.mark.parametrize(
    "body,field",
    [({"date": "11/21"}, "date"), (plan(start="25:00"), "window_start"), (plan(start="23:00", end="22:00"), ""),
     ({**plan(), "unknown": 1}, "unknown")],
)
def test_invalid_plan_input_short_message(client, body, field):
    r = client.post("/plans", json=body)
    assert r.status_code == 422 and r.json()["detail"] == "입력 형식을 확인해 주세요."
    if field:
        assert field in r.json()["fields"]


def test_update_checks_window_after_change(client):
    p = client.post("/plans", json=plan(start="22:00", end="24:00")).json()
    r = client.put(f"/plans/{p['id']}", json={"window_start": "23:59", "window_end": "23:00"})
    assert r.status_code == 422
    r = client.put(f"/plans/{p['id']}", json={"window_start": "24:00"})
    assert r.status_code == 422 and "시작 시각" in r.json()["detail"]


# ── 실행 로그 ────────────────────────────────────────────
def test_logs_list_detail_delete_and_no_update(client):
    sid = client.post("/upload", content=FREEZE).json()["session_id"]
    chat(client, "계획 짜줘", sid)
    app.state.logger.stop()  # 남은 이벤트 저장까지 기다림
    app.state.logger.start()

    sessions = client.get("/logs").json()
    assert sessions[0]["session_id"] == sid and sessions[0]["events"] > 10
    detail = client.get(f"/logs/{sid}").json()["events"]
    assert [e["seq"] for e in detail] == list(range(1, len(detail) + 1))
    assert detail[0]["type"] == "step_start"

    assert client.put(f"/logs/{sid}", json={}).status_code == 405  # 수정 주소 없음 (F3014)
    assert client.patch(f"/logs/{sid}", json={}).status_code == 405
    assert client.delete(f"/logs/{sid}").json()["deleted"] == len(detail)
    assert client.get(f"/logs/{sid}").status_code == 404


# ── 화면 파일 (F3018) ────────────────────────────────────
def test_screen_is_served_from_same_server(client):
    """빌드한 Vue 화면(frontend/dist)이 있으면 그것을, 없으면 예전 web/을 같은 서버가 내보낸다."""
    from app.main import DIST_DIR, WEB_DIR

    page = client.get("/")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    assert "참고용 정보" in page.text and "OSV.dev" in page.text  # 출처 표기 (NF3007) — 두 화면 모두 HTML에 직접
    if WEB_DIR == DIST_DIR:
        assert '<div id="app">' in page.text and "DR.PATCH" in page.text
        assets = ["/brand/icon.svg", "/brand/mascot.svg", "/models/doctor.glb", "/models/desk.glb"]
        assets += [line.split('"')[1] for line in page.text.split() if line.startswith(("src=\"/assets/", "href=\"/assets/"))]
    else:
        for tab in ("대화", "계획 관리", "실행 로그"):
            assert tab in page.text
        assets = ["/style.css", "/js/api.js", "/js/render.js", "/js/chat.js", "/js/plans.js", "/js/logs.js", "/js/main.js"]
    for path in assets:
        assert client.get(path).status_code == 200, path
    assert client.get("/plans").headers["content-type"].startswith("application/json")  # API가 먼저
    assert client.get("/health").json() == {"ok": True}


def test_confirm_only_named_round(client):
    """시나리오 점검: '1회차 확정해줘'는 1회차만 저장."""
    sid = client.post("/upload", content=FREEZE).json()["session_id"]
    chat(client, "계획 짜줘", sid)
    brain = FakeBrain(Analysis(intent="confirm", intent_reason="확정", confirm_rounds=[1]))
    final = chat(client, "1회차 확정해줘", sid, brain)[-1]
    assert [p["round_no"] for p in final["confirmed"]] == [1]
    assert [p["round_no"] for p in client.get("/plans", params={"session_id": sid}).json()] == [1]


def test_fact_question_has_no_missing_list(client):
    final = chat(client, "Ubuntu 20.04 언제까지?", None, FakeBrain(Analysis(intent="fact", intent_reason="질문")))[-1]
    assert final["missing"] == []


def test_plan_done_undo_and_early_done(client):
    """spec v1.18 C: 날짜 전 미리 끝냄, 되돌리기."""
    created = client.post(
        "/plans",
        json={"round_no": 1, "date": "2099-12-31", "window_start": "22:00", "window_end": "24:00",
              "items": [{"name": "django", "current_version": "2.2.0", "target_version": "5.2.19"}]},
    ).json()
    assert created["status"] == "planned" and created["done_at"] is None

    done = client.put(f"/plans/{created['id']}", json={"status": "done"}).json()
    assert done["status"] == "done" and done["done_at"] is not None
    assert done["items"][0]["done_at"] is not None

    undone = client.put(f"/plans/{created['id']}", json={"status": "planned"}).json()
    assert undone["status"] == "planned" and undone["done_at"] is None
    assert undone["items"][0]["done_at"] is None


def test_plan_items_all_checked_marks_done_and_uncheck_reverts(client):
    """spec v1.18 C: 항목을 모두 체크하면 status=done, 하나라도 풀면 planned."""
    p = client.post(
        "/plans",
        json={"round_no": 1, "date": "2026-11-25",
              "items": [{"name": "a"}, {"name": "b"}]},
    ).json()
    one = client.put(
        f"/plans/{p['id']}",
        json={"items": [{"name": "a", "done_at": "2026-11-20T10:00:00+00:00"}, {"name": "b"}]},
    ).json()
    assert one["status"] == "planned"

    both = client.put(
        f"/plans/{p['id']}",
        json={"items": [{"name": "a", "done_at": "2026-11-20T10:00:00+00:00"},
                        {"name": "b", "done_at": "2026-11-20T10:05:00+00:00"}]},
    ).json()
    assert both["status"] == "done" and both["done_at"] is not None

    reverted = client.put(
        f"/plans/{p['id']}",
        json={"items": [{"name": "a", "done_at": "2026-11-20T10:00:00+00:00"}, {"name": "b", "done_at": None}]},
    ).json()
    assert reverted["status"] == "planned" and reverted["done_at"] is None


def test_done_plan_excluded_from_overlaps(client):
    """spec v1.18 C: 끝난 계획은 겹침 판단에서 빠진다."""
    p1 = client.post("/plans", json={"round_no": 1, "date": "2026-11-25", "window_start": "22:00", "window_end": "24:00"}).json()
    p2 = client.post("/plans", json={"round_no": 2, "date": "2026-11-25", "window_start": "23:00", "window_end": "24:00"}).json()
    assert len(p2["overlaps"]) == 1

    done1 = client.put(f"/plans/{p1['id']}", json={"status": "done"}).json()
    assert done1["overlaps"] == []
    p2_after = client.get(f"/plans/{p2['id']}").json()
    assert p2_after["overlaps"] == []


def test_old_db_plans_table_gets_status_and_done_at(tmp_path):
    """spec v1.18 C: 옛 DB 파일에도 plans.status·done_at 열이 자동으로 추가된다."""
    import sqlite3
    from app.db import repo

    db_file = str(tmp_path / "old.db")
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            "CREATE TABLE plans (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, "
            "round_no INTEGER NOT NULL, date TEXT NOT NULL, window_start TEXT, window_end TEXT, "
            "items_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO plans (session_id, round_no, date, items_json, created_at, updated_at) "
            "VALUES ('s1', 1, '2026-11-25', '[]', '2026-11-18', '2026-11-18')"
        )
        conn.commit()
    repo.init_db(db_file)
    with repo.connect(db_file) as conn:
        p = repo.get_plan(conn, 1)
    assert p["status"] == "planned" and p["done_at"] is None
