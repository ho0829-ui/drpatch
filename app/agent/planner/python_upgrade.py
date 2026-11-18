"""필요한 가장 낮은 Python 구하기 + Python 업그레이드 재계획 (spec "재계획").

get_vulns·get_eol은 함수로 넘겨받는다 → 테스트는 가짜 함수, 실제 흐름은 레지스트리를 감싼 함수.
같은 (패키지, 버전)은 한 번만 묻는다 (F3009: 이미 확보한 결과 재사용).
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.agent.planner.versions import Candidate, lower_bound_minors, pick_latest

# (name, version) -> 취약점 건수. None = 확인 못 함 (Tool 실패)
VulnCheck = Callable[[str, str], int | None]
# "3.11" -> {"eol_date": "...", "is_eol": bool}. None = 확인 못 함 (없는 줄기·Tool 실패)
EolCheck = Callable[[str], dict | None]

MAX_REPLANS = 3


@dataclass
class Attempt:
    python: str
    is_eol: bool | None
    eol_date: str | None
    reason: str


@dataclass
class UpgradePlan:
    status: str  # "ok" | "hold"
    python: str | None = None
    eol_date: str | None = None
    targets: dict[str, Candidate] = field(default_factory=dict)
    attempts: list[Attempt] = field(default_factory=list)  # 재계획 기록 (로그·응답에 이유로 씀)
    reason: str | None = None

    @property
    def replans(self) -> int:
        return len(self.attempts)


def _cached(check: VulnCheck) -> VulnCheck:
    memo: dict[tuple[str, str], int | None] = {}

    def wrapper(name: str, version: str) -> int | None:
        key = (name, version)
        if key not in memo:
            memo[key] = check(name, version)
        return memo[key]

    return wrapper


def find_safe_python(
    packages: dict[str, list[dict]], start_minor: int, end_minor: int, check_vulns: VulnCheck
) -> tuple[int, dict[str, Candidate]] | None:
    """start~end 줄기를 하나씩 올리며, 모든 패키지의 '그 줄기 최신 정식 버전'이 취약점 0건인 첫 줄기."""
    for minor in range(start_minor, end_minor + 1):
        python = f"3.{minor}"
        targets: dict[str, Candidate] = {}
        for name, versions in packages.items():
            candidate = pick_latest(versions, python)
            if candidate is None or check_vulns(name, candidate.version) != 0:
                break  # 이 줄기에선 안전한 버전이 없음 (확인 못 한 것도 안전하다고 보지 않음)
            targets[name] = candidate
        else:
            return minor, targets
    return None


def plan_python_upgrade(
    current_python: str,
    packages: dict[str, list[dict]],
    check_vulns: VulnCheck,
    check_eol: EolCheck,
    max_replans: int = MAX_REPLANS,
) -> UpgradePlan:
    """packages = 호환 제약을 위반한 패키지 → get_package_versions의 versions.

    재계획 1회 = Python 후보 줄기 하나를 정해 get_eol로 확인하는 것 (줄기 훑기의 get_vulns는 세지 않음).
    """
    check_vulns = _cached(check_vulns)
    current_minor = int(current_python.split(".")[1])
    # 줄기를 어디까지 올려 볼지: requires_python 하한이 가장 높은 줄기까지. 그 위에선 최신 버전이 더 바뀌지 않는다.
    bound = max([current_minor + 1, *(m for v in packages.values() for m in lower_bound_minors(v))])

    plan = UpgradePlan(status="hold")
    search_from = current_minor + 1
    while plan.replans < max_replans:
        found = find_safe_python(packages, search_from, max(bound, search_from), check_vulns)
        if found is None:
            plan.reason = "어떤 Python 줄기에서도 취약점 없는 버전을 찾지 못했습니다"
            return plan
        minor, targets = found
        python = f"3.{minor}"
        eol = check_eol(python)
        if eol is None:
            plan.attempts.append(Attempt(python, None, None, "지원 종료일을 확인하지 못함"))
            plan.reason = f"Python {python}의 지원 기간을 확인하지 못했습니다"
            return plan
        if eol["is_eol"]:
            plan.attempts.append(Attempt(python, True, eol["eol_date"], f"{eol['eol_date']}에 이미 지원 종료"))
            search_from = minor + 1
            continue
        plan.attempts.append(Attempt(python, False, eol["eol_date"], f"{eol['eol_date']}까지 지원"))
        plan.status, plan.python, plan.eol_date, plan.targets = "ok", python, eol["eol_date"], targets
        return plan

    plan.reason = f"재계획 상한({max_replans}회)에 도달했습니다"
    return plan
