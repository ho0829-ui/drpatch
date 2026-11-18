"""메인 Agent 그래프 (LangGraph). docs/architecture.md 3절.

analyze ─┬─ 계획인데 입력 빠짐 → ask
         ├─ 계획 → plan_tools → call_tools → judge ─┬─ 위반 → replan → build → respond
         │                                         └─────────────→ build → respond
         ├─ 사실 조회 → fact
         └─ 확정 / 그 밖 → other
노드마다 step_start/step_end, LLM 판단은 llm_decision, 재계획은 replan 이벤트를 발행한다 (F3012).
"""

from collections.abc import Callable
from datetime import date

from langgraph.graph import END, START, StateGraph

from app.agent.brain import AgentBrain
from app.agent.planner.items import PackageResult, build_items, top_severity
from app.agent.planner.priority import sort_items
from app.agent.planner.python_upgrade import UpgradePlan, plan_python_upgrade
from app.agent.planner.rounds import split_rounds
from app.agent.planner.versions import pick_latest
from app.agent.render import fallback_text, plan_dict
from app.agent.runner import Emit, ToolRunner, no_emit
from app.agent.state import (
    AgentState,
    Conditions,
    ask_message,
    missing_inputs,
    normalize_os_version,
    normalize_python,
)
from app.tools.default import build_registry

PLAN_TOOLS = ["get_eol", "get_vulns", "get_package_versions"]  # 계획 수립에 셋 다 필요
LLM_FAILED = "LLM 응답을 받지 못해 기본값을 썼어요"


def merge_conditions(prev: Conditions, analysis) -> Conditions:
    """이번 메시지에서 나온 값만 덮어쓴다 (F3010: 바뀐 조건만 갱신)."""
    updates: dict = {}
    if analysis.os_name:
        updates["os_name"] = analysis.os_name.strip().lower()
    os_name = updates.get("os_name", prev.os_name)
    if analysis.os_version:
        updates["os_version"] = normalize_os_version(os_name, analysis.os_version)
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
    if analysis.interval_days and analysis.interval_days > 0:
        updates["interval_days"] = analysis.interval_days
    return prev.model_copy(update=updates)


def build_graph(brain: AgentBrain, runner: ToolRunner, emit: Emit = no_emit):
    def step(name: str, fn: Callable[[AgentState], dict]):
        def wrapped(state: AgentState) -> dict:
            emit("step_start", {"step": name})
            out = fn(state)
            emit("step_end", {"step": name})
            return out

        return wrapped

    # ── 노드 ────────────────────────────────────────────
    def analyze(state: AgentState) -> dict:
        try:
            a = brain.analyze(state["message"], state["conditions"], state["today"])
        except Exception as e:  # LLM이 죽어도 서비스는 안내로 끝낸다 (NF3003)
            emit("error", {"step": "analyze", "kind": type(e).__name__})
            return {"intent": "error", "answer": "지금은 AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요."}
        conditions = merge_conditions(state["conditions"], a)
        emit("llm_decision", {"decision": "intent", "intent": a.intent, "reason": a.intent_reason})
        return {"intent": a.intent, "intent_reason": a.intent_reason, "conditions": conditions,
                "missing": missing_inputs(conditions)}

    def ask(state: AgentState) -> dict:
        return {"answer": ask_message(state["missing"])}

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
                calls = [("get_package_versions", {"name": p["name"]}) for p in c.packages]
                for p, r in zip(c.packages, runner.call_many(calls)):
                    results["versions"][p["name"]] = r
        return {"results": results}

    def judge(state: AgentState) -> dict:
        c, results = state["conditions"], state["results"]
        package_results, violations = [], []
        for p in c.packages:
            name, current = p["name"], p["version"]
            vulns = results["vulns"].get(name)
            if not vulns or not vulns["ok"]:
                package_results.append(PackageResult(name, current, unchecked_reason="취약점 정보를 확인하지 못함"))
                continue
            severity = top_severity(vulns["data"]["vulns"])
            if severity is None:
                package_results.append(PackageResult(name, current))
                continue
            versions = results["versions"].get(name)
            if not versions or not versions["ok"]:
                package_results.append(PackageResult(name, current, unchecked_reason="버전 정보를 확인하지 못함"))
                continue
            target = pick_latest(versions["data"]["versions"], c.python_version)
            if target is None:
                package_results.append(PackageResult(name, current, severity))
                continue
            remaining = runner.vuln_count(name, target.version)
            if remaining is None:
                package_results.append(PackageResult(name, current, unchecked_reason="목표 버전 취약점을 확인하지 못함"))
            elif remaining == 0:
                package_results.append(PackageResult(name, current, severity, target))
            else:
                package_results.append(PackageResult(name, current, severity, target, violation=True))
                violations.append({"name": name, "current": current, "best_on_current_python": target.version,
                                   "remaining_vulns": remaining})
        emit("judgment", {"violations": violations, "checked": len(package_results)})
        return {"package_results": package_results, "violations": violations}

    def replan(state: AgentState) -> dict:
        c = state["conditions"]
        try:
            choice = brain.choose_replan(state["violations"], c.python_version)
            strategy, reason = choice.strategy, choice.reason
        except Exception:
            strategy, reason = "upgrade_python", LLM_FAILED
        emit("llm_decision", {"decision": "replan_strategy", "strategy": strategy, "reason": reason})
        if strategy != "upgrade_python":
            return {"replan_strategy": strategy, "replan_reason": reason,
                    "upgrade": UpgradePlan(status="hold", reason=f"보류로 결정: {reason}")}

        names = {v["name"] for v in state["violations"]}
        packages = {n: r["data"]["versions"] for n, r in state["results"]["versions"].items() if n in names}
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
            c.os_name.capitalize() if c.os_name else None, c.os_version,
            os_r["data"] if os_r and os_r["ok"] else None,
        )
        ordered = sort_items(items.items, state["today"])
        rounds = split_rounds(ordered, c.capacity, c.first_date, c.interval_days)
        plan = plan_dict(items, rounds, state.get("upgrade"))
        plan["window"] = {"start": c.window_start, "end": c.window_end}
        plan["excluded"] = c.excluded
        plan["eol_checks"] = {
            "os": os_r["data"] if os_r and os_r["ok"] else "확인 못 함",
            "python": py_r["data"] if py_r and py_r["ok"] else "확인 못 함",
        }
        return {"plan": plan}

    def respond(state: AgentState) -> dict:
        try:
            answer = brain.write_response(state["plan"])
        except Exception:
            answer = fallback_text(state["plan"])
        return {"answer": answer}

    def fact(state: AgentState) -> dict:
        try:
            return {"answer": brain.answer_fact(state["message"], runner)}
        except Exception:
            return {"answer": "지금은 답을 만들지 못했어요. 잠시 후 다시 시도해 주세요."}

    def other(state: AgentState) -> dict:
        if state["intent"] == "confirm":
            return {"answer": "제안한 계획을 확정할게요."}  # 저장은 API가 한다 (Tool 아님)
        try:
            return {"answer": brain.chat(state["message"])}
        except Exception:
            return {"answer": "패치 계획을 세우려면 requirements.txt와 OS·Python 버전을 알려 주세요."}

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
            return "ask" if state["missing"] else "plan_tools"
        return "fact" if intent == "fact" else "other"

    g.add_edge(START, "analyze")
    g.add_conditional_edges("analyze", after_analyze, ["ask", "plan_tools", "fact", "other", END])
    g.add_edge("plan_tools", "call_tools")
    g.add_edge("call_tools", "judge")
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
) -> dict:
    """요청 하나를 처리한다. 결과: intent, answer, conditions(갱신됨), plan(계획 수립일 때), missing, tool_plan."""
    runner = runner or ToolRunner(build_registry(), emit)
    graph = build_graph(brain, runner, emit)
    state = graph.invoke({"message": message, "conditions": conditions, "today": today or date.today()})
    return {
        "intent": state.get("intent"),
        "answer": state.get("answer"),
        "conditions": state.get("conditions", conditions),
        "missing": state.get("missing", []),
        "tool_plan": state.get("tool_plan", []),
        "plan": state.get("plan"),
        "tool_calls": runner.calls,
    }
