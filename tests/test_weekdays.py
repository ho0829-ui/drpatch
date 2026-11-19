"""요일 반복 규칙·캘린더 맞춤·DB 열 추가·우선순위 테스트 (네트워크 없음, spec v1.21 M)."""

from __future__ import annotations

import sqlite3
from datetime import date

from app.agent.brain import Analysis
from app.agent.graph import build_graph, merge_conditions
from app.agent.planner.calendar_fit import find_free_date
from app.agent.planner.items import Item
from app.agent.planner.rounds import split_rounds
from app.agent.render import conditions_header
from app.agent.runner import ToolRunner
from app.agent.schedule_text import fmt_schedule
from app.agent.state import Conditions, UNSUPPORTED_INTERVAL_MSG, ask_message, missing_inputs
from app.db import repo
from app.calendar.backend import LocalCalendar


def _item(name: str, sev: str = "HIGH") -> Item:
    return Item(
        kind="package",
        name=name,
        current_version="1.0.0",
        target_version="2.0.0",
        severity=sev,
        eol_date=None,
        reason="취약점",
    )


def test_split_rounds_weekdays_matching_and_non_matching_first_date():
    items = [_item(f"pkg{i}") for i in range(4)]
    # 2026-11-24는 화요일(1). 화·목([1, 3])이면 11/24(화) → 11/26(목) → 12/1(화), 4번째는 미배정
    res = split_rounds(items, capacity=1, first_date=date(2026, 11, 24), interval_days=None, weekdays=[1, 3])
    assert [r.date for r in res.rounds] == [date(2026, 11, 24), date(2026, 11, 26), date(2026, 12, 1)]
    assert [i.name for i in res.unassigned] == ["pkg3"]

    # 2026-11-23은 월요일(0). 화·목([1, 3])이면 첫 맞는 날인 11/24(화)부터 시작
    res2 = split_rounds(items[:3], capacity=1, first_date=date(2026, 11, 23), interval_days=None, weekdays=[1, 3])
    assert [r.date for r in res2.rounds] == [date(2026, 11, 24), date(2026, 11, 26), date(2026, 12, 1)]


def test_split_rounds_weekdays_biweekly_skips_alternate_week():
    items = [_item(f"pkg{i}") for i in range(3)]
    # 2026-11-23(월) 시작, 격주 화·금([1, 4], week_interval=2):
    # 1주차: 11/24(화), 11/27(금) / 2주차(11/30~12/6) 건너뜀 / 3주차: 12/8(화)
    res = split_rounds(
        items, capacity=1, first_date=date(2026, 11, 23), interval_days=None, weekdays=[1, 4], week_interval=2
    )
    assert [r.date for r in res.rounds] == [date(2026, 11, 24), date(2026, 11, 27), date(2026, 12, 8)]


def test_find_free_date_respects_allowed_weekdays():
    # 2026-11-24(화)에 종일 일정, allowed_weekdays=[1, 3](화·목) → 수요일(25)을 건너뛰고 11/26(목)
    events = [{"date": "2026-11-24", "title": "배포", "start": None, "end": None, "source": "user"}]
    free = find_free_date(date(2026, 11, 24), None, None, events, allowed_weekdays=[1, 3])
    assert free == date(2026, 11, 26)

    # 7일 안의 화·목(11/24, 11/26, 12/1)이 모두 차면 None
    busy_all = [
        {"date": "2026-11-24", "title": "일정1", "start": None, "end": None, "source": "user"},
        {"date": "2026-11-26", "title": "일정2", "start": None, "end": None, "source": "user"},
        {"date": "2026-12-01", "title": "일정3", "start": None, "end": None, "source": "user"},
    ]
    assert find_free_date(date(2026, 11, 24), None, None, busy_all, allowed_weekdays=[1, 3]) is None


def test_merge_conditions_priority_and_override():
    base = Conditions(packages=[{"name": "requests", "version": "2.19.0"}], os_name="ubuntu", os_version="22.04",
                      python_version="3.11", capacity=2, first_date=date(2026, 11, 24))

    # 1. 매주 화·목
    c1 = merge_conditions(base, Analysis(intent="plan", intent_reason="r", weekdays=[3, 1, 1], interval_days=7))
    assert c1.weekdays == [1, 3]
    assert c1.week_interval == 1
    assert c1.interval_days is None
    assert missing_inputs(c1) == []
    assert fmt_schedule(c1) == "매주 화·목"

    # 2. 요일 뒤 "3일마다" → weekdays 지움
    c2 = merge_conditions(c1, Analysis(intent="plan", intent_reason="r", interval_days=3))
    assert c2.interval_days == 3
    assert c2.weekdays is None
    assert c2.week_interval is None
    assert fmt_schedule(c2) == "3일마다"

    # 3. 격주 화·금
    c3 = merge_conditions(c2, Analysis(intent="plan", intent_reason="r", weekdays=[1, 4], interval_days=14))
    assert c3.weekdays == [1, 4]
    assert c3.week_interval == 2
    assert c3.interval_days is None
    assert fmt_schedule(c3) == "격주 화·금"

    # 4. 주 2회 (요일 없음) → missing에 interval_days 남고 요일 되묻기
    c4 = merge_conditions(base, Analysis(intent="plan", intent_reason="r", weekly_count=2))
    assert c4.weekly_count == 2
    assert c4.weekdays is None
    assert missing_inputs(c4) == ["interval_days"]
    assert fmt_schedule(c4) == "주 2회 (요일 필요)"
    assert ask_message(["interval_days"], c4) == "주 2회라면 무슨 요일로 할까요? (예: 화·금)"

    # 5. 몇째 주 미지원 안내
    assert ask_message(["interval_days"], base, interval_unsupported=True) == UNSUPPORTED_INTERVAL_MSG


def test_conditions_header_uses_fmt_schedule():
    c = Conditions(
        os_name="ubuntu", os_version="22.04", python_version="3.11",
        capacity=2, first_date=date(2026, 11, 24), weekdays=[1, 3], week_interval=1,
    )
    assert conditions_header(c) == "차트: Ubuntu 22.04 · Python 3.11 · 한 번에 2개 · 11/24(화)부터 매주 화·목"


def test_old_db_sessions_gets_weekday_columns_and_roundtrip(tmp_path):
    db_file = str(tmp_path / "old.db")
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """CREATE TABLE sessions (
                id TEXT PRIMARY KEY, packages_json TEXT NOT NULL DEFAULT '[]',
                excluded_json TEXT NOT NULL DEFAULT '[]', os TEXT, os_version TEXT,
                python_version TEXT, capacity_n INTEGER, first_date TEXT,
                window_start TEXT, window_end TEXT, interval_days INTEGER,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )"""
        )
    repo.init_db(db_file)
    with repo.connect(db_file) as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(sessions)")}
        assert {"weekdays", "weekly_count", "week_interval"} <= cols
        repo.save_session(conn, "s1", {
            "packages": [], "excluded": [], "weekdays": [1, 3], "weekly_count": None, "week_interval": 2
        })
        loaded = repo.get_session(conn, "s1")
        assert loaded["conditions"]["weekdays"] == [1, 3]
        assert loaded["conditions"]["week_interval"] == 2
        assert loaded["conditions"]["weekly_count"] is None


def test_calendar_fit_pushes_next_round_when_collision_lands_on_same_weekday(tmp_path):
    """1회차(11/24 화)가 일정 때문에 11/26(목)으로 밀리면, 원래 11/26(목)이던 2회차가 12/1(화)로 밀린다."""
    db_file = str(tmp_path / "cal.db")
    repo.init_db(db_file)
    cal = LocalCalendar(db_file)
    cal.add_event("정기 배포", "2026-11-24", "21:00", "23:00")

    class _FakeBrain:
        def analyze(self, msg, cond, today, last_turn=None):
            return Analysis(intent="plan", intent_reason="계획")
        def plan_tools(self, cond):
            from app.agent.brain import ToolPlan
            return ToolPlan(steps=["get_eol", "get_vulns", "get_package_versions"], reason="전부")
        def choose_replan(self, violations, py, msg=""):
            from app.agent.brain import ReplanChoice
            return ReplanChoice(strategy="hold", reason="보류")
        def write_response(self, summary):
            return "완료"
        def chat(self, msg):
            return "안녕"
        def answer_fact(self, msg, runner, cond=None):
            return "사실"

    class _FakeReg:
        def names(self):
            return ["get_eol", "get_vulns", "get_package_versions", "list_calendar_events"]

        def call(self, name, args):
            if name == "get_eol":
                return {"ok": True, "data": {"is_eol": False, "eol_date": "2028-04-01"}}
            if name == "get_vulns":
                return {"ok": True, "data": {
                    "count": 1 if args["version"] == "1.0.0" else 0,
                    "vulns": [{"id": "V1", "severity": "HIGH"}] if args["version"] == "1.0.0" else [],
                }}
            if name == "get_package_versions":
                return {"ok": True, "data": {
                    "versions": [{"version": "2.0.0", "requires_python": ">=3.8"}]
                }}
            if name == "list_calendar_events":
                return {"ok": True, "data": {"events": cal.list_events(args["date_from"], args["date_to"])}}
            raise KeyError(name)

    graph = build_graph(_FakeBrain(), ToolRunner(_FakeReg()))
    cond = Conditions(
        packages=[{"name": "a", "version": "1.0.0"}, {"name": "b", "version": "1.0.0"}],
        os_name="ubuntu", os_version="22.04", python_version="3.11",
        capacity=1, first_date=date(2026, 11, 24),
        window_start="22:00", window_end="24:00",
        weekdays=[1, 3], week_interval=1,
    )
    out = graph.invoke({"message": "계획", "today": date(2026, 11, 19), "conditions": cond})
    rounds = out["plan"]["rounds"]
    assert [r["date"] for r in rounds] == ["2026-11-26", "2026-12-01"]
    assert rounds[0]["moved_from"] == "2026-11-24"
    assert rounds[1]["moved_from"] == "2026-11-26"
