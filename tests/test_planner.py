"""planner 순수 함수 (spec "판단 규칙"). 네트워크 없이 저장본(PyPI)과 가짜 get_vulns·get_eol로 확인한다."""

import json
from datetime import date
from pathlib import Path

import pytest

from app.agent.planner.items import (
    FLAG_AFTER_EOL,
    FLAG_COMPAT_UNKNOWN,
    FLAG_MAJOR,
    Item,
    PackageResult,
    build_items,
    top_severity,
)
from app.agent.planner.priority import sort_items
from app.agent.planner.python_upgrade import plan_python_upgrade
from app.agent.planner.rounds import split_rounds
from app.agent.planner.versions import Candidate, is_final, is_major_change, pick_latest, python_allows
from app.tools.package_versions import parse_versions

FIX = Path(__file__).parent / "fixtures"


def pypi_versions(name: str) -> list[dict]:
    raw = json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))
    body = raw["body"] if set(raw) == {"status", "body", "text"} else raw
    return parse_versions(body)["data"]["versions"]


DJANGO = pypi_versions("pypi_django_all")
REQUESTS = pypi_versions("pypi_requests_all")

# 2026-11-18 실측 (scripts/walk_example.py, docs/planning-check.md "설계 시험")
REAL_VULN_COUNTS = {
    ("django", "4.2.30"): 8,
    ("django", "5.2.19"): 0,
    ("requests", "2.32.4"): 1,
    ("requests", "2.32.5"): 1,
    ("requests", "2.34.2"): 0,
}
REAL_PYTHON_EOL = {
    "3.10": {"eol_date": "2026-10-01", "is_eol": True},
    "3.11": {"eol_date": "2027-10-31", "is_eol": False},
    "3.12": {"eol_date": "2028-10-31", "is_eol": False},
}


class Recorder:
    """가짜 Tool 함수. 부른 기록을 남기고, 모르는 입력이면 실패시킨다 (예상 밖 호출 잡기)."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def __call__(self, *key):
        key = key if len(key) > 1 else key[0]
        self.calls.append(key)
        if key not in self.table:
            raise AssertionError(f"예상 밖 호출: {key}")
        return self.table[key]


def v(version, requires_python=None, yanked=False):
    return {"version": version, "requires_python": requires_python, "yanked": yanked}


# ── versions ─────────────────────────────────────────────
@pytest.mark.parametrize(
    "text,expected",
    [("4.2.30", True), ("2.0.post1", True), ("5.0rc1", False), ("5.0a1", False), ("5.0b2", False),
     ("5.0.dev0", False), ("not-a-version", False)],
)
def test_is_final(text, expected):
    assert is_final(text) is expected


@pytest.mark.parametrize(
    "spec,python,expected",
    [(">=3.8", "3.8", True), (">=3.10", "3.8", False), (">=2.7,!=3.0.*,!=3.1.*", "3.0", False),
     (">=2.7,!=3.0.*,!=3.1.*", "3.8", True), ("~=3.7", "3.11", True), ("<3.8", "3.8", False),
     (None, "3.8", None), ("", "3.8", None), ("아무거나", "3.8", None)],
)
def test_python_allows(spec, python, expected):
    assert python_allows(spec, python) is expected


def test_pick_latest_on_real_django():
    assert pick_latest(DJANGO, "3.8") == Candidate("4.2.30", compat_unknown=False)
    assert pick_latest(DJANGO, "3.10").version == "5.2.19"
    assert pick_latest(DJANGO, "3.12").version == "6.1.3"


def test_pick_latest_on_real_requests():
    assert pick_latest(REQUESTS, "3.8").version == "2.32.4"
    assert pick_latest(REQUESTS, "3.9").version == "2.32.5"
    assert pick_latest(REQUESTS, "3.10").version == "2.34.2"


def test_pick_latest_skips_prerelease_yanked_and_orders_versions():
    versions = [v("4.2.3", ">=3.8"), v("4.2.30", ">=3.8"), v("5.0rc1", ">=3.8"), v("4.2.31", ">=3.8", yanked=True)]
    assert pick_latest(versions, "3.8") == Candidate("4.2.30", compat_unknown=False)


def test_pick_latest_marks_unknown_compat():
    assert pick_latest([v("1.0", ">=3.6"), v("1.1", None)], "3.8") == Candidate("1.1", compat_unknown=True)


def test_pick_latest_none_when_nothing_installable():
    assert pick_latest([v("2.0", ">=3.12")], "3.8") is None


def test_major_change():
    assert is_major_change("2.2.0", "5.2.19") is True
    assert is_major_change("2.19.0", "2.34.2") is False


@pytest.mark.parametrize(
    "vulns,expected",
    [([], None), ([{"severity": "LOW"}, {"severity": "CRITICAL"}], "CRITICAL"),
     ([{"severity": None}], "UNKNOWN"), ([{"severity": None}, {"severity": "MODERATE"}], "MODERATE")],
)
def test_top_severity(vulns, expected):
    assert top_severity(vulns) == expected


# ── Python 업그레이드 재계획 ─────────────────────────────
def test_upgrade_spec_example_two_replans():
    """spec 예시 6단계: 3.9 안 됨 → 3.10 후보(종료) → 3.11 확정. 재계획 2회."""
    vulns, eol = Recorder(REAL_VULN_COUNTS), Recorder(REAL_PYTHON_EOL)
    plan = plan_python_upgrade("3.8", {"django": DJANGO, "requests": REQUESTS}, vulns, eol)
    assert plan.status == "ok"
    assert plan.python == "3.11"
    assert plan.eol_date == "2027-10-31"
    assert {n: c.version for n, c in plan.targets.items()} == {"django": "5.2.19", "requests": "2.34.2"}
    assert [a.python for a in plan.attempts] == ["3.10", "3.11"]
    assert plan.replans == 2
    assert eol.calls == ["3.10", "3.11"]
    assert len(vulns.calls) == len(set(vulns.calls))  # 같은 (패키지, 버전)은 한 번만 조회 (F3009)


def test_upgrade_hits_replan_limit():
    versions = {"pkg": [v("1.0", ">=3.8"), v("2.0", ">=3.9")]}
    vulns = Recorder({("pkg", "1.0"): 1, ("pkg", "2.0"): 0})
    eol = Recorder({f"3.{m}": {"eol_date": "2020-01-01", "is_eol": True} for m in range(9, 20)})
    plan = plan_python_upgrade("3.8", versions, vulns, eol, max_replans=3)
    assert plan.status == "hold"
    assert plan.replans == 3
    assert "상한" in plan.reason


def test_upgrade_no_safe_version_anywhere():
    versions = {"pkg": [v("1.0", ">=3.8"), v("2.0", ">=3.10")]}
    vulns = Recorder({("pkg", "1.0"): 2, ("pkg", "2.0"): 1})
    plan = plan_python_upgrade("3.8", versions, vulns, Recorder({}))
    assert plan.status == "hold"
    assert plan.replans == 0  # 후보 줄기가 없으면 get_eol을 부르지 않음


def test_upgrade_eol_unknown_is_hold_not_guess():
    versions = {"pkg": [v("1.0", ">=3.8"), v("2.0", ">=3.9")]}
    vulns = Recorder({("pkg", "1.0"): 1, ("pkg", "2.0"): 0})
    plan = plan_python_upgrade("3.8", versions, vulns, Recorder({"3.9": None}))
    assert plan.status == "hold"
    assert "확인하지 못했" in plan.reason


def test_upgrade_vuln_check_failure_is_not_treated_as_safe():
    versions = {"pkg": [v("1.0", ">=3.8"), v("2.0", ">=3.9"), v("3.0", ">=3.10")]}
    vulns = Recorder({("pkg", "1.0"): 1, ("pkg", "2.0"): None, ("pkg", "3.0"): 0})
    plan = plan_python_upgrade("3.8", versions, vulns, Recorder({"3.10": {"eol_date": "2030-01-01", "is_eol": False}}))
    assert plan.python == "3.10"  # 3.9의 2.0은 확인 못 함 → 안전하다고 보지 않고 다음 줄기


# ── 항목·우선순위·회차: spec 예시 끝까지 ─────────────────
UBUNTU_EOL = {"eol_date": "2025-05-31", "is_eol": True}
PY38_EOL = {"eol_date": "2024-10-07", "is_eol": True}


def spec_example_items():
    upgrade = plan_python_upgrade(
        "3.8", {"django": DJANGO, "requests": REQUESTS}, Recorder(REAL_VULN_COUNTS), Recorder(REAL_PYTHON_EOL)
    )
    packages = [
        PackageResult("requests", "2.19.0", "HIGH", Candidate("2.32.4", False), violation=True),
        PackageResult("django", "2.2.0", "CRITICAL", Candidate("4.2.30", False), violation=True),
    ]
    return build_items(packages, "3.8", PY38_EOL, upgrade, "Ubuntu", "20.04", UBUNTU_EOL)


def test_spec_example_items():
    result = spec_example_items()
    by_name = {i.name: i for i in result.items}
    assert set(by_name) == {"Ubuntu", "Python", "django", "requests"}  # Python은 한 항목으로 합침
    assert by_name["Python"].target_version == "3.11"
    assert by_name["Python"].severity == "HIGH"
    assert by_name["django"].target_version == "5.2.19"
    assert FLAG_MAJOR in by_name["django"].flags
    assert by_name["requests"].target_version == "2.34.2"
    assert by_name["django"].needs_python_upgrade and by_name["requests"].needs_python_upgrade
    assert by_name["Ubuntu"].target_version is None
    assert result.safe == [] and result.unchecked == [] and result.held == []


def test_spec_example_priority_and_rounds():
    """spec 예시 7·8단계: django(CRITICAL) > Python(2024-10-07) > Ubuntu(2025-05-31) > requests(종료일 없음).
    N=2, 순서 제약 먼저 → 1회차 Python·Ubuntu(11/21), 2회차 django·requests(12/5)."""
    ordered = sort_items(spec_example_items().items, today=date(2026, 11, 18))
    assert [i.name for i in ordered] == ["django", "Python", "Ubuntu", "requests"]

    result = split_rounds(ordered, capacity=2, first_date=date(2026, 11, 21), interval_days=14)
    assert [(r.round_no, r.date, [i.name for i in r.items]) for r in result.rounds] == [
        (1, date(2026, 11, 21), ["Python", "Ubuntu"]),
        (2, date(2026, 12, 5), ["django", "requests"]),
    ]
    assert result.unassigned == []
    assert all(FLAG_AFTER_EOL in i.flags for i in result.rounds[0].items)  # 이미 지원 종료
    assert all(FLAG_AFTER_EOL not in i.flags for i in result.rounds[1].items)


# ── 항목 만들기: 그 밖의 경우 ────────────────────────────
def test_safe_unchecked_and_held_are_not_items():
    packages = [
        PackageResult("safe-pkg", "1.0"),
        PackageResult("broken", "1.0", unchecked_reason="취약점 정보를 확인하지 못함"),
        PackageResult("stuck", "1.0", "HIGH", violation=True),
    ]
    result = build_items(packages, "3.12", {"eol_date": "2028-10-31", "is_eol": False}, None)
    assert result.items == []
    assert result.safe == ["safe-pkg"]
    assert result.unchecked == [{"name": "broken", "reason": "취약점 정보를 확인하지 못함"}]
    assert result.held[0]["name"] == "stuck"


def test_supported_python_and_os_are_not_items():
    packages = [PackageResult("pkg", "1.0", "LOW", Candidate("1.1", True))]
    result = build_items(packages, "3.12", {"eol_date": "2028-10-31", "is_eol": False}, None,
                         "Ubuntu", "24.04", {"eol_date": "2029-05-31", "is_eol": False})
    assert [i.name for i in result.items] == ["pkg"]
    assert FLAG_COMPAT_UNKNOWN in result.items[0].flags


def test_eol_python_without_upgrade_has_no_target():
    result = build_items([], "3.8", PY38_EOL, None)
    assert len(result.items) == 1
    assert result.items[0].target_version is None
    assert "지원 중인 버전으로 올림 필요" in result.items[0].reason


# ── 회차 나누기: 그 밖의 경우 ────────────────────────────
def item(name, severity="LOW", kind="package", needs=False, eol=None):
    return Item(kind, name, "1.0", "2.0", severity, eol, "", (), needs)


def test_overflow_goes_to_next_rounds_then_unassigned():
    items = [item(f"p{i}") for i in range(8)]
    result = split_rounds(items, capacity=2, first_date=date(2026, 11, 21), interval_days=7)
    assert [[i.name for i in r.items] for r in result.rounds] == [["p0", "p1"], ["p2", "p3"], ["p4", "p5"]]
    assert [r.date for r in result.rounds] == [date(2026, 11, 21), date(2026, 11, 28), date(2026, 12, 5)]
    assert [i.name for i in result.unassigned] == ["p6", "p7"]


def test_dependent_item_never_in_same_round_as_upgrade():
    items = [item("dep", "CRITICAL", needs=True), item("Python", "HIGH", kind="python_upgrade"), item("other")]
    result = split_rounds(items, capacity=3, first_date=date(2026, 11, 21), interval_days=7)
    assert [[i.name for i in r.items] for r in result.rounds] == [["Python", "other"], ["dep"]]


def test_dependent_item_unassigned_when_upgrade_in_last_round():
    items = [item(f"p{i}", "CRITICAL") for i in range(2)] + [
        item("Python", "HIGH", kind="python_upgrade"), item("dep", "HIGH", needs=True)]
    result = split_rounds(items, capacity=1, first_date=date(2026, 11, 21), interval_days=7)
    assert [[i.name for i in r.items] for r in result.rounds] == [["p0"], ["p1"], ["Python"]]
    assert [i.name for i in result.unassigned] == ["dep"]


def test_priority_same_severity_by_eol_then_no_eol_last():
    items = [item("no-eol", "HIGH"), item("late", "HIGH", eol=date(2027, 1, 1)),
             item("early", "HIGH", eol=date(2024, 1, 1)), item("crit", "CRITICAL"), item("unknown", "UNKNOWN")]
    ordered = sort_items(items, today=date(2026, 11, 18))
    assert [i.name for i in ordered] == ["crit", "early", "late", "no-eol", "unknown"]


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        split_rounds([], capacity=0, first_date=date(2026, 11, 21), interval_days=7)
