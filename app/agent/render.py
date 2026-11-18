"""계획 결과를 화면·저장용 dict로 바꾸고, LLM이 실패했을 때 쓸 기본 문장을 만든다."""

from app.agent.planner.items import Item, ItemsResult
from app.agent.planner.python_upgrade import UpgradePlan
from app.agent.planner.rounds import RoundsResult

SEVERITY_KO = {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MODERATE": "MODERATE", "LOW": "LOW", "UNKNOWN": "심각도 미상"}


def item_dict(item: Item) -> dict:
    return {
        "kind": item.kind,
        "name": item.name,
        "current_version": item.current_version,
        "target_version": item.target_version,
        "severity": item.severity,
        "eol_date": item.eol_date.isoformat() if item.eol_date else None,
        "reason": item.reason,
        "flags": list(item.flags),
    }


def plan_dict(items: ItemsResult, rounds: RoundsResult, upgrade: UpgradePlan | None,
              ordered: list[Item] | None = None) -> dict:
    return {
        "priority": [item_dict(i) for i in (ordered or [])],  # 회차와 별개로 위험한 순서 (일정이 없어도 보여 줌)
        "rounds": [
            {"round_no": r.round_no, "date": r.date.isoformat(), "items": [item_dict(i) for i in r.items]}
            for r in rounds.rounds
        ],
        "unassigned": [item_dict(i) for i in rounds.unassigned],
        "safe": items.safe,
        "unchecked": items.unchecked,
        "held": items.held,
        "python_upgrade": None if upgrade is None else {
            "status": upgrade.status,
            "python": upgrade.python,
            "replans": upgrade.replans,
            "attempts": [a.__dict__ for a in upgrade.attempts],
            "reason": upgrade.reason,
        },
    }


def _item_line(item: dict) -> str:
    target = f" → {item['target_version']}" if item["target_version"] else ""
    flags = f" [{', '.join(item['flags'])}]" if item["flags"] else ""
    return f"  - {item['name']} {item['current_version']}{target} ({SEVERITY_KO[item['severity']]}){flags}: {item['reason']}"


def fallback_text(plan: dict) -> str:
    """LLM 응답이 실패해도 계획은 보여준다 (숫자는 코드 계산 그대로)."""
    lines = []
    for r in plan["rounds"]:
        lines.append(f"{r['round_no']}회차 ({r['date']})")
        lines += [_item_line(i) for i in r["items"]]
    if not plan["rounds"] and plan.get("priority"):
        lines.append("위험한 순서")
        lines += [_item_line(i) for i in plan["priority"]]
    elif not plan["rounds"]:
        lines.append("이번에 계획에 넣을 항목이 없어요.")
    extras = [
        ("미배정", [i["name"] for i in plan["unassigned"]]),
        ("안전(취약점 0건)", plan["safe"]),
        ("확인 못 함", [f"{u['name']}({u['reason']})" for u in plan["unchecked"]]),
        ("보류", [f"{h['name']}({h['reason']})" for h in plan["held"]]),
    ]
    lines += [f"{label}: {', '.join(names)}" for label, names in extras if names]
    return "\n".join(lines)
