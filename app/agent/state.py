"""그래프가 주고받는 값: 세션 조건(Memory)과 한 번의 요청 상태."""

import re
from datetime import date
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class Conditions(BaseModel):
    """세션 조건 (spec Memory). API 결과는 넣지 않는다."""

    packages: list[dict] = Field(default_factory=list)  # [{name, version}] — 파일 업로드에서
    excluded: list[dict] = Field(default_factory=list)  # [{line_no, text, reason}]
    os_name: str | None = None  # ubuntu
    os_version: str | None = None  # 20.04
    python_version: str | None = None  # 3.8
    capacity: int | None = None  # N
    first_date: date | None = None
    window_start: str | None = None  # "22:00"
    window_end: str | None = None
    interval_days: int | None = None


# 계획에 꼭 필요한 값과 되물을 때 쓰는 이름 (spec "빠진 입력")
REQUIRED = [
    ("packages", "requirements.txt 파일 (pip freeze로 만든 것)"),
    ("os", "OS와 버전 (예: Ubuntu 20.04 / macOS 15 / Windows 11 24H2)"),
    ("python_version", "Python 버전 (예: 3.8)"),
    ("capacity", "한 번에 처리할 개수 (예: 5개까지)"),
    ("first_date", "첫 점검 날짜 (예: 11/21)"),
    ("interval_days", "점검 간격 (매주 / 격주 / 매월 / N일)"),
]

OS_NAME_ALIASES = {
    "맥": "macos",
    "맥북": "macos",
    "맥os": "macos",
    "mac": "macos",
    "macos": "macos",
    "mac os": "macos",
    "os x": "macos",
    "osx": "macos",
    "darwin": "macos",
    "윈도우": "windows",
    "윈도우즈": "windows",
    "윈도": "windows",
    "windows": "windows",
    "win": "windows",
    "우분투": "ubuntu",
    "ubuntu": "ubuntu",
}

MACOS_CODENAMES = {
    "타호": "26",
    "tahoe": "26",
    "세쿼이아": "15",
    "세콰이어": "15",
    "sequoia": "15",
    "소노마": "14",
    "sonoma": "14",
    "벤투라": "13",
    "벤추라": "13",
    "ventura": "13",
    "몬터레이": "12",
    "몬테레이": "12",
    "monterey": "12",
    "빅서": "11",
    "big sur": "11",
    "bigsur": "11",
}


def missing_inputs(c: Conditions) -> list[str]:
    values = {
        "packages": c.packages,
        "os": c.os_name and c.os_version,
        "python_version": c.python_version,
        "capacity": c.capacity,
        "first_date": c.first_date,
        "interval_days": c.interval_days,
    }
    return [key for key, _ in REQUIRED if not values[key]]


SCHEDULE_KEYS = ("capacity", "first_date", "interval_days")  # 회차로 나눌 때만 필요한 값


def tool_inputs_missing(missing: list[str]) -> bool:
    """Tool을 부르는 데 필요한 값(파일·OS·Python)이 빠졌는지. 일정만 빠졌으면 False."""
    return any(key not in SCHEDULE_KEYS for key in missing)


def schedule_ask_message(missing: list[str]) -> str:
    labels = dict(REQUIRED)
    lines = "\n".join(f"- {labels[key]}" for key in missing if key in SCHEDULE_KEYS)
    return f"흠, 회차 일정을 잡으려면 몇 가지가 더 필요합니다.\n{lines}"


def _os_missing_label(os_name: str | None) -> str:
    if not os_name:
        return dict(REQUIRED)["os"]
    if os_name == "macos":
        return "macOS 버전 (예: macOS 15 — 이 Mac에 관하여에서 확인)"
    if os_name == "windows":
        return "Windows 버전과 기능 업데이트 (예: Windows 11 24H2 — 설정 > 시스템 > 정보)"
    if os_name == "ubuntu":
        return "Ubuntu 버전 (예: Ubuntu 20.04)"
    return f"{os_name} 버전"


def ask_message(missing: list[str], conditions: Conditions | None = None) -> str:
    """빠진 것만 묻는 고정 문장 (spec v1.9·v1.17: 되묻기는 코드가, 박사님 말투)."""
    labels = dict(REQUIRED)
    os_name = conditions.os_name if conditions else None
    if missing == ["os"] and os_name:
        if os_name == "macos":
            return "맥이시군요. 버전만 알려 주시죠 (예: macOS 15 — 이 Mac에 관하여에서 확인)."
        if os_name == "windows":
            return "윈도우시군요. 버전과 기능 업데이트만 알려 주시죠 (예: Windows 11 24H2 — 설정 > 시스템 > 정보)."
        if os_name == "ubuntu":
            return "우분투시군요. 버전만 알려 주시죠 (예: Ubuntu 20.04)."
        return f"{os_name}이시군요. 버전만 알려 주시죠."
    lines = "\n".join(
        f"- {_os_missing_label(os_name) if key == 'os' else labels[key]}"
        for key in missing
    )
    return f"흠, 차트를 채우려면 몇 가지가 더 필요합니다.\n{lines}"


def normalize_os_name(name: str | None) -> str | None:
    """OS 이름 정규화: 맥·맥북·macOS·OS X → macos, 윈도우·Windows → windows."""
    if not name:
        return None
    cleaned = re.sub(r"\s+", " ", name.strip()).lower()
    if not cleaned:
        return None
    return OS_NAME_ALIASES.get(cleaned, cleaned)


def normalize_os_version(os_name: str | None, version: str | None) -> str | None:
    """OS별 버전 정규화 (spec v1.17). 알 수 없거나 불완전하면 None(= 되묻기)."""
    if not version:
        return None
    v = re.sub(r"\s+", " ", version.strip())
    if not v:
        return None

    if os_name == "ubuntu":
        v = re.sub(r"^ubuntu\s+", "", v, flags=re.I)
        if re.fullmatch(r"\d{2}", v):
            return f"{v}.04"
        return v

    if os_name == "macos":
        v = re.sub(r"^(?:mac\s*os|os\s*x|osx|맥\s*os|맥북|맥)\s+", "", v, flags=re.I).strip()
        if v.lower() in MACOS_CODENAMES:
            return MACOS_CODENAMES[v.lower()]
        m = re.fullmatch(r"(\d+)(?:\.\d+)*", v)
        return m[1] if m else None

    if os_name == "windows":
        v = re.sub(r"^(?:windows|윈도우즈|윈도우|윈도|win)\s+", "", v, flags=re.I).strip()
        if re.fullmatch(r"(?:10|11)-\d{2}h[12]-[we]", v, flags=re.I):
            return v.lower()
        m = re.fullmatch(
            r"(10|11)[\s\-]+(\d{2}h[12])(?:\s+(home|pro|workstation|enterprise|education|iot|w|e))?",
            v,
            flags=re.I,
        )
        if not m:
            return None  # 주 버전("11")만 있으면 기능 업데이트(24H2 등)를 되묻는다
        major, feat, edition = m[1], m[2].lower(), (m[3] or "").lower()
        suffix = "e" if edition in {"enterprise", "education", "e"} else "w"
        return f"{major}-{feat}-{suffix}"

    return v


def normalize_python(version: str | None) -> str | None:
    """'3.8.10' → '3.8'. 2.x도 받는다(지원 종료 Python으로 처리). 형식이 틀리면 None (= 빠진 입력으로 되묻기)."""
    if not version:
        return None
    m = re.fullmatch(r"\s*([23])\.(\d+)(?:\.\d+)?\s*", version)
    return f"{m[1]}.{m[2]}" if m else None


class AgentState(TypedDict, total=False):
    message: str
    today: date
    last_turn: dict | None  # 직전 요청·응답 (F3010)
    conditions: Conditions
    intent: str  # plan | fact | confirm | other
    intent_reason: str
    confirm_rounds: list[int] | None  # "1회차 확정해줘" → [1], 없으면 전체
    missing: list[str]
    tool_plan: list[str]
    tool_plan_reason: str
    results: dict[str, Any]  # 조회 결과 (eol_os, eol_python, vulns{name}, versions{name})
    tools_down: bool  # 모든 Tool이 같은 이유로 실패 → 바로 안내
    package_results: list[Any]  # planner.items.PackageResult
    violations: list[str]
    replan_strategy: str
    replan_reason: str
    upgrade: Any  # planner.python_upgrade.UpgradePlan | None
    plan: dict[str, Any]  # 회차 계획 (화면·저장용 dict)
    answer: str
