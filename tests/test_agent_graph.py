"""메인 Agent 그래프 (F3005~F3009, F3011). 가짜 LLM(FakeBrain) + 저장된 실제 API 응답으로 네트워크 없이 돈다."""

import json
from datetime import date
from pathlib import Path

import pytest
import requests

from app.agent.brain import Analysis, ReplanChoice, ToolPlan
from app.agent.graph import run_agent
from app.agent.state import Conditions
from app.tools import http

FIX = Path(__file__).parent / "fixtures"
TODAY = date(2026, 11, 18)


def fixture(name: str):
    data = json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))
    if isinstance(data, dict) and set(data) == {"status", "body", "text"}:
        return data["status"], data["body"]
    return 200, data


def route(method, url, body):
    """URL·요청 본문 → 저장본 이름. 저장본이 없는 호출은 테스트 실패 (예상 밖 호출 잡기)."""
    if "endoflife.date" in url:
        product, cycle = url.split("/products/")[1].split("/releases/")
        return f"eol_{product}_{cycle}"
    if "osv.dev" in url:
        return f"osv_{body['package']['name']}_{body['version']}"
    if "pypi.org" in url:
        return f"pypi_{url.split('/pypi/')[1].split('/')[0]}_all"
    raise AssertionError(url)


class Transport:
    def __init__(self, override=None):
        self.override = override or {}
        self.calls = []

    def __call__(self, method, url, json_body, timeout):
        name = route(method, url, json_body)
        self.calls.append(name)
        if name in self.override:
            value = self.override[name]
            if isinstance(value, Exception):
                raise value
            return value
        assert (FIX / f"{name}.json").exists(), f"예상 밖 호출: {name}"
        return fixture(name)


@pytest.fixture
def transport(monkeypatch):
    def install(override=None):
        t = Transport(override)
        monkeypatch.setattr(http, "transport", t)
        return t

    return install


class FakeBrain:
    """정해진 답을 내는 가짜 LLM. fail=무엇을 실패시킬지."""

    def __init__(self, analysis: Analysis, steps=None, strategy="upgrade_python", fail=()):
        self.analysis = analysis
        self.steps = steps if steps is not None else ["get_eol", "get_vulns", "get_package_versions"]
        self.strategy = strategy
        self.fail = set(fail)
        self.seen_summary = None

    def _maybe_fail(self, name):
        if name in self.fail:
            raise RuntimeError(f"fake {name} failure")

    def analyze(self, message, conditions, today, last_turn=None):
        self._maybe_fail("analyze")
        self.seen_last_turn = last_turn
        return self.analysis

    def plan_tools(self, conditions):
        self._maybe_fail("plan_tools")
        return ToolPlan(steps=self.steps, reason="지원 종료 → 취약점 → 설치 가능 버전 순")

    def choose_replan(self, violations, python_version, message=""):
        self._maybe_fail("choose_replan")
        return ReplanChoice(strategy=self.strategy, reason="안전한 버전이 Python을 올려야만 있음")

    def answer_fact(self, message, runner, conditions=None):
        self._maybe_fail("answer_fact")
        r = runner.call("get_eol", {"product": "ubuntu", "cycle": "20.04"})
        return f"일반 지원은 {r['data']['eol_date']}에 끝났어요."

    def write_response(self, summary):
        self._maybe_fail("write_response")
        self.seen_summary = summary
        return "회차별 계획을 만들었어요."

    def chat(self, message):
        self._maybe_fail("chat")
        return "패치 계획을 도와드려요."


EXAMPLE_FILE = Conditions(
    packages=[{"name": "requests", "version": "2.19.0"}, {"name": "django", "version": "2.2.0"}],
    excluded=[{"line_no": 3, "text": "-e git+https://github.com/me/tool.git#egg=tool", "reason": "PyPI 출처 아님"}],
)
EXAMPLE_MESSAGE = Analysis(
    intent="plan", intent_reason="계획 요청", os_name="Ubuntu", os_version="20", python_version="3.8",
    capacity=2, first_date="2026-11-21", window_start="22:00", window_end="24:00", interval_days=14,
)


def collect():
    events = []
    return events, lambda t, p: events.append((t, p))


# ── spec 예시를 그래프로 ─────────────────────────────────
def test_spec_example_through_graph(transport):
    t = transport()
    events, emit = collect()
    out = run_agent("우분투 20, 파이썬 3.8, 2개까지, 11/21 22~24시, 격주", EXAMPLE_FILE,
                    FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=emit)

    assert out["intent"] == "plan"
    assert out["conditions"].os_version == "20.04"  # '우분투 20' → 20.04
    plan = out["plan"]
    assert [(r["round_no"], r["date"], [i["name"] for i in r["items"]]) for r in plan["rounds"]] == [
        (1, "2026-11-21", ["Python", "Ubuntu"]),
        (2, "2026-12-05", ["django", "requests"]),
    ]
    targets = {i["name"]: i["target_version"] for r in plan["rounds"] for i in r["items"]}
    assert targets == {"Python": "3.11", "Ubuntu": None, "django": "5.2.19", "requests": "2.34.2"}
    assert plan["python_upgrade"]["python"] == "3.11" and plan["python_upgrade"]["replans"] == 2
    assert plan["window"] == {"start": "22:00", "end": "24:00"}
    assert plan["excluded"][0]["reason"] == "PyPI 출처 아님"
    assert out["answer"].endswith("회차별 계획을 만들었어요.")
    assert out["answer"].startswith("차트: Ubuntu 20.04 · Python 3.8 · 한 번에 2개 · 11/21(토)부터 격주 (22–24시)")

    # 같은 호출은 한 번만 (F3009 재사용): 저장본 호출 목록에 중복 없음
    assert len(t.calls) == len(set(t.calls)) == out["tool_calls"]

    types = [e[0] for e in events]
    decisions = [p["decision"] for e, p in events if e == "llm_decision"]
    assert decisions == ["intent", "tool_plan", "replan_strategy"]
    assert [p["python"] for e, p in events if e == "replan"] == ["3.10", "3.11"]
    assert types.count("tool_call") == types.count("tool_result") == out["tool_calls"]
    steps = [p["step"] for e, p in events if e == "step_start"]
    assert steps == ["analyze", "plan_tools", "call_tools", "judge", "replan", "build", "respond"]


# ── 되묻기 ───────────────────────────────────────────────
def test_missing_inputs_asks_only_missing_and_calls_no_tool(transport):
    t = transport()
    analysis = Analysis(intent="plan", intent_reason="계획 요청", python_version="3.8")
    out = run_agent("계획 짜줘, 파이썬 3.8", Conditions(), FakeBrain(analysis), today=TODAY)
    assert out["missing"] == ["packages", "os", "capacity", "first_date", "interval_days"]
    assert "requirements.txt" in out["answer"] and "OS와 버전" in out["answer"]
    assert "Python 버전" not in out["answer"]  # 이미 받은 건 묻지 않음
    assert t.calls == [] and out["tool_calls"] == 0


# ── Memory: 바뀐 조건만 갱신 ─────────────────────────────
def test_follow_up_updates_only_changed_conditions(transport):
    transport()
    first = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    change = Analysis(intent="plan", intent_reason="개수만 바꿈", capacity=4)
    second = run_agent("이번엔 4개까지", first["conditions"], FakeBrain(change), today=TODAY)
    c = second["conditions"]
    assert (c.capacity, c.python_version, c.os_version, c.interval_days) == (4, "3.8", "20.04", 14)
    assert [len(r["items"]) for r in second["plan"]["rounds"]] == [2, 2]  # 순서 제약 때문에 여전히 두 회차


# ── Tool 실패 ────────────────────────────────────────────
def test_one_tool_failure_marks_only_that_package(transport):
    transport({"osv_requests_2.19.0": requests.Timeout()})
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    plan = out["plan"]
    assert plan["unchecked"] == [{"name": "requests", "reason": "취약점 정보를 확인하지 못함"}]
    names = [i["name"] for r in plan["rounds"] for i in r["items"]]
    assert "django" in names and "requests" not in names


def test_eol_failure_is_shown_as_unchecked_not_invented(transport):
    transport({"eol_ubuntu_20.04": (503, None)})
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    assert out["plan"]["eol_checks"]["os"] == "확인 못 함"
    assert "Ubuntu" not in [i["name"] for r in out["plan"]["rounds"] for i in r["items"]]


# ── LLM 계획·판단 ────────────────────────────────────────
def test_code_adds_tools_the_llm_left_out(transport):
    transport()
    events, emit = collect()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE, steps=["get_vulns"]), today=TODAY, emit=emit)
    assert out["tool_plan"] == ["get_vulns", "get_eol", "get_package_versions"]
    plan_event = next(p for e, p in events if e == "llm_decision" and p["decision"] == "tool_plan")
    assert plan_event["added_by_code"] == ["get_eol", "get_package_versions"]


def test_replan_hold_strategy_holds_packages(transport):
    transport()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE, strategy="hold"), today=TODAY)
    plan = out["plan"]
    assert {h["name"] for h in plan["held"]} == {"django", "requests"}
    assert [i["name"] for r in plan["rounds"] for i in r["items"]] == ["Python", "Ubuntu"]
    assert all(i["target_version"] is None for r in plan["rounds"] for i in r["items"])


# ── LLM 실패해도 서비스는 계속 ───────────────────────────
@pytest.mark.parametrize("fail", ["plan_tools", "choose_replan"])
def test_llm_failure_mid_flow_uses_defaults(transport, fail):
    transport()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE, fail=[fail]), today=TODAY)
    assert out["plan"]["python_upgrade"]["python"] == "3.11"


def test_response_failure_falls_back_to_code_text(transport):
    transport()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE, fail=["write_response"]), today=TODAY)
    assert "1회차 (2026-11-21)" in out["answer"]
    assert "django 2.2.0 → 5.2.19" in out["answer"]


def test_analyze_failure_ends_with_notice(transport):
    t = transport()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE, fail=["analyze"]), today=TODAY)
    assert out["intent"] == "error"
    assert "잠시 후" in out["answer"]
    assert t.calls == []


# ── 사실 조회·그 밖 ──────────────────────────────────────
def test_fact_question_uses_tool_result(transport):
    t = transport()
    analysis = Analysis(intent="fact", intent_reason="지원 기간 질문")
    out = run_agent("Ubuntu 20.04 언제까지 지원돼?", Conditions(), FakeBrain(analysis), today=TODAY)
    assert out["answer"] == "일반 지원은 2025-05-31에 끝났어요."
    assert t.calls == ["eol_ubuntu_20.04"]


def test_confirm_does_not_call_tools(transport):
    t = transport()
    out = run_agent("확정해줘", EXAMPLE_FILE, FakeBrain(Analysis(intent="confirm", intent_reason="확정")), today=TODAY)
    assert out["intent"] == "confirm" and t.calls == []


# ── 재계획 상한 (그래프 단위) ────────────────────────────
def _eol(cycle):
    return 200, {"result": {"eolFrom": "2026-01-01", "isEol": True, "isLts": False, "label": cycle,
                            "latest": {"name": f"{cycle}.0"}}}


def test_replan_stops_at_limit_and_holds_with_reason(transport):
    """3.10·3.11·3.12가 모두 지원 종료라고 가정 → 재계획 3회에서 멈추고 보류(사유)."""
    transport({"eol_python_3.10": _eol("3.10"), "eol_python_3.11": _eol("3.11"),
               "eol_python_3.12": _eol("3.12"), "osv_django_6.1.3": (200, {})})
    events, emit = collect()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=emit)
    plan = out["plan"]
    assert plan["python_upgrade"]["status"] == "hold"
    assert plan["python_upgrade"]["replans"] == 3
    assert "상한" in plan["python_upgrade"]["reason"]
    assert {h["name"] for h in plan["held"]} == {"django", "requests"}
    replans = [p for e, p in events if e == "replan"]
    assert [p.get("python") for p in replans] == ["3.10", "3.11", "3.12", None]
    assert replans[-1]["result"] == "hold"


# ── 2일차 리뷰 반영 (그래프 단위) ─────────────────────────
def test_review_4_no_installable_version_goes_to_replan(transport):
    """리뷰 #4: 지금 Python에 설치 가능한 버전이 없으면 보류가 아니라 재계획."""
    body = {"info": {"version": "2.0", "project_url": "https://pypi.org/project/pkg/"},
            "releases": {"1.0": [{"yanked": True, "requires_python": ">=3.8"}],
                         "2.0": [{"yanked": False, "requires_python": ">=3.11"}]}}
    transport({"pypi_pkg_all": (200, body), "osv_pkg_1.0": (200, {"vulns": [{"id": "X", "database_specific": {"severity": "HIGH"}}]}),
               "osv_pkg_2.0": (200, {})})
    file = Conditions(packages=[{"name": "pkg", "version": "1.0"}])
    out = run_agent("…", file, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    targets = {i["name"]: i["target_version"] for r in out["plan"]["rounds"] for i in r["items"]}
    assert targets["pkg"] == "2.0" and targets["Python"] == "3.11"


def test_review_12_lower_version_is_not_a_target(transport):
    """리뷰 #12: 지금 Python의 최신이 현재보다 낮으면 다운그레이드하지 않고 재계획."""
    body = {"info": {"version": "3.0", "project_url": None},
            "releases": {"1.0": [{"requires_python": ">=3.8"}], "2.0": [{"requires_python": ">=3.10"}],
                         "3.0": [{"requires_python": ">=3.11"}]}}
    transport({"pypi_pkg_all": (200, body),
               "osv_pkg_2.0": (200, {"vulns": [{"id": "X", "database_specific": {"severity": "LOW"}}]}),
               "osv_pkg_3.0": (200, {})})
    file = Conditions(packages=[{"name": "pkg", "version": "2.0"}])  # 3.8 서버에 2.0이 깔려 있음
    out = run_agent("…", file, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    targets = {i["name"]: i["target_version"] for r in out["plan"]["rounds"] for i in r["items"]}
    assert targets["pkg"] == "3.0"  # 1.0으로 내려가지 않음


def test_review_6_all_tools_down_stops_with_notice(transport):
    t = transport({name: requests.ConnectionError() for name in
                   ["eol_ubuntu_20.04", "eol_python_3.8", "osv_requests_2.19.0", "osv_django_2.2.0"]})
    events, emit = collect()
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=emit)
    assert "못 가져왔네요" in out["answer"] and out["plan"] is None
    assert not any(e == "step_start" and p["step"] == "judge" for e, p in events)
    assert any(e == "error" and p["kind"] == "all_tools_failed" for e, p in events)
    assert "pypi_requests_all" not in t.calls  # 취약점 조회가 다 실패 → 버전 목록은 부르지 않음


def test_review_8_logs_explain_versions_and_order(transport):
    transport()
    events, emit = collect()
    run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY, emit=emit)
    judgment = next(p for e, p in events if e == "judgment")
    assert {p["name"]: p["status"] for p in judgment["packages"]} == {"requests": "violation", "django": "violation"}
    built = next(p for e, p in events if e == "plan_built")
    assert [o["name"] for o in built["order"]] == ["django", "Python", "Ubuntu", "requests"]
    assert [r["items"] for r in built["rounds"]] == [["Python", "Ubuntu"], ["django", "requests"]]
    assert "업그레이드 다음 회차" in built["rule"]


def test_zero_vulns_is_safe_only_if_package_and_version_exist_on_pypi(transport):
    """상호 점검(2026-11-20): PyPI에 없는 패키지가 OSV 0건이라 "안전"으로 나오던 것.

    OSV는 모르는 패키지도 0건으로 답한다 → 0건이어도 PyPI에서 패키지·버전이 있는지 확인한 뒤에만 안전.
    """
    t = transport()
    extra = [{"name": "requests", "version": "2.34.2"},         # 있는 패키지·버전, 0건 → 안전
             {"name": "ghost-pkg-xyz", "version": "1.0"},       # PyPI에 없는 패키지
             {"name": "django", "version": "9.9.9"}]            # 패키지는 있지만 없는 버전
    file = Conditions(packages=[p for p in EXAMPLE_FILE.packages if p["name"] not in ("requests", "django")] + extra)
    t.override["osv_ghost-pkg-xyz_1.0"] = (200, {})
    t.override["osv_django_9.9.9"] = (200, {})
    t.override["pypi_ghost-pkg-xyz_all"] = fixture("pypi_no_package")
    out = run_agent("…", file, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    assert "pypi_ghost-pkg-xyz_all" in t.calls  # 0건이어도 존재 확인
    assert out["plan"]["safe"] == ["requests"]
    assert {(u["name"], u["reason"]) for u in out["plan"]["unchecked"]} >= {
        ("ghost-pkg-xyz", "PyPI에 없는 패키지"), ("django", "PyPI에 없는 버전")}


def test_review_9_user_message_reaches_replan_choice(transport):
    transport()

    class Brain(FakeBrain):
        def choose_replan(self, violations, python_version, message=""):
            self.replan_message = message
            return super().choose_replan(violations, python_version, message)

    brain = Brain(EXAMPLE_MESSAGE)
    run_agent("파이썬은 못 올려", EXAMPLE_FILE, brain, today=TODAY)
    assert brain.replan_message == "파이썬은 못 올려"


def test_review_11_os_change_clears_old_version(transport):
    transport()
    first = run_agent("…", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    out = run_agent("데비안으로 바꿀게", first["conditions"],
                    FakeBrain(Analysis(intent="plan", intent_reason="OS 변경", os_name="debian")), today=TODAY)
    assert out["conditions"].os_name == "debian" and out["conditions"].os_version is None
    assert out["missing"] == ["os"]


def test_review_11_python2_is_accepted(transport):
    transport()
    out = run_agent("…", Conditions(), FakeBrain(Analysis(intent="plan", intent_reason="x", python_version="2.7")),
                    today=TODAY)
    assert out["conditions"].python_version == "2.7" and "python_version" not in out["missing"]


def test_review_3_fact_tool_result_is_computed_by_code(transport):
    """리뷰 #3: 사실 조회에서 LLM에게 버전 목록 원본을 주지 않고, 코드가 계산한 값을 준다."""
    from app.agent.fact_tools import run_fact_tool
    from app.agent.runner import ToolRunner
    from app.tools.default import build_registry

    transport()
    runner = ToolRunner(build_registry())
    result = run_fact_tool(runner, "get_package_versions", {"name": "django"}, "3.8")
    assert "versions" not in result
    assert result["installable_latest"] == "4.2.30" and result["vulns_in_installable_latest"] == 8
    unknown = run_fact_tool(runner, "get_package_versions", {"name": "django"}, None)
    assert "installable_latest" not in unknown and "Python 버전" in unknown["note"]
    vulns = run_fact_tool(runner, "get_vulns", {"name": "django", "version": "2.2.0"}, "3.8")
    assert vulns["count"] == 43 and vulns["top_severity"] == "CRITICAL" and len(vulns["vulns"]) == 10


# ── spec v1.14: 일정만 빠지면 우선순위 먼저 ───────────────
def test_priority_first_when_only_schedule_missing(transport):
    t = transport()
    analysis = Analysis(intent="plan", intent_reason="뭐부터", os_name="ubuntu", os_version="20.04", python_version="3.8")
    out = run_agent("Ubuntu 20.04, Python 3.8인데 지금 뭐부터 해야 돼?", EXAMPLE_FILE, FakeBrain(analysis), today=TODAY)
    assert out["missing"] == ["capacity", "first_date", "interval_days"]
    assert t.calls  # Tool은 불렀다
    plan = out["plan"]
    assert plan["rounds"] == [] and plan["schedule_missing"] == ["capacity", "first_date", "interval_days"]
    assert [i["name"] for i in plan["priority"]] == ["Python", "Ubuntu", "django", "requests"]  # 업그레이드가 먼저
    assert "회차 일정을 잡으려면" in out["answer"] and "OS와 버전" not in out["answer"]


def test_priority_fallback_text_without_llm(transport):
    transport()
    analysis = Analysis(intent="plan", intent_reason="뭐부터", os_name="ubuntu", os_version="20.04", python_version="3.8")
    out = run_agent("…", EXAMPLE_FILE, FakeBrain(analysis, fail=["write_response"]), today=TODAY)
    assert "위험한 순서" in out["answer"] and "django 2.2.0 → 5.2.19" in out["answer"]


def test_v117_macos_followup_asks_only_version():
    """spec v1.17 재현: OS 물음 → '로컬 맥북' → 두 번째는 macOS 버전만 묻고 같은 문장이 반복되지 않는다."""
    pkgs = [{"name": "requests", "version": "2.19.0"}]
    cond = Conditions(packages=pkgs)

    brain1 = FakeBrain(
        analysis=Analysis(
            intent="plan", intent_reason="계획",
            python_version="3.11", capacity=5, first_date="2026-11-25", interval_days=7,
        )
    )
    out1 = run_agent("Python 3.11이고 한 번에 5개까지, 11/25부터 매주", cond, brain1, today=TODAY)
    assert out1["missing"] == ["os"]
    assert out1["tool_calls"] == 0
    assert "Ubuntu" in out1["answer"] and "macOS" in out1["answer"] and "Windows" in out1["answer"]

    brain2 = FakeBrain(
        analysis=Analysis(intent="plan", intent_reason="OS 응답", os_name="맥북", os_version=None)
    )
    out2 = run_agent("로컬 맥북을 백엔드 서버로 쓰고 있어요", out1["conditions"], brain2, today=TODAY)
    assert out2["conditions"].os_name == "macos"
    assert out2["conditions"].os_version is None
    assert out2["missing"] == ["os"]
    assert out2["tool_calls"] == 0
    assert "맥이시군요" in out2["answer"] and "macOS 15" in out2["answer"]
    assert out2["answer"] != out1["answer"]


def test_v117_os_normalization_and_windows_feature_update():
    """spec v1.17: OS 이름·코드네임·Windows cycle 정규화, 주 버전만 있으면 되묻기."""
    from app.agent.state import ask_message, normalize_os_name, normalize_os_version

    assert normalize_os_name("맥북") == "macos"
    assert normalize_os_name("OS X") == "macos"
    assert normalize_os_name("윈도우") == "windows"
    assert normalize_os_version("macos", "세쿼이아") == "15"
    assert normalize_os_version("macos", "타호") == "26"
    assert normalize_os_version("macos", "15.3.1") == "15"
    assert normalize_os_version("macos", "모르는코드네임") is None
    assert normalize_os_version("windows", "11 24H2") == "11-24h2-w"
    assert normalize_os_version("windows", "11 24H2 Enterprise") == "11-24h2-e"
    assert normalize_os_version("windows", "11") is None  # 기능 업데이트 없음 → 되묻기

    win_msg = ask_message(["os"], Conditions(os_name="windows"))
    assert "Windows" in win_msg and "24H2" in win_msg


def test_v117_maintained_macos_not_added_and_null_eol_sorts_safely():
    """spec v1.17: 지원 중(eol_date=None, is_eol=False) OS는 계획 항목이 아니며, eol_date=None 정렬도 안전."""
    from app.agent.planner.items import Item, build_items
    from app.agent.planner.priority import sort_items

    res = build_items(
        [], "3.11", {"eol_date": "2027-10-31", "is_eol": False}, None,
        "macOS", "15", {"eol_date": None, "is_eol": False, "note": "지원 중 (종료일 미발표)"},
    )
    assert res.items == []
    ordered = sort_items([
        Item("package", "a", "1.0", "2.0", "HIGH", None, "이유"),
        Item("package", "b", "1.0", "2.0", "HIGH", date(2026, 12, 1), "이유"),
    ], TODAY)
    assert [i.name for i in ordered] == ["b", "a"]


def test_v118_conditions_header_shape_and_respond_prefix(transport):
    """spec v1.18 B: 계획 답 맨 앞에 코드가 만든 조건 한 줄이 붙는다."""
    from app.agent.render import conditions_header

    c = Conditions(
        os_name="ubuntu", os_version="22.04", python_version="3.11",
        capacity=5, first_date=date(2026, 11, 25), interval_days=7,
        window_start="22:00", window_end="24:00",
    )
    assert conditions_header(c) == "차트: Ubuntu 22.04 · Python 3.11 · 한 번에 5개 · 11/25(수)부터 매주 (22–24시)"

    c_win = Conditions(os_name="windows", os_version="11-24h2-w", python_version="3.12")
    assert conditions_header(c_win) == "차트: Windows 11 24H2 (Home/Pro 기준) · Python 3.12"

    transport()
    out = run_agent("계획 짜줘", EXAMPLE_FILE, FakeBrain(EXAMPLE_MESSAGE), today=TODAY)
    assert out["answer"].startswith("차트: Ubuntu 20.04 · Python 3.8 · 한 번에 2개 · 11/21(토)부터 격주 (22–24시)\n\n")


def test_v117_os_item_uses_display_name_and_os_specific_hint():
    """spec v1.17: 지원 끝난 Windows는 조회 이름(11-24h2-w)·'LTS' 대신 보이는 이름과 OS에 맞는 안내."""
    from app.agent.os_display import os_display_name, os_display_version, upgrade_hint
    from app.agent.planner.items import build_items

    assert os_display_name("macos") == "macOS"
    assert os_display_version("windows", "11-24h2-w") == "11 24H2 (Home/Pro 기준)"
    assert os_display_version("windows", "11-24h2-e") == "11 24H2 (Enterprise/Education 기준)"
    assert os_display_version("ubuntu", "20.04") == "20.04"

    res = build_items(
        [], "3.11", {"eol_date": "2027-10-31", "is_eol": False}, None,
        os_display_name("windows"), os_display_version("windows", "11-24h2-w"),
        {"eol_date": "2026-10-13", "is_eol": True}, upgrade_hint("windows"),
    )
    item = res.items[0]
    assert (item.name, item.current_version) == ("Windows", "11 24H2 (Home/Pro 기준)")
    assert "기능 업데이트" in item.reason and "LTS" not in item.reason
