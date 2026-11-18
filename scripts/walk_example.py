"""spec "예시 한 건 따라가기"를 실제 Tool(실제 API)로 한 단계씩 밟아 보는 확인 스크립트. 테스트가 아니다.

    .venv/bin/python scripts/walk_example.py

주의: 4단계의 버전 비교·requires_python 판정은 **확인용 임시 계산**이다 (>=3.N 하한, 숫자 비교만 봄).
실제 판정 코드는 packaging(허용 시) 또는 별도 구현으로 만든다. 이 스크립트가 그 필요를 드러내는 게 목적.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing.requirements import parse  # noqa: E402
from app.tools.default import build_registry  # noqa: E402

FILE = "requests==2.19.0\ndjango==2.2.0\n-e git+https://github.com/me/tool.git#egg=tool\n"
PYTHON = (3, 8)
reg = build_registry()
notes: list[str] = []


def step(title: str) -> None:
    print(f"\n=== {title}")


def rough_key(version: str):
    """임시: 숫자 부분만 비교. 1.0rc1, 1!2.0 같은 건 정확히 못 다룬다."""
    if not re.fullmatch(r"\d+(\.\d+)*", version):
        return None  # 정식 버전이 아님(rc, a, b, dev, post 등) → 임시 계산에서 제외
    return tuple(int(p) for p in version.split("."))


def rough_allows(requires_python: str | None, py: tuple[int, int]) -> bool | None:
    """임시: 쉼표로 나뉜 조건 중 >=, >, <, !=X.Y.* 만 대충 본다. None = 판정 못 함."""
    if not requires_python:
        return None
    for cond in requires_python.replace(" ", "").split(","):
        m = re.fullmatch(r"(>=|>|<=|<|!=|==)(\d+)(?:\.(\d+))?(?:\.(\d+|\*))?", cond)
        if not m:
            return None
        op, major, minor = m[1], int(m[2]), int(m[3] or 0)
        target = (major, minor)
        if op == ">=" and not py >= target:
            return False
        if op == ">" and not py > target:
            return False
        if op == "<" and not py < target:
            return False
        if op == "<=" and not py <= target:
            return False
        if op == "!=" and m[4] == "*" and py == target:
            return False
    return True


step("1. 파싱")
parsed = parse(FILE)
print("조회:", [(p.name, p.version) for p in parsed.packages])
print("제외:", [(e.line_no, e.reason) for e in parsed.excluded])

step("2. get_eol (OS·Python)")
for product, cycle in [("ubuntu", "20.04"), ("python", "3.8")]:
    r = reg.call("get_eol", {"product": product, "cycle": cycle})
    d = r["data"]
    print(f"{d['label']}: 종료 {d['eol_date']} is_eol={d['is_eol']} ESM {d['esm_date']}")

step("3. get_vulns (현재 버전)")
current = {}
for p in parsed.packages:
    d = reg.call("get_vulns", {"name": p.name, "version": p.version})["data"]
    levels = [v["severity"] for v in d["vulns"]]
    top = next((s for s in ["CRITICAL", "HIGH", "MODERATE", "LOW"] if s in levels), "미상")
    current[p.name] = d
    print(f"{p.name} {p.version}: {d['count']}건, 최고 {top}")

step("4. get_package_versions → Python 3.8에서 설치 가능한 최신 (임시 계산)")
targets = {}
for p in parsed.packages:
    d = reg.call("get_package_versions", {"name": p.name})["data"]
    candidates, unknown, prerelease = [], [], 0
    for v in d["versions"]:
        if v["yanked"]:
            continue
        key = rough_key(v["version"])
        if key is None:
            prerelease += 1
            continue
        allowed = rough_allows(v["requires_python"], PYTHON)
        if allowed is None:
            unknown.append(v["version"])
            candidates.append((key, v["version"], "호환 미확인"))
        elif allowed:
            candidates.append((key, v["version"], "호환"))
    best = max(candidates) if candidates else None
    best_known = max((c for c in candidates if c[2] == "호환"), default=None)
    targets[p.name] = best
    print(f"{p.name}: 최신 {d['latest']} / 3.8 최신 후보 {best[1]}({best[2]}) / "
          f"requires_python 확인된 것 중 최신 {best_known[1] if best_known else '없음'}")
    print(f"   정식 아닌 버전(rc 등) {prerelease}개 건너뜀, requires_python 비어 있음 {len(unknown)}개 "
          f"(예: {unknown[-3:]})")

step("5. get_vulns (목표 버전 재조회)")
violations = []
for name, best in targets.items():
    d = reg.call("get_vulns", {"name": name, "version": best[1]})["data"]
    print(f"{name} {best[1]}: {d['count']}건 {[v['severity'] for v in d['vulns']]}")
    if d["count"]:
        violations.append(name)
print("호환 제약 위반:", violations or "없음")

step("6. (위반 시) Python 업그레이드 후보")
for py in [(3, 10), (3, 12)]:
    r = reg.call("get_eol", {"product": "python", "cycle": f"{py[0]}.{py[1]}"})["data"]
    print(f"python {py[0]}.{py[1]}: 종료 {r['eol_date']} is_eol={r['is_eol']}")
for name in violations:
    d = reg.call("get_package_versions", {"name": name})["data"]
    for py in [(3, 10), (3, 12)]:
        ok_versions = [(rough_key(v["version"]), v["version"]) for v in d["versions"]
                       if not v["yanked"] and rough_key(v["version"]) and rough_allows(v["requires_python"], py)]
        top = max(ok_versions)[1]
        vc = reg.call("get_vulns", {"name": name, "version": top})["data"]["count"]
        print(f"{name}: Python {py[0]}.{py[1]}에서 최신 {top} → 취약점 {vc}건")
