"""대화 맥락 Memory (F3010): 세션 조건·직전 대화·직전 계획을 SQLite에 저장하고 다음 턴에 쓴다."""

import pytest
from test_agent_graph import EXAMPLE_FILE, EXAMPLE_MESSAGE, TODAY, FakeBrain, Transport

from app.agent.brain import Analysis
from app.agent.session import chat_turn, load_session, save_upload
from app.db import repo
from app.events.bus import EventBus
from app.tools import http


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "memory.db")
    repo.init_db(path)
    return path


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(http, "transport", Transport())


def upload_example(db, session_id="s1"):
    assert save_upload(session_id, EXAMPLE_FILE.packages, EXAMPLE_FILE.excluded, db)


def test_upload_then_first_turn_creates_session_and_saves_conditions(db):
    upload_example(db)
    out = chat_turn("s1", "우분투 20, 파이썬 3.8, 2개, 11/21 22~24시, 격주", FakeBrain(EXAMPLE_MESSAGE),
                    db_path=db, today=TODAY)
    assert out["session_id"] == "s1" and out["saved"]
    session = load_session("s1", db)
    c = session["conditions"]
    assert (c.os_name, c.os_version, c.python_version, c.capacity, c.interval_days) == ("ubuntu", "20.04", "3.8", 2, 14)
    assert c.first_date.isoformat() == "2026-11-21" and (c.window_start, c.window_end) == ("22:00", "24:00")
    assert [p["name"] for p in c.packages] == ["requests", "django"]
    assert session["last_turn"]["message"].startswith("우분투 20")
    assert session["last_plan"]["rounds"][0]["items"][0]["name"] == "Python"


def test_new_session_id_when_none_given(db):
    out = chat_turn(None, "안녕", FakeBrain(Analysis(intent="other", intent_reason="인사")), db_path=db, today=TODAY)
    assert len(out["session_id"]) == 32
    assert load_session(out["session_id"], db)["last_turn"]["answer"] == "패치 계획을 도와드려요."


def test_second_turn_changes_only_what_changed(db):
    """F3010: '이번엔 4개까지' → N만 바뀌고 나머지 조건·패키지는 그대로."""
    upload_example(db)
    chat_turn("s1", "첫 요청", FakeBrain(EXAMPLE_MESSAGE), db_path=db, today=TODAY)
    brain = FakeBrain(Analysis(intent="plan", intent_reason="개수 변경", capacity=4))
    out = chat_turn("s1", "이번엔 4개까지", brain, db_path=db, today=TODAY)

    c = load_session("s1", db)["conditions"]
    assert (c.capacity, c.python_version, c.os_version, c.interval_days) == (4, "3.8", "20.04", 14)
    assert c.first_date.isoformat() == "2026-11-21" and len(c.packages) == 2
    assert brain.seen_last_turn == {"message": "첫 요청", "answer": "회차별 계획을 만들었어요."}  # 직전 대화 전달
    assert out["plan"] is not None


def test_confirm_keeps_last_plan_even_after_fact_question(db):
    upload_example(db)
    planned = chat_turn("s1", "계획 짜줘", FakeBrain(EXAMPLE_MESSAGE), db_path=db, today=TODAY)
    chat_turn("s1", "Ubuntu 20.04 언제까지?", FakeBrain(Analysis(intent="fact", intent_reason="질문")),
              db_path=db, today=TODAY)
    confirm = chat_turn("s1", "확정해줘", FakeBrain(Analysis(intent="confirm", intent_reason="확정")),
                        db_path=db, today=TODAY)
    assert confirm["intent"] == "confirm"
    assert confirm["last_plan"] == planned["plan"]


def test_memory_survives_new_connection(db):
    """서버 재시작 = 새 연결. 저장한 조건이 그대로 읽힌다."""
    upload_example(db)
    chat_turn("s1", "…", FakeBrain(EXAMPLE_MESSAGE), db_path=db, today=TODAY)
    with repo.connect(db) as fresh:
        row = repo.get_session(fresh, "s1")
    assert row["conditions"]["capacity"] == 2


def test_db_failure_still_answers(tmp_path):
    bad = str(tmp_path / "no_tables.db")  # 표가 없는 DB → 읽기·쓰기 실패
    bus = EventBus()
    sub = bus.subscribe()
    out = chat_turn("s1", "안녕", FakeBrain(Analysis(intent="other", intent_reason="인사")),
                    bus=bus, db_path=bad, today=TODAY)
    assert out["answer"] == "패치 계획을 도와드려요."
    assert out["saved"] is False
    events = []
    while (e := sub.get(0)) is not None:
        events.append(e)
    assert any(e.type == "error" and e.payload["step"] == "save_session" for e in events)


def test_events_carry_session_id(db):
    bus = EventBus()
    sub = bus.subscribe()
    chat_turn("abc", "안녕", FakeBrain(Analysis(intent="other", intent_reason="인사")), bus=bus, db_path=db, today=TODAY)
    first = sub.get(0)
    assert first.session_id == "abc" and first.seq == 1


def test_old_db_file_gets_new_columns(tmp_path):
    """예전 스키마(직전 대화 칸 없음)로 만든 DB도 init_db가 칸을 붙인다."""
    import sqlite3

    path = str(tmp_path / "old.db")
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, packages_json TEXT NOT NULL DEFAULT '[]', "
                     "excluded_json TEXT NOT NULL DEFAULT '[]', os TEXT, os_version TEXT, python_version TEXT, "
                     "capacity_n INTEGER, first_date TEXT, window_start TEXT, window_end TEXT, interval_days INTEGER, "
                     "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
    repo.init_db(path)
    with repo.connect(path) as conn:
        repo.save_session(conn, "x", {"packages": []}, last_message="m", last_answer="a", last_plan={"rounds": []})
        assert repo.get_session(conn, "x")["last_plan"] == {"rounds": []}
