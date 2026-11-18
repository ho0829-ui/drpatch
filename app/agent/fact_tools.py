"""사실 조회 경로에서 LLM에게 넘길 Tool 결과를 코드가 먼저 계산·요약한다 (2일차 리뷰 #3).

LLM에게 버전 목록 원본을 주지 않는다 → 버전 비교·시험판 제외·requires_python 판정은 코드(planner)가 한다.
"""

from app.agent.planner.items import top_severity
from app.agent.planner.versions import pick_latest
from app.agent.runner import ToolRunner

VULN_LIST_LIMIT = 10


def run_fact_tool(runner: ToolRunner, name: str, args: dict, python_version: str | None) -> dict:
    result = runner.call(name, args)
    if not result["ok"]:
        return {"ok": False, "error": result["error"]["code"], "note": "확인 못 함"}
    data = result["data"]

    if name == "get_package_versions":
        summary = {"ok": True, "package": args.get("name"), "latest": data["latest"], "project_url": data["project_url"]}
        if not python_version:
            summary["note"] = "Python 버전을 모르면 설치 가능한 버전을 계산하지 않는다. 사용자에게 Python 버전을 물어라."
            return summary
        target = pick_latest(data["versions"], python_version)
        summary["python"] = python_version
        if target is None:
            summary["installable_latest"] = None
            summary["note"] = f"Python {python_version}에서 설치 가능한 정식 버전이 없다."
            return summary
        count = runner.vuln_count(args["name"], target.version)
        summary.update({
            "installable_latest": target.version,  # 코드가 계산: 이 Python에서 설치 가능한 최신 정식 버전
            "compat_unknown": target.compat_unknown,
            "vulns_in_installable_latest": "확인 못 함" if count is None else count,
        })
        return summary

    if name == "get_vulns":
        return {"ok": True, "count": data["count"], "top_severity": top_severity(data["vulns"]),
                "vulns": data["vulns"][:VULN_LIST_LIMIT], "truncated": data["truncated"] or data["count"] > VULN_LIST_LIMIT}

    return {"ok": True, **data}  # get_eol: 날짜 값 그대로
