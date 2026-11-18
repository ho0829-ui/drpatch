"""1일차 16시 게이트용 API 호출 확인 스크립트.

실행:  python check_apis.py
결과:  화면에 요약이 나오고, 응답 원본은 tests/fixtures/ 에 저장돼요 (나중에 테스트에 그대로 씀).
화면 요약 전체를 복사해서 대화에 붙여주세요.
"""
import json
import pathlib

import requests

FIX = pathlib.Path("tests/fixtures")
FIX.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "patch-planner-study/0.1 (SSAFY AI core project)"}
TIMEOUT = 15


def save(name, data):
    (FIX / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def call(name, method, url, **kw):
    try:
        r = requests.request(method, url, headers=HEADERS, timeout=TIMEOUT, **kw)
    except Exception as e:  # 네트워크 오류도 결과로 남김
        print(f"[{name}] 실패: {type(e).__name__}: {e}")
        return None
    size_kb = len(r.content) / 1024
    print(f"[{name}] HTTP {r.status_code}, {size_kb:.0f}KB, {r.elapsed.total_seconds():.2f}초")
    if r.status_code != 200:
        print("   본문 앞부분:", r.text[:200])
        return None
    data = r.json()
    save(name, data)
    return data


print("=" * 60, "\n1) endoflife.date (지원 종료일)")
for product, cycle in [("ubuntu", "20.04"), ("python", "3.8"), ("python", "3.12")]:
    name = f"eol_{product}_{cycle}"
    d = call(name, "GET", f"https://endoflife.date/api/v1/products/{product}/releases/{cycle}")
    if d is None:  # v1 경로가 바뀌었으면 예전 경로로 한 번 더
        d = call(name + "_old", "GET", f"https://endoflife.date/api/{product}/{cycle}.json")
    if d:
        body = d.get("result", d)
        print("   키 목록:", list(body.keys()))
        for k in ("eolFrom", "eol", "isEol", "eoesFrom", "extendedSupport", "isLts", "lts", "latest"):
            if k in body:
                print(f"   {k}: {body[k]}")

print("=" * 60, "\n2) OSV.dev (취약점)")
for pkg, ver in [("django", "2.2.0"), ("requests", "2.19.0"), ("requests", "2.32.3")]:
    d = call(f"osv_{pkg}_{ver}", "POST", "https://api.osv.dev/v1/query",
             json={"package": {"name": pkg, "ecosystem": "PyPI"}, "version": ver})
    if d is None:
        continue
    vulns = d.get("vulns", [])
    print(f"   {pkg}=={ver}: 취약점 {len(vulns)}건, next_page_token={'있음' if d.get('next_page_token') else '없음'}")
    no_label = 0
    for v in vulns:
        if not (v.get("database_specific") or {}).get("severity"):
            no_label += 1
    print(f"   등급 글자(database_specific.severity) 없는 건수: {no_label}")
    if vulns:
        v = vulns[0]
        print("   첫 건 id:", v.get("id"))
        print("   severity 필드:", v.get("severity"))
        print("   database_specific.severity:", (v.get("database_specific") or {}).get("severity"))
        fixed = [e.get("fixed") for a in v.get("affected", []) for rg in a.get("ranges", [])
                 for e in rg.get("events", []) if "fixed" in e]
        print("   수정 버전(fixed):", fixed[:5])

print("=" * 60, "\n3) PyPI JSON API (버전별 requires_python)")
d = call("pypi_django_all", "GET", "https://pypi.org/pypi/django/json")
if d:
    print("   최신 버전:", d["info"]["version"], "/ 최신의 requires_python:", d["info"].get("requires_python"))
    rel = d.get("releases", {})
    sample = {v: (files[0].get("requires_python") if files else None, files[0].get("yanked") if files else None)
              for v, files in list(rel.items()) if v in ("2.2.28", "3.2.25", "4.2", "5.0")}
    print("   릴리스 수:", len(rel), "/ 버전별 (requires_python, yanked):", sample)
for v in ("4.2", "5.0"):
    d = call(f"pypi_django_{v}", "GET", f"https://pypi.org/pypi/django/{v}/json")
    if d:
        print(f"   django {v} requires_python:", d["info"].get("requires_python"), "/ yanked:", d["info"].get("yanked"))

print("=" * 60, "\n끝. 위 내용을 전부 복사해서 붙여주세요. 원본은 tests/fixtures/ 에 저장됐어요.")
