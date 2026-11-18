"""필요한 가장 낮은 Python 구하기 + Python 업그레이드 재계획 (spec "재계획").

get_vulns·get_eol은 함수로 넘겨받는다 → 테스트는 가짜 함수, 실제 흐름은 레지스트리를 감싼 함수.
같은 (패키지, 버전)은 한 번만 묻는다 (F3009: 이미 확보한 결과 재사용).

패키지마다 따로 "안전한 버전이 처음 생기는 Python 줄기"를 구하고, 그중 가장 높은 줄기를 Python 후보로 한다.
조회가 실패한 패키지는 "확인 못 함"으로 빼고 나머지는 계속 진행한다 (2일차 리뷰 반영).
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.agent.planner.versions import Candidate, mentioned_minors, pick_latest

# (name, version) -> 취약점 건수. None = 확인 못 함 (Tool 실패)
VulnCheck = Callable[[str, str], int | None]
# "3.11" -> {"eol_date": "...", "is_eol": bool}. None = 확인 못 함 (없는 줄기·Tool 실패)
EolCheck = Callable[[str], dict | None]

MAX_REPLANS = 3
UNRESOLVED_UNCHECKED = "unchecked"  # 취약점 조회 실패로 판단 못 함
UNRESOLVED_NONE = "none"  # 어떤 줄기에서도 취약점 없는 버전이 없음


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
    unresolved: dict[str, str] = field(default_factory=dict)  # 업그레이드로도 못 정한 패키지 → 이유 종류

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


def package_min_minor(
    name: str, versions: list[dict], start: int, end: int, check_vulns: VulnCheck
) -> tuple[int | None, bool]:
    """(취약점 0건 최신 버전이 처음 생기는 줄기, 조회 실패를 만났는지). 목표 버전이 바뀔 때만 조회한다."""
    previous, saw_unknown = None, False
    for minor in range(start, end + 1):
        candidate = pick_latest(versions, f"3.{minor}")
        if candidate is None or candidate.version == previous:
            continue
        previous = candidate.version
        count = check_vulns(name, candidate.version)
        if count == 0:
            return minor, saw_unknown
        if count is None:
            saw_unknown = True
    return None, saw_unknown


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
    major, minor_text = current_python.split(".")[:2]
    start = int(minor_text) + 1 if major == "3" else 0  # Python 2.x면 3.0부터
    # 어디까지 올려 볼지: 조건에 나오는 가장 높은 줄기 + 1 (>3.9, ~=3.10, ==3.11.* 모두 다음 줄기에서 열림)
    mentioned = [m for v in packages.values() for m in mentioned_minors(v)]
    bound = max([start, *(m + 1 for m in mentioned)])

    plan = UpgradePlan(status="hold")
    active = dict(packages)
    search_from = start
    while plan.replans < max_replans:
        minima: dict[str, int] = {}
        for name, versions in active.items():
            minor, saw_unknown = package_min_minor(name, versions, search_from, max(bound, search_from), check_vulns)
            if minor is None:
                plan.unresolved[name] = UNRESOLVED_UNCHECKED if saw_unknown else UNRESOLVED_NONE
            else:
                minima[name] = minor
        if not minima:
            plan.reason = ("취약점 정보를 확인하지 못해 필요한 Python을 판단하지 못했습니다"
                           if UNRESOLVED_UNCHECKED in plan.unresolved.values()
                           else "어떤 Python 줄기에서도 취약점 없는 버전을 찾지 못했습니다")
            return plan

        minor = max(minima.values())
        python = f"3.{minor}"
        targets: dict[str, Candidate] = {}
        for name in minima:  # 후보 줄기에서 다시 고른 버전도 0건인지 (대부분 이미 조회한 것)
            candidate = pick_latest(packages[name], python)
            count = check_vulns(name, candidate.version) if candidate else None
            if candidate is not None and count == 0:
                targets[name] = candidate
            else:
                plan.unresolved[name] = UNRESOLVED_NONE if count else UNRESOLVED_UNCHECKED
        active = {name: packages[name] for name in targets}
        if not targets:
            plan.reason = "후보 Python에서 안전한 버전을 다시 확인하지 못했습니다"
            return plan

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
