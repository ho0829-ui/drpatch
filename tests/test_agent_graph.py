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

    def choose_replan(self, violations, python_version):
        self._maybe_fail("choose_replan")
        return ReplanChoice(strategy=self.strategy, reason="안전한 버전이 Python을 올려야만 있음")

    def answer_fact(self, message, runner):
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
    assert out["answer"] == "회차별 계획을 만들었어요."

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
