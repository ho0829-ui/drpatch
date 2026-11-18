"""pip freeze로 만든 requirements.txt를 "조회할 패키지"와 "조회 제외(이유)"로 나눈다.

규칙은 docs/spec.md "requirements.txt 파싱 규칙". Tool이 아니라 실행 흐름이 직접 쓴다.
오류를 내지 않는다: 모든 줄은 조회되거나, 이유와 함께 제외되거나, (빈 줄·주석이면) 무시된다.
"""

import codecs
import re
from dataclasses import asdict, dataclass

REASON_NOT_PYPI = "PyPI 출처 아님"
REASON_NOT_EXACT = "정확한 버전 아님"
REASON_OPTION = "옵션 줄"
REASON_NO_VERSION = "버전 없음"
REASON_DUPLICATE = "중복"
REASON_INVALID = "형식 오류"

# 이름 [추가 기능] 나머지(버전 조건)
_REQUIREMENT = re.compile(
    r"^(?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*(?:\[[^\]]*\])?\s*(?P<spec>.*)$"
)
_EXACT = re.compile(r"^==\s*(?P<version>[A-Za-z0-9][A-Za-z0-9.+!_-]*)$")
_INLINE_COMMENT = re.compile(r"(^|\s)#.*$")  # pip 규칙: 맨 앞이거나 공백 뒤의 #부터 주석
_TRAILING_OPTIONS = re.compile(r"\s--?[A-Za-z][\w-]*(?:[=\s]\S+)?")  # --hash=... 등
_URL_HINTS = ("://", "git+", "hg+", "svn+", "bzr+", "file:")


@dataclass(frozen=True)
class Package:
    name: str
    version: str
    line_no: int
    marker: str | None = None  # 환경 표시. 있으면 "환경 조건 있음"


@dataclass(frozen=True)
class Excluded:
    line_no: int
    text: str
    reason: str


@dataclass(frozen=True)
class ParseResult:
    packages: list[Package]
    excluded: list[Excluded]

    def to_dict(self) -> dict:
        return {
            "packages": [asdict(p) for p in self.packages],
            "excluded": [asdict(e) for e in self.excluded],
        }


def normalize_name(name: str) -> str:
    """같은 패키지 판단용 (PEP 503): 소문자, -_. 묶음은 - 하나로."""
    return re.sub(r"[-_.]+", "-", name).lower()


def decode(raw: bytes) -> str:
    """BOM을 보고 UTF-8 / UTF-16을 읽는다. PowerShell의 `pip freeze >`는 UTF-16으로 저장한다."""
    if raw.startswith(codecs.BOM_UTF8):
        return raw[len(codecs.BOM_UTF8):].decode("utf-8", errors="replace")
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _logical_lines(text: str) -> list[tuple[int, str]]:
    """줄 끝 \\ 로 이어진 줄을 합친다. 줄 번호는 첫 줄 기준."""
    lines: list[tuple[int, str]] = []
    buffer, start = "", None
    for no, line in enumerate(text.splitlines(), 1):
        if start is None:
            start = no
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        lines.append((start, buffer + line))
        buffer, start = "", None
    if start is not None:
        lines.append((start, buffer))
    return lines


def _classify(line: str) -> tuple[str, str, str | None] | str:
    """(name, version, marker) 이거나 제외 이유."""
    if line.startswith(("-e", "--editable")):
        return REASON_NOT_PYPI
    if line.startswith("-"):
        return REASON_OPTION
    if any(hint in line for hint in _URL_HINTS) or " @ " in f" {line} " or line.startswith((".", "/")):
        return REASON_NOT_PYPI

    requirement, _, marker = line.partition(";")
    requirement = _TRAILING_OPTIONS.sub("", f" {requirement}").strip()
    marker = marker.strip() or None

    match = _REQUIREMENT.match(requirement)
    if not match:
        return REASON_INVALID
    spec = match["spec"].strip()
    if not spec:
        return REASON_NO_VERSION
    exact = _EXACT.match(spec)
    if exact and not spec.startswith("==="):
        return match["name"], exact["version"], marker
    if re.match(r"^(===|==|!=|~=|>=|<=|>|<)", spec):
        return REASON_NOT_EXACT
    return REASON_INVALID


def parse(text: str) -> ParseResult:
    packages: list[Package] = []
    excluded: list[Excluded] = []
    seen: set[str] = set()

    for line_no, original in _logical_lines(text):
        line = _INLINE_COMMENT.sub("", original).strip()
        if not line:
            continue  # 빈 줄·주석 줄
        shown = original.strip()
        result = _classify(line)
        if isinstance(result, str):
            excluded.append(Excluded(line_no, shown, result))
            continue
        name, version, marker = result
        key = normalize_name(name)
        if key in seen:
            excluded.append(Excluded(line_no, shown, REASON_DUPLICATE))
            continue
        seen.add(key)
        packages.append(Package(name, version, line_no, marker))

    return ParseResult(packages, excluded)


def parse_bytes(raw: bytes) -> ParseResult:
    return parse(decode(raw))
