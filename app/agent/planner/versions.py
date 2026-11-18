"""버전 판단 (spec "목표 버전 고르기"). 순수 함수: 네트워크·LLM 없음.

입력 `versions`는 get_package_versions의 data["versions"] 모양: [{version, requires_python, yanked}].
"""

from dataclasses import dataclass

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


def parse_version(text: str) -> Version | None:
    try:
        return Version(text)
    except InvalidVersion:
        return None


def is_final(text: str) -> bool:
    """정식 버전인지: rc·a·b(시험판)와 dev는 아님. post(사후 수정)는 정식으로 본다."""
    v = parse_version(text)
    return v is not None and not v.is_prerelease and not v.is_devrelease


def python_allows(requires_python: str | None, python: str) -> bool | None:
    """True/False = 판정함, None = 판정 못 함(값이 비었거나 형식이 틀림 → "호환 미확인")."""
    if not requires_python:
        return None
    try:
        return SpecifierSet(requires_python).contains(python, prereleases=True)
    except InvalidSpecifier:
        return None


@dataclass(frozen=True)
class Candidate:
    version: str
    compat_unknown: bool  # requires_python을 확인 못 함 ("호환 미확인")


def pick_latest(versions: list[dict], python: str) -> Candidate | None:
    """python에서 설치 가능하고 yanked가 아닌 정식 버전 중 가장 최신. 없으면 None."""
    best: tuple[Version, Candidate] | None = None
    for entry in versions:
        if entry.get("yanked") or not is_final(entry["version"]):
            continue
        allowed = python_allows(entry.get("requires_python"), python)
        if allowed is False:
            continue
        v = parse_version(entry["version"])
        if best is None or v > best[0]:
            best = (v, Candidate(entry["version"], compat_unknown=allowed is None))
    return best[1] if best else None


def is_newer(target: str, current: str) -> bool:
    """target이 current보다 높은 버전인지. current를 해석할 수 없으면 True(비교 못 함 → 막지 않음)."""
    t, c = parse_version(target), parse_version(current)
    if c is None:
        return True
    return t is not None and t > c


def is_major_change(current: str, target: str) -> bool:
    a, b = parse_version(current), parse_version(target)
    return a is not None and b is not None and a.major != b.major


def mentioned_minors(versions: list[dict], major: int = 3) -> set[int]:
    """requires_python 조건에 나오는 3.N의 N 모음 (연산자 무관: >=, >, ~=, ==3.N.*, !=3.N.* 등).
    줄기를 어디까지 올려 볼지 정할 때 쓴다 → 가장 큰 N + 1까지 보면 모든 조건이 열리는 줄기를 지나간다."""
    minors = set()
    for entry in versions:
        try:
            spec = SpecifierSet(entry.get("requires_python") or "")
        except InvalidSpecifier:
            continue
        for s in spec:
            v = parse_version(s.version.replace(".*", ""))
            if v is not None and v.major == major:
                minors.add(v.minor)
    return minors
