"""판단 결과를 계획 항목으로 묶는다 (spec "우선순위" 아래 규칙, "재계획"의 같은 일은 한 항목).

- 취약점 0건 → "안전" 목록, Tool 실패 → "확인 못 함" 목록, 업그레이드로도 못 고침 → "보류" 목록. 셋 다 회차에 안 넣음.
- Python 항목은 하나: 지원 종료(HIGH)와 재계획으로 생긴 업그레이드를 합친다. 업그레이드는 앞 회차에 와야 할
  전제 조건이라 등급은 HIGH로 둔다.
"""

from dataclasses import dataclass, field
from datetime import date

from app.agent.planner.python_upgrade import UpgradePlan
from app.agent.planner.versions import Candidate, is_major_change

SEVERITIES = ["CRITICAL", "HIGH", "MODERATE", "LOW", "UNKNOWN"]  # UNKNOWN = 심각도 미상

FLAG_MAJOR = "큰 변경"
FLAG_COMPAT_UNKNOWN = "호환 미확인"
FLAG_AFTER_EOL = "종료 이후 처리"


def top_severity(vulns: list[dict]) -> str | None:
    """가진 취약점 중 가장 높은 등급. 0건이면 None, 등급이 전부 없으면 UNKNOWN."""
    if not vulns:
        return None
    levels = {v.get("severity") or "UNKNOWN" for v in vulns}
    return next(s for s in SEVERITIES if s in levels)


@dataclass(frozen=True)
class PackageResult:
    """패키지 하나의 판단 결과 (judge 단계가 만든다)."""

    name: str
    current_version: str
    severity: str | None = None  # 현재 버전의 최고 등급. None = 0건
    target: Candidate | None = None  # 현재 Python 기준 목표 (위반이 아닐 때)
    violation: bool = False  # 현재 Python으론 안전한 버전이 없음
    unchecked_reason: str | None = None  # Tool 실패 등으로 확인 못 함


@dataclass(frozen=True)
class Item:
    kind: str  # package | python_upgrade | os
    name: str
    current_version: str
    target_version: str | None
    severity: str
    eol_date: date | None
    reason: str
    flags: tuple[str, ...] = ()
    needs_python_upgrade: bool = False


@dataclass
class ItemsResult:
    items: list[Item] = field(default_factory=list)
    safe: list[str] = field(default_factory=list)
    unchecked: list[dict] = field(default_factory=list)  # {name, reason}
    held: list[dict] = field(default_factory=list)  # {name, reason}


def _to_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _package_item(pkg: PackageResult, target: Candidate, needs_upgrade: bool, python: str | None) -> Item:
    flags = []
    if is_major_change(pkg.current_version, target.version):
        flags.append(FLAG_MAJOR)
    if target.compat_unknown:
        flags.append(FLAG_COMPAT_UNKNOWN)
    reason = f"현재 버전 취약점 최고 {pkg.severity}"
    if needs_upgrade:
        reason += f", Python {python} 이상에서만 안전한 버전 설치 가능"
    return Item("package", pkg.name, pkg.current_version, target.version, pkg.severity,
                None, reason, tuple(flags), needs_upgrade)


def build_items(
    packages: list[PackageResult],
    python_current: str,
    python_eol: dict | None,
    upgrade: UpgradePlan | None,
    os_label: str | None = None,
    os_version: str | None = None,
    os_eol: dict | None = None,
) -> ItemsResult:
    result = ItemsResult()
    upgrade_ok = upgrade is not None and upgrade.status == "ok"

    for pkg in packages:
        if pkg.unchecked_reason:
            result.unchecked.append({"name": pkg.name, "reason": pkg.unchecked_reason})
        elif pkg.severity is None:
            result.safe.append(pkg.name)
        elif pkg.violation and upgrade_ok and pkg.name in upgrade.targets:
            result.items.append(_package_item(pkg, upgrade.targets[pkg.name], True, upgrade.python))
        elif pkg.violation:
            reason = upgrade.reason if upgrade and upgrade.reason else "현재 Python에서 안전한 버전이 없음"
            result.held.append({"name": pkg.name, "reason": reason})
        elif pkg.target is None:
            result.held.append({"name": pkg.name, "reason": "설치 가능한 정식 버전이 없음"})
        else:
            result.items.append(_package_item(pkg, pkg.target, False, None))

    python_is_eol = bool(python_eol and python_eol.get("is_eol"))
    if python_is_eol or upgrade_ok:
        if upgrade_ok:
            reason = f"Python {upgrade.python}부터 안전한 버전 설치 가능 ({upgrade.eol_date}까지 지원)"
            target = upgrade.python
        else:
            reason = "지원 중인 버전으로 올림 필요"
            target = None
        if python_is_eol:
            reason = f"지원 종료({python_eol['eol_date']}), " + reason
        result.items.insert(0, Item("python_upgrade", "Python", python_current, target, "HIGH",
                                    _to_date(python_eol.get("eol_date") if python_eol else None), reason))

    if os_eol and os_eol.get("is_eol"):
        result.items.insert(0, Item("os", os_label or "OS", os_version or "", None, "HIGH",
                                    _to_date(os_eol.get("eol_date")),
                                    f"지원 종료({os_eol['eol_date']}), 지원 중인 다음 LTS로 올림 필요"))
    return result
