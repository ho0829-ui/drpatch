"""결과 없음·없는 대상·재계획 경로의 실제 응답을 한 번 받아 tests/fixtures/에 저장한다 (요구사항 2.7 Tool 설계 확인).

    .venv/bin/python scripts/capture_failure_fixtures.py

저장 형식: {"status": HTTP 상태, "body": JSON 본문 또는 null, "text": JSON이 아니면 본문 앞부분}
"""

import json
import pathlib

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
HEADERS = {"User-Agent": "sudo-patch/0.1 (study project; patch planner)"}

CASES = [
    ("eol_no_product", "GET", "https://endoflife.date/api/v1/products/no-such-product-xyz/releases/1.0", None),
    ("eol_no_cycle", "GET", "https://endoflife.date/api/v1/products/ubuntu/releases/99.99", None),
    ("eol_python_3.14", "GET", "https://endoflife.date/api/v1/products/python/releases/3.14", None),
    ("osv_requests_2.32.5", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "requests", "ecosystem": "PyPI"}, "version": "2.32.5"}),
    ("osv_requests_2.34.2", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "requests", "ecosystem": "PyPI"}, "version": "2.34.2"}),
    ("osv_no_package", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "no-such-package-xyz-123", "ecosystem": "PyPI"}, "version": "1.0"}),
    ("pypi_no_package", "GET", "https://pypi.org/pypi/no-such-package-xyz-123/json", None),
    ("pypi_requests_all", "GET", "https://pypi.org/pypi/requests/json", None),
    ("eol_python_3.10", "GET", "https://endoflife.date/api/v1/products/python/releases/3.10", None),
    ("eol_python_3.11", "GET", "https://endoflife.date/api/v1/products/python/releases/3.11", None),
    ("osv_django_4.2.30", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "django", "ecosystem": "PyPI"}, "version": "4.2.30"}),
    ("osv_django_5.2.19", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "django", "ecosystem": "PyPI"}, "version": "5.2.19"}),
    ("osv_requests_2.32.4", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "requests", "ecosystem": "PyPI"}, "version": "2.32.4"}),    ("osv_django_6.1.3", "POST", "https://api.osv.dev/v1/query",
     {"package": {"name": "django", "ecosystem": "PyPI"}, "version": "6.1.3"}),
]

for name, method, url, body in CASES:
    r = requests.request(method, url, headers=HEADERS, json=body, timeout=15)
    try:
        payload = {"status": r.status_code, "body": r.json(), "text": None}
    except ValueError:
        payload = {"status": r.status_code, "body": None, "text": r.text[:300]}
    (FIX / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{name}: HTTP {r.status_code}, JSON={'예' if payload['body'] is not None else '아니오'}, {len(r.content)//1024}KB")
