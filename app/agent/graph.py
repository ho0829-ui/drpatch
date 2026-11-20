"""메인 Agent 그래프 (LangGraph). docs/architecture.md 3절.

analyze ─┬─ 계획인데 입력 빠짐 → ask
         ├─ 계획 → plan_tools → call_tools → judge ─┬─ 위반 → replan → build → respond
         │                                         └─────────────→ build → respond
         ├─ 사실 조회 → fact
         └─ 확정 / 그 밖 → other
노드마다 step_start/step_end, LLM 판단은 llm_decision, 재계획은 replan 이벤트를 발행한다 (F3012).
"""

from collections.abc import Callable
from datetime import date, timedelta

from langgraph.graph import END, START, StateGraph

from app.agent.brain import AgentBrain
from app.agent.os_display import os_display_name, os_display_version, upgrade_hint
from app.agent.planner.items import PackageResult, build_items, top_severity
from app.agent.planner.priority import sort_items
from app.agent.planner.python_upgrade import UpgradePlan, candidate_versions, plan_python_upgrade
from app.agent.planner.calendar_fit import SEARCH_DAYS, conflicts_on, find_free_date
from app.agent.planner.rounds import RoundsResult, move_round, next_matching_date, split_rounds
from app.agent.planner.versions import is_newer, parse_version, pick_latest
from app.agent.render import conditions_header, fallback_text, plan_dict
from app.agent.runner import Emit, ToolRunner, no_emit
from app.agent.state import (
    AgentState,
    Conditions,
    ask_message,
    SCHEDULE_KEYS,
    missing_inputs,
    normalize_os_name,
    normalize_os_version,
    normalize_weekdays,
    schedule_ask_message,
    tool_inputs_missing,
    normalize_python,
)
from app.tools.base import PACKAGE_NOT_FOUND, TIMEOUT, UPSTREAM_ERROR
from app.tools.default import build_registry

PLAN_TOOLS = ["get_eol", "get_vulns", "get_package_versions"]  # 계획 수립에 셋 다 필요
LLM_FAILED = "LLM 응답을 받지 못해 기본값을 썼어요"
TOOLS_DOWN = "허허, 외부 진료 기록을 못 가져왔네요. 네트워크를 확인하고 잠시 후 다시 해 보시죠."


def _vulns_ok(result: dict | None) -> bool:
    return bool(result and result["ok"])


def _existence_problem(name: str, current: str, versions: dict | None) -> str | None:
    """취약점 0건인 패키지가 PyPI에 정말 있는지. 없거나 확인 못 하면 "안전"이라 하지 않는다 (지어내지 않음).

    OSV는 모르는 패키지도 0건으로 답하므로 0건만으로는 안전을 판단할 수 없다.
    """
    if not versions or not versions["ok"]:
        if versions and versions["error"]["code"] == PACKAGE_NOT_FOUND:
            return "PyPI에 없는 패키지"
        return "패키지 정보를 확인하지 못함"
    current_v = parse_version(current)
    known = {parse_version(v["version"]) for v in versions["data"]["versions"]}
    if current_v is None or current_v not in known:
        return "PyPI에 없는 버전"
    return None


def _status(r: PackageResult) -> str:
    if r.unchecked_reason:
        return "unchecked"
    if r.severity is None:
        return "safe"
    return "violation" if r.violation else "fix_on_current_python"

# 단계 종료 이벤트에 싣는 요약 (F3012: 의도 분석 종료에는 의도와 이유)
STEP_SUMMARY: dict[str, Callable[[dict], dict]] = {
    "analyze": lambda o: {"intent": o.get("intent"), "reason": o.get("intent_reason"), "missing": o.get("missing")},
    "ask": lambda o: {"asked": True},
    "plan_tools": lambda o: {"tool_plan": o.get("tool_plan"), "reason": o.get("tool_plan_reason")},
    "call_tools": lambda o: {"eol": [k for k in ("eol_os", "eol_python") if k in o.get("results", {})],
                             "packages": len(o.get("results", {}).get("vulns", {}))},
    "judge": lambda o: {"violations": len(o.get("violations", []))},
    "replan": lambda o: {"strategy": o.get("replan_strategy"),
                         "result": getattr(o.get("upgrade"), "status", None),
                         "python": getattr(o.get("upgrade"), "python", None)},
    "build": lambda o: {"rounds": len(o.get("plan", {}).get("rounds", []))},
}


def merge_conditions(prev: Conditions, analysis) -> Conditions:
    """이번 메시지에서 나온 값만 덮어쓴다 (F3010: 바뀐 조건만 갱신)."""
    updates: dict = {}
    if analysis.os_name:
        norm_os = normalize_os_name(analysis.os_name)
        if norm_os:
            updates["os_name"] = norm_os
    os_name = updates.get("os_name", prev.os_name)
    if analysis.os_version:
        updates["os_version"] = normalize_os_version(os_name, analysis.os_version)
    elif "os_name" in updates and updates["os_name"] != prev.os_name:
        updates["os_version"] = None  # OS가 바뀌었는데 버전이 없으면 이전 버전을 쓰지 않고 다시 묻는다 (리뷰 #11)
    if normalize_python(analysis.python_version):
        updates["python_version"] = normalize_python(analysis.python_version)
    if analysis.capacity and analysis.capacity > 0:
        updates["capacity"] = analysis.capacity
    if analysis.first_date:
        try:
            updates["first_date"] = date.fromisoformat(analysis.first_date)
        except ValueError:
            pass  # 형식이 틀리면 버림 → 빠진 입력이면 되묻는다
    for key in ("window_start", "window_end"):
        if getattr(analysis, key):
            updates[key] = getattr(analysis, key)
    new_weekdays = normalize_weekdays(getattr(analysis, "weekdays", None))
    new_interval = analysis.interval_days if (analysis.interval_days and analysis.interval_days > 0) else None
    raw_wc = getattr(analysis, "weekly_count", None)
    new_weekly_count = raw_wc if (isinstance(raw_wc, int) and not isinstance(raw_wc, bool) and raw_wc > 0) else None

    if new_weekdays:
        updates["weekdays"] = new_weekdays
        updates["interval_days"] = None
        updates["weekly_count"] = None
        updates["week_interval"] = 2 if new_interval == 14 else 1
    elif new_interval in (7, 14) and prev.weekdays:
        # 요일을 정해 둔 뒤 "격주로 바꿔줘"·"매주로" → 요일은 두고 주 간격만 바꾼다 (요일을 잃지 않게)
        updates["week_interval"] = 2 if new_interval == 14 else 1
        updates["weekly_count"] = None
    elif new_interval:
        updates["interval_days"] = new_interval
        updates["weekdays"] = None
        updates["week_interval"] = None
        updates["weekly_count"] = None
    elif new_weekly_count:
        updates["weekly_count"] = new_weekly_count
        updates["weekdays"] = None
        updates["interval_days"] = None
        updates["week_interval"] = None
    return prev.model_copy(update=updates)


def build_graph(brain: AgentBrain, runner: ToolRunner, emit: Emit = no_emit):
    def step(name: str, fn: Callable[[AgentState], dict]):
        def wrapped(state: AgentState) -> dict:
            emit("step_start", {"step": name})
            out = fn(state)
            emit("step_end", {"step": name, **STEP_SUMMARY.get(name, lambda o: {})(out)})
            return out

        return wrapped

    # ── 노드 ────────────────────────────────────────────
    def analyze(state: AgentState) -> dict:
        try:
            a = brain.analyze(state["message"], state["conditions"], state["today"], state.get("last_turn"))
        except Exception as e:  # LLM이 죽어도 서비스는 안내로 끝낸다 (NF3003)
            emit("error", {"step": "analyze", "kind": type(e).__name__})
            return {"intent": "error", "answer": "허허, 잠깐 기계가 말을 안 듣네요. 잠시 후 다시 해 보시죠."}
        conditions = merge_conditions(state["conditions"], a)
        unsupported = bool(getattr(a, "interval_unsupported", False))
        missing = missing_inputs(conditions) if a.intent == "plan" else []  # 계획일 때만 (시나리오 점검)
        if a.intent == "plan" and unsupported and "interval_days" not in missing:
            missing = [*missing, "interval_days"]
        emit("llm_decision", {"decision": "intent", "intent": a.intent, "reason": a.intent_reason})
        return {"intent": a.intent, "intent_reason": a.intent_reason, "conditions": conditions,
                "missing": missing,
                "interval_unsupported": unsupported,
                "confirm_rounds": a.confirm_rounds}

    def ask(state: AgentState) -> dict:
        return {"answer": ask_message(state["missing"], state.get("conditions"), state.get("interval_unsupported", False))}

    def plan_tools(state: AgentState) -> dict:
        try:
            plan = brain.plan_tools(state["conditions"])
            steps, reason = list(dict.fromkeys(plan.steps)), plan.reason
        except Exception:
            steps, reason = [], LLM_FAILED
        added = [t for t in PLAN_TOOLS if t not in steps]
        steps = [t for t in steps if t in PLAN_TOOLS] + added
        emit("llm_decision", {"decision": "tool_plan", "steps": steps, "reason": reason, "added_by_code": added})
        return {"tool_plan": steps, "tool_plan_reason": reason}

    def call_tools(state: AgentState) -> dict:
        c = state["conditions"]
        results: dict = {"vulns": {}, "versions": {}}
        for tool in state["tool_plan"]:
            if tool == "get_eol":
                os_r, py_r = runner.call_many([
                    ("get_eol", {"product": c.os_name, "cycle": c.os_version}),
                    ("get_eol", {"product": "python", "cycle": c.python_version}),
                ])
                results["eol_os"], results["eol_python"] = os_r, py_r
            elif tool == "get_vulns":
                calls = [("get_vulns", {"name": p["name"], "version": p["version"]}) for p in c.packages]
                for p, r in zip(c.packages, runner.call_many(calls)):
                    results["vulns"][p["name"]] = r
            elif tool == "get_package_versions":
                # 취약점을 먼저 조회했으면, 조회에 성공한 패키지만 버전 목록을 받는다 (실패는 이미 "확인 못 함").
                # 0건도 받는다: OSV는 없는 패키지도 0건이라, PyPI에 그 패키지·버전이 있는지 확인해야 "안전"이라 할 수 있다
                if "get_vulns" in state["tool_plan"][: state["tool_plan"].index(tool)]:
                    targets = [p for p in c.packages if _vulns_ok(results["vulns"].get(p["name"]))]
                else:
                    targets = c.packages
                calls = [("get_package_versions", {"name": p["name"]}) for p in targets]
                for p, r in zip(targets, runner.call_many(calls)):
                    results["versions"][p["name"]] = r

        all_results = [r for k in ("eol_os", "eol_python") if k in results for r in [results[k]]]
        all_results += list(results["vulns"].values()) + list(results["versions"].values())
        codes = {r["error"]["code"] for r in all_results if not r["ok"]}
        if all_results and all(not r["ok"] for r in all_results) and len(codes) == 1 and codes <= {TIMEOUT, UPSTREAM_ERROR}:
            emit("error", {"step": "call_tools", "kind": "all_tools_failed", "code": codes.pop()})
            return {"results": results, "tools_down": True, "answer": TOOLS_DOWN}
        return {"results": results}

    def judge(state: AgentState) -> dict:
        c, results = state["conditions"], state["results"]
        decided: dict[str, PackageResult] = {}
        pending = []  # (name, current, severity, target) — 목표 버전 재조회가 필요한 것
        for p in c.packages:
            name, current = p["name"], p["version"]
            vulns = results["vulns"].get(name)
            if not vulns or not vulns["ok"]:
                decided[name] = PackageResult(name, current, unchecked_reason="취약점 정보를 확인하지 못함")
                continue
            severity = top_severity(vulns["data"]["vulns"])
            versions = results["versions"].get(name)
            if severity is None:
                problem = _existence_problem(name, current, versions)
                decided[name] = PackageResult(name, current, unchecked_reason=problem) if problem \
                    else PackageResult(name, current)
                continue
            if not versions or not versions["ok"]:
                decided[name] = PackageResult(name, current, unchecked_reason="버전 정보를 확인하지 못함")
                continue
            target = pick_latest(versions["data"]["versions"], c.python_version)
            if target is None or not is_newer(target.version, current):
                # 지금 Python에 설치 가능한 버전이 없거나, 현재보다 높은 버전이 없음 → 위반 (리뷰 #4·#12)
                decided[name] = PackageResult(name, current, severity, None, violation=True)
                continue
            pending.append((name, current, severity, target))

        counts = runner.call_many([("get_vulns", {"name": n, "version": t.version}) for n, _, _, t in pending])
        for (name, current, severity, target), r in zip(pending, counts):
            remaining = r["data"]["count"] if r["ok"] else None
            if remaining is None:
                decided[name] = PackageResult(name, current, unchecked_reason="목표 버전 취약점을 확인하지 못함")
            else:
                decided[name] = PackageResult(name, current, severity, target, violation=remaining > 0)

        package_results = [decided[p["name"]] for p in c.packages]
        violations = [
            {"name": r.name, "current": r.current_version,
             "best_on_current_python": r.target.version if r.target else None}
            for r in package_results if r.violation
        ]
        emit("judgment", {
            "packages": [{"name": r.name, "current": r.current_version, "severity": r.severity,
                          "target_on_current_python": r.target.version if r.target else None,
                          "status": _status(r)} for r in package_results],
            "violations": [v["name"] for v in violations],
        })
        return {"package_results": package_results, "violations": violations}

    def replan(state: AgentState) -> dict:
        c = state["conditions"]
        try:
            choice = brain.choose_replan(state["violations"], c.python_version, state["message"])
            strategy, reason = choice.strategy, choice.reason
        except Exception:
            strategy, reason = "upgrade_python", LLM_FAILED
        emit("llm_decision", {"decision": "replan_strategy", "strategy": strategy, "reason": reason})
        if strategy != "upgrade_python":
            return {"replan_strategy": strategy, "replan_reason": reason,
                    "upgrade": UpgradePlan(status="hold", reason=f"보류로 결정: {reason}")}

        names = {v["name"] for v in state["violations"]}
        packages = {n: r["data"]["versions"] for n, r in state["results"]["versions"].items() if n in names}
        # 후보 버전 취약점을 미리 병렬로 조회 (요청 안 캐시에 남아 아래 탐색은 기다리지 않음, 3일차 응답 시간 개선)
        runner.call_many([("get_vulns", {"name": n, "version": v})
                          for n, v in candidate_versions(c.python_version, packages)])
        upgrade = plan_python_upgrade(c.python_version, packages, runner.vuln_count, runner.python_eol)
        for no, attempt in enumerate(upgrade.attempts, 1):
            emit("replan", {"no": no, "python": attempt.python, "is_eol": attempt.is_eol, "reason": attempt.reason})
        if upgrade.status != "ok":
            emit("replan", {"no": None, "result": "hold", "reason": upgrade.reason})
        return {"replan_strategy": strategy, "replan_reason": reason, "upgrade": upgrade}

    def build(state: AgentState) -> dict:
        c, results = state["conditions"], state["results"]
        os_r, py_r = results.get("eol_os"), results.get("eol_python")
        items = build_items(
            state["package_results"], c.python_version,
            py_r["data"] if py_r and py_r["ok"] else None, state.get("upgrade"),
            os_display_name(c.os_name), os_display_version(c.os_name, c.os_version),
            os_r["data"] if os_r and os_r["ok"] else None, upgrade_hint(c.os_name),
        )
        ordered = sort_items(items.items, state["today"])
        schedule_missing = [k for k in state.get("missing", []) if k in SCHEDULE_KEYS]
        rounds = (
            RoundsResult()
            if schedule_missing
            else split_rounds(
                ordered,
                c.capacity,
                c.first_date,
                c.interval_days,
                weekdays=c.weekdays,
                week_interval=c.week_interval or 1,
            )
        )
        emit("plan_built", {
            "rule": "등급(CRITICAL>HIGH>MODERATE>LOW>미상) → 지원 종료가 빠른 순, Python 업그레이드가 필요한 항목은 업그레이드 다음 회차",
            "order": [{"name": i.name, "severity": i.severity,
                       "eol_date": i.eol_date.isoformat() if i.eol_date else None,
                       "after_python_upgrade": i.needs_python_upgrade} for i in ordered],
            "rounds": [{"round_no": r.round_no, "date": r.date.isoformat(), "items": [i.name for i in r.items]}
                       for r in rounds.rounds],
            "unassigned": [i.name for i in rounds.unassigned],
            "capacity": c.capacity,
        })
        # "무엇부터"의 순서: 위험한 순서이되, Python 업그레이드가 필요한 항목은 업그레이드 뒤로 (순서 제약 먼저)
        doing_order = [i for r in split_rounds(ordered, max(len(ordered), 1), state["today"], 1).rounds
                       for i in r.items] if ordered else []
        calendar_check = fit_to_calendar(rounds.rounds, c.window_start, c.window_end, allowed_weekdays=c.weekdays)
        plan = plan_dict(items, rounds, state.get("upgrade"), doing_order)
        plan["calendar_check"] = calendar_check
        plan["schedule_missing"] = schedule_missing
        plan["window"] = {"start": c.window_start, "end": c.window_end}
        plan["excluded"] = c.excluded
        plan["eol_checks"] = {
            # 조회 기준(예: Windows Home/Pro)을 함께 넘겨 답에 그대로 밝히게 한다 (spec v1.17)
            "os": {**os_r["data"], "name": os_display_name(c.os_name),
                   "version": os_display_version(c.os_name, c.os_version)} if os_r and os_r["ok"] else "확인 못 함",
            "python": py_r["data"] if py_r and py_r["ok"] else "확인 못 함",
        }
        return {"plan": plan}

    def fit_to_calendar(
        rounds: list,
        start: str | None,
        end: str | None,
        allowed_weekdays: list[int] | None = None,
    ) -> str:
        """회차마다 캘린더를 조회해 겹치면 다음 빈 날로 (F3023 · v1.21 M). 캘린더 Tool이 없으면 건너뜀."""
        if "list_calendar_events" not in runner.registry.names():
            return "사용 안 함"
        if not rounds:
            return "확인함"
        status = "확인함"
        prev_date: date | None = None
        for r in rounds:
            orig_date = r.date
            # 앞 회차가 밀려 같은 날(또는 이전 날)이 되면 다음 맞는 날로 민다 (spec v1.21 M)
            if prev_date is not None and r.date <= prev_date:
                pushed = (
                    next_matching_date(prev_date + timedelta(days=1), allowed_weekdays)
                    if allowed_weekdays
                    else prev_date + timedelta(days=1)
                )
                move_round(r, pushed)
            result = runner.call("list_calendar_events", {
                "date_from": r.date.isoformat(),
                "date_to": (r.date + timedelta(days=SEARCH_DAYS)).isoformat()})
            if not result["ok"]:
                status = "확인 못 함"  # 날짜는 그대로 (지어내지 않음)
                prev_date = r.date
                continue
            events = result["data"]["events"]
            free = find_free_date(r.date, start, end, events, allowed_weekdays=allowed_weekdays)
            if free is None:
                r.calendar_conflicts = [e["title"] for e in conflicts_on(r.date, start, end, events)]
            elif free != r.date:
                move_round(r, free)
                r.moved_from = orig_date
            prev_date = r.date
        emit("calendar_check", {"status": status, "rounds": [
            {"round_no": r.round_no, "date": r.date.isoformat(),
             "moved_from": r.moved_from.isoformat() if r.moved_from else None,
             "conflicts": r.calendar_conflicts} for r in rounds]})
        return status

    def respond(state: AgentState) -> dict:
        try:
            answer = brain.write_response(state["plan"])
        except Exception:
            answer = fallback_text(state["plan"])
        header = conditions_header(state["conditions"])
        if header:
            answer = f"{header}\n\n{answer}"
        if state["plan"].get("schedule_missing"):  # 우선순위를 보여 준 뒤 일정만 되묻는다 (spec v1.14)
            answer += "\n\n" + schedule_ask_message(
                state["plan"]["schedule_missing"],
                state.get("conditions"),
                state.get("interval_unsupported", False),
            )
        return {"answer": answer}

    def fact(state: AgentState) -> dict:
        try:
            return {"answer": brain.answer_fact(state["message"], runner, state["conditions"])}
        except Exception:
            return {"answer": "허허, 잠깐 답을 정리하지 못했네요. 잠시 후 다시 해 보시죠."}

    def other(state: AgentState) -> dict:
        if state["intent"] == "confirm":
            return {"answer": "도장 찍습니다. 확정이에요."}  # 저장은 API가 한다 (Tool 아님)
        try:
            return {"answer": brain.chat(state["message"])}
        except Exception:
            return {"answer": "차트를 보려면 requirements.txt와 OS·Python 버전을 알려 주시죠."}

    # ── 연결 ────────────────────────────────────────────
    g = StateGraph(AgentState)
    for name, fn in [("analyze", analyze), ("ask", ask), ("plan_tools", plan_tools), ("call_tools", call_tools),
                     ("judge", judge), ("replan", replan), ("build", build), ("respond", respond),
                     ("fact", fact), ("other", other)]:
        g.add_node(name, step(name, fn))

    def after_analyze(state: AgentState) -> str:
        intent = state["intent"]
        if intent == "error":
            return END
        if intent == "plan":
            return "ask" if tool_inputs_missing(state["missing"]) else "plan_tools"  # 일정만 빠지면 우선순위 먼저
        return "fact" if intent == "fact" else "other"

    g.add_edge(START, "analyze")
    g.add_conditional_edges("analyze", after_analyze, ["ask", "plan_tools", "fact", "other", END])
    g.add_edge("plan_tools", "call_tools")
    g.add_conditional_edges("call_tools", lambda s: END if s.get("tools_down") else "judge", ["judge", END])
    g.add_conditional_edges("judge", lambda s: "replan" if s["violations"] else "build", ["replan", "build"])
    g.add_edge("replan", "build")
    g.add_edge("build", "respond")
    for last in ("ask", "respond", "fact", "other"):
        g.add_edge(last, END)
    return g.compile()


def run_agent(
    message: str,
    conditions: Conditions,
    brain: AgentBrain,
    *,
    today: date | None = None,
    emit: Emit = no_emit,
    runner: ToolRunner | None = None,
    last_turn: dict | None = None,
    calendar=None,
    db_path: str | None = None,
) -> dict:
    """요청 하나를 처리한다. 결과: intent, answer, conditions(갱신됨), plan(계획 수립일 때), missing, tool_plan."""
    runner = runner or ToolRunner(build_registry(calendar, db_path), emit)
    graph = build_graph(brain, runner, emit)
    state = graph.invoke({"message": message, "conditions": conditions, "today": today or date.today(),
                          "last_turn": last_turn})
    return {
        "intent": state.get("intent"),
        "answer": state.get("answer"),
        "conditions": state.get("conditions", conditions),
        "missing": state.get("missing", []),
        "tool_plan": state.get("tool_plan", []),
        "plan": state.get("plan"),
        "tool_calls": runner.calls,
        "confirm_rounds": state.get("confirm_rounds"),
    }
