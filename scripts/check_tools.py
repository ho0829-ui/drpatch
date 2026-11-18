"""Tool 3종을 실제 API로 한 번씩 불러보는 수동 확인 스크립트. 테스트가 아니다.

    .venv/bin/python scripts/check_tools.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools.default import build_registry  # noqa: E402

CALLS = [
    ("get_eol", {"product": "ubuntu", "cycle": "20.04"}),
    ("get_eol", {"product": "python", "cycle": "3.8.10"}),
    ("get_eol", {"product": "ubuntu", "cycle": "99.99"}),
    ("get_vulns", {"name": "requests", "version": "2.19.0"}),
    ("get_vulns", {"name": "django", "version": "2.2.0"}),
    ("get_vulns", {"name": "requests", "version": "2.34.2"}),
    ("get_package_versions", {"name": "django"}),
    ("get_package_versions", {"name": "no-such-package-xyz-123"}),
    ("get_eol", {"product": "", "cycle": "20.04"}),
]


def summary(name: str, data: dict) -> str:
    if name == "get_eol":
        return f"{data['label']} 종료 {data['eol_date']} ESM {data['esm_date']} note={data['note']}"
    if name == "get_vulns":
        levels = sorted({v["severity"] or "미상" for v in data["vulns"]})
        return f"{data['count']}건 {levels} truncated={data['truncated']}"
    return f"latest {data['latest']}, 버전 {len(data['versions'])}개"


registry = build_registry()
for name, args in CALLS:
    start = time.perf_counter()
    result = registry.call(name, args)
    took = time.perf_counter() - start
    body = summary(name, result["data"]) if result["ok"] else f"{result['error']['code']}: {result['error']['message']}"
    print(f"[{'ok' if result['ok'] else '실패'}] {name}({args}) {took:.2f}초\n      {body}")
