"""이벤트 버스(F3012) + 로깅 Agent(F3013) + "로깅 꺼도 대화 정상"."""

import json
import time

import pytest

from app.db import repo
from app.events.bus import EventBus
from app.events.logger import LoggingAgent


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test.db")
    repo.init_db(path)
    return path


def wait_until(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return False


# ── 이벤트 버스 ──────────────────────────────────────────
def test_seq_is_per_session_and_starts_at_one():
    bus = EventBus()
    sub = bus.subscribe()
    bus.publish("a", "step_start", {"step": "analyze"})
    bus.publish("b", "step_start", {"step": "analyze"})
    bus.publish("a", "step_end", {"step": "analyze"})
    got = [sub.get(0) for _ in range(3)]
    assert [(e.session_id, e.seq, e.type) for e in got] == [("a", 1, "step_start"), ("b", 1, "step_start"),
                                                            ("a", 2, "step_end")]
    assert got[0].created_at.endswith("+00:00")


def test_every_subscriber_gets_every_event_and_publisher_needs_none():
    bus = EventBus()
    assert bus.publish("s", "x", {}) is not None  # 구독자가 없어도 됨
    s1, s2 = bus.subscribe(), bus.subscribe()
    bus.publish("s", "y", {"v": 1})
    assert s1.get(0).payload == s2.get(0).payload == {"v": 1}
    s1.close()
    bus.publish("s", "z", {})
    assert s1.get(0) is None and s2.get(0).type == "z"


def test_full_queue_drops_without_blocking():
    bus = EventBus()
    sub = bus.subscribe(maxsize=2)  # 아무도 꺼내지 않는 구독자
    start = time.perf_counter()
    for i in range(1000):
        bus.publish("s", "e", {"i": i})
    assert time.perf_counter() - start < 1.0
    assert sub.dropped == 998


def test_publish_never_raises():
    bus = EventBus()
    bus.subscribe()
    assert bus.publish("s", "e", None) is not None
    assert bus.publish("s", "e", "dict가 아님") is None  # 발행 실패는 None, 예외 없음


def test_emitter_matches_graph_emit_shape():
    bus = EventBus()
    sub = bus.subscribe()
    emit = bus.emitter("sess")
    emit("tool_call", {"tool": "get_eol"})
    e = sub.get(0)
    assert (e.session_id, e.type, e.payload) == ("sess", "tool_call", {"tool": "get_eol"})


# ── 로깅 Agent ───────────────────────────────────────────
def test_logger_saves_events_per_session_in_order(db):
    bus = EventBus()
    logger = LoggingAgent(bus, db).start()
    for i in range(5):
        bus.publish("a", "step", {"i": i, "한글": "그대로"})
    bus.publish("b", "step", {"i": 99})
    logger.stop()
    assert logger.saved == 6 and logger.failed == 0

    with repo.connect(db) as conn:
        a = repo.get_events(conn, "a")
        assert [e["seq"] for e in a] == [1, 2, 3, 4, 5]
        assert a[0]["payload"] == {"i": 0, "한글": "그대로"}  # 원본 그대로
        sessions = {s["session_id"]: s["events"] for s in repo.list_log_sessions(conn)}
        assert sessions == {"a": 5, "b": 1}
        assert repo.delete_events(conn, "a") == 5
        assert repo.get_events(conn, "a") == []


def test_logger_survives_db_errors(tmp_path):
    bus = EventBus()
    bad_path = str(tmp_path / "no_tables.db")  # 표를 안 만든 DB → INSERT 실패
    logger = LoggingAgent(bus, bad_path).start()
    for i in range(3):
        bus.publish("s", "e", {"i": i})
    assert wait_until(lambda: logger.failed == 3)
    assert logger._thread.is_alive()  # 죽지 않고 계속 돈다
    logger.stop()


def test_logger_does_not_use_llm():
    import app.events.logger as logger_module

    source = open(logger_module.__file__, encoding="utf-8").read()
    assert "llm" not in source.replace("LLM을 부르지 않는다", "").lower()


def test_no_update_function_for_logs():
    assert not [name for name in dir(repo) if "update" in name and "event" in name]  # 로그 수정 불가 (F3014)


# ── 로깅이 멈춰도 대화는 정상 (tasks.md) ─────────────────
from test_agent_graph import EXAMPLE_FILE, EXAMPLE_MESSAGE, TODAY, FakeBrain  # noqa: E402

from app.agent.graph import run_agent  # noqa: E402
from app.tools import http  # noqa: E402


@pytest.fixture
def offline(monkeypatch):
    from test_agent_graph import Transport

    monkeypatch.setattr(http, "transport", Transport())


def plan_names(out):
    return [[i["name"] for i in r["items"]] for r in out["plan"]["rounds"]]


EXPECTED = [["Python", "Ubuntu"], ["django", "requests"]]


def test_chat_works_with_logger_running(offline, db):
    bus = EventBus()
    logger = LoggingAgent(bus, db).start()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=bus.emitter("s1"))
    logger.stop()
    assert plan_names(out) == EXPECTED
    with repo.connect(db) as conn:
        events = repo.get_events(conn, "s1")
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    analyze_end = next(e for e in events if e["type"] == "step_end" and e["payload"]["step"] == "analyze")
    assert analyze_end["payload"]["intent"] == "plan" and analyze_end["payload"]["reason"]  # F3012 예시
    assert {"step_start", "step_end", "tool_call", "tool_result", "llm_decision", "replan"} <= {e["type"] for e in events}
    tool_results = [e["payload"] for e in events if e["type"] == "tool_result"]
    assert all("ms" in p for p in tool_results)  # 소요 시간


def test_chat_works_without_logger(offline):
    bus = EventBus()  # 구독자 없음
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=bus.emitter("s"))
    assert plan_names(out) == EXPECTED


def test_chat_works_when_logger_db_fails(offline, tmp_path):
    bus = EventBus()
    logger = LoggingAgent(bus, str(tmp_path / "no_tables.db")).start()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=bus.emitter("s"))
    assert plan_names(out) == EXPECTED
    assert wait_until(lambda: logger.failed > 0)
    logger.stop()


def test_chat_works_when_logger_stuck_and_queue_full(offline):
    bus = EventBus()
    stuck = bus.subscribe(maxsize=1)  # 멈춘 로깅 Agent: 아무도 꺼내지 않음
    start = time.perf_counter()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=bus.emitter("s"))
    assert plan_names(out) == EXPECTED
    assert stuck.dropped > 0
    assert time.perf_counter() - start < 5  # 기다리지 않음


def test_app_starts_logger_and_stops_cleanly(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    with TestClient(app) as client:
        assert client.get("/health").json() == {"ok": True, "public": False}
        assert app.state.logger is not None
        app.state.bus.publish("boot", "test", {"ok": True})
    with repo.connect(str(tmp_path / "app.db")) as conn:
        assert json.dumps(repo.get_events(conn, "boot")[0]["payload"]) == '{"ok": true}'


def test_review_5_logs_survive_server_restart(db):
    """리뷰 #5: 재시작하면 버스 순번이 1부터 다시 시작 → 저장 순번은 DB 기준으로 이어 붙인다."""
    for run in range(2):  # 같은 세션으로 두 번 (= 서버 재시작 사이)
        bus = EventBus()
        logger = LoggingAgent(bus, db).start()
        bus.publish("s", "turn", {"run": run})
        bus.publish("s", "turn", {"run": run})
        logger.stop()
        assert logger.failed == 0
    with repo.connect(db) as conn:
        events = repo.get_events(conn, "s")
    assert [(e["seq"], e["payload"]["run"]) for e in events] == [(1, 0), (2, 0), (3, 1), (4, 1)]
