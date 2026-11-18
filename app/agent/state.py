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
    ("os", "OS와 버전 (예: Ubuntu 20.04)"),
    ("python_version", "Python 버전 (예: 3.8)"),
    ("capacity", "한 번에 처리할 개수 (예: 5개까지)"),
    ("first_date", "첫 점검 날짜 (예: 11/21)"),
    ("interval_days", "점검 간격 (매주 / 격주 / 매월 / N일)"),
]


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


def ask_message(missing: list[str]) -> str:
    """빠진 것만 묻는 고정 문장 (spec v1.9: 되묻기는 코드가)."""
    labels = dict(REQUIRED)
    lines = "\n".join(f"- {labels[key]}" for key in missing)
    return f"계획을 세우려면 아래 내용이 더 필요해요.\n{lines}"


def normalize_os_version(os_name: str | None, version: str | None) -> str | None:
    """'우분투 20' → 20.04 (Ubuntu LTS는 .04)."""
    if not version:
        return None
    version = version.strip()
    if os_name == "ubuntu" and re.fullmatch(r"\d{2}", version):
        return f"{version}.04"
    return version


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
