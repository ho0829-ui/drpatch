"""get_vulns: OSV.dev로 패키지 버전의 취약점 조회 (F3002 후보 확보)."""

import re

from app.tools import http
from app.tools.base import UPSTREAM_ERROR, safe_parse, fail, ok
from app.tools.specs import VulnsInput

QUERY_URL = "https://api.osv.dev/v1/query"
MAX_PAGES = 10
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MODERATE", "LOW"]


def normalize_name(name: str) -> str:
    """PyPI 이름 비교용 (PEP 503): 소문자, -_. 묶음은 - 하나로."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _severity(vuln: dict) -> str | None:
    value = (vuln.get("database_specific") or {}).get("severity")
    value = value.upper() if isinstance(value, str) else None
    return value if value in SEVERITY_ORDER else None


def _higher(a: str | None, b: str | None) -> str | None:
    if a is None or b is None:
        return a or b
    return a if SEVERITY_ORDER.index(a) <= SEVERITY_ORDER.index(b) else b


def _fixed_versions(vuln: dict, package: str) -> list[str]:
    fixed = []
    for affected in vuln.get("affected") or []:
        pkg = affected.get("package") or {}
        if pkg.get("ecosystem") != "PyPI" or normalize_name(pkg.get("name", "")) != package:
            continue
        for rng in affected.get("ranges") or []:
            if rng.get("type") != "ECOSYSTEM":  # GIT 범위의 fixed는 커밋 해시라 버전이 아님
                continue
            for event in rng.get("events") or []:
                if "fixed" in event and event["fixed"] not in fixed:
                    fixed.append(event["fixed"])
    return fixed


def group_vulns(vulns: list[dict], package: str) -> list[dict]:
    """같은 취약점(id·aliases가 겹침)을 1건으로 묶는다. 등급은 있는 쪽(둘 다 있으면 높은 쪽)."""
    package = normalize_name(package)
    groups: list[dict] = []
    for vuln in vulns:
        ids = {vuln.get("id"), *(vuln.get("aliases") or [])} - {None}
        severity = _severity(vuln)
        fixed = _fixed_versions(vuln, package)
        target = next((g for g in groups if g["ids"] & ids), None)
        if target is None:
            groups.append({"id": vuln.get("id"), "ids": ids, "severity": severity, "fixed_versions": fixed})
            continue
        target["ids"] |= ids
        target["severity"] = _higher(target["severity"], severity)
        target["fixed_versions"] += [v for v in fixed if v not in target["fixed_versions"]]
    return [{k: g[k] for k in ("id", "severity", "fixed_versions")} for g in groups]


def get_vulns(params: VulnsInput) -> dict:
    query = {"package": {"name": params.name, "ecosystem": "PyPI"}, "version": params.version}
    vulns: list[dict] = []
    page_token = None
    truncated = False
    for page in range(MAX_PAGES):
        body = {**query, "page_token": page_token} if page_token else query
        fetched = http.fetch_json("POST", QUERY_URL, json_body=body)
        if not fetched["ok"]:
            return fetched
        data = fetched["data"]
        if not isinstance(data, dict) or not isinstance(data.get("vulns", []), list):
            return fail(UPSTREAM_ERROR, "OSV 응답 형식이 예상과 다릅니다")
        vulns += data.get("vulns", [])  # 모르는 패키지·0건이면 {} (2026-11-18 확인)
        page_token = data.get("next_page_token")
        if not page_token:
            break
    else:
        truncated = True  # 페이지 상한까지 받았는데 다음 쪽이 남음

    grouped = safe_parse(lambda: ok(group_vulns(vulns, params.name)))
    if not grouped["ok"]:
        return grouped
    return ok({"count": len(grouped["data"]), "vulns": grouped["data"], "truncated": truncated})
