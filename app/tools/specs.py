"""Tool 명세 3종 (docs/spec.md "Tool 명세"). 이름·설명·종류·입력·출력·실패 코드.

입력·출력은 pydantic 모델로 정의한다. LLM에 넘기는 입력 형식과 레지스트리의 입력 검사가 모두 이 모델에서 나온다.
실제 API 호출 함수는 F3002~F3004에서 만들어 레지스트리에 함께 등록한다.
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.tools.base import (
    NO_EOL_DATE,
    PACKAGE_NOT_FOUND,
    PRODUCT_NOT_FOUND,
    TIMEOUT,
    UPSTREAM_ERROR,
)
from app.tools.registry import ToolSpec, to_llm_spec

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ── get_eol ──────────────────────────────────────────────
class EolInput(_Input):
    product: NonEmptyStr = Field(description="endoflife.date 제품 이름. 예: ubuntu, python")
    cycle: NonEmptyStr = Field(description="릴리스 줄기. 예: ubuntu는 20.04, python은 3.8")


class EolData(BaseModel):
    eol_date: date = Field(description="일반 지원 종료일")
    esm_date: date | None = Field(description="확장 지원(ESM) 종료일. 없으면 null")
    is_eol: bool
    lts: bool
    latest_patch: str | None = Field(description="그 줄기의 최신 패치 버전. 모르면 null")


GET_EOL = ToolSpec(
    name="get_eol",
    description="OS나 Python이 언제까지 지원되는지 알아야 할 때 쓴다. "
    "일반 지원 종료일, 확장 지원(ESM) 종료일, 지원 종료 여부, LTS 여부, 최신 패치 버전을 돌려준다.",
    kind="external",
    input_model=EolInput,
    output_model=EolData,
    error_codes=(PRODUCT_NOT_FOUND, NO_EOL_DATE, UPSTREAM_ERROR, TIMEOUT),
)


# ── get_vulns ────────────────────────────────────────────
class VulnsInput(_Input):
    name: NonEmptyStr = Field(description="PyPI 패키지 이름. 예: django")
    version: NonEmptyStr = Field(description="확인할 버전. 예: 2.2.0")


class Vuln(BaseModel):
    id: str
    severity: str | None = Field(description="CRITICAL/HIGH/MODERATE/LOW. 확인 못 하면 null(심각도 미상)")
    fixed_versions: list[str]


class VulnsData(BaseModel):
    count: int = Field(ge=0, description="중복(aliases)을 묶은 뒤 건수. 0건도 성공")
    vulns: list[Vuln]


GET_VULNS = ToolSpec(
    name="get_vulns",
    description="특정 PyPI 패키지 버전이 위험한지, 몇 버전에서 고쳐졌는지 알아야 할 때 쓴다. "
    "취약점 개수와 취약점별 등급·수정 버전을 돌려준다.",
    kind="external",
    input_model=VulnsInput,
    output_model=VulnsData,
    error_codes=(UPSTREAM_ERROR, TIMEOUT),
)


# ── get_package_versions ─────────────────────────────────
class PackageVersionsInput(_Input):
    name: NonEmptyStr = Field(description="PyPI 패키지 이름. 예: requests")


class PackageVersion(BaseModel):
    version: str
    requires_python: str | None = Field(description="비어 있으면 null (호환 미확인)")
    yanked: bool


class PackageVersionsData(BaseModel):
    latest: str
    versions: list[PackageVersion]


GET_PACKAGE_VERSIONS = ToolSpec(
    name="get_package_versions",
    description="업그레이드할 버전이 지금 Python에서 설치되는지 알아야 할 때 쓴다. "
    "패키지의 최신 버전과 버전별 requires_python·yanked 여부를 돌려준다.",
    kind="external",
    input_model=PackageVersionsInput,
    output_model=PackageVersionsData,
    error_codes=(PACKAGE_NOT_FOUND, UPSTREAM_ERROR, TIMEOUT),
)


TOOL_SPECS: list[ToolSpec] = [GET_EOL, GET_VULNS, GET_PACKAGE_VERSIONS]


def llm_tool_specs() -> list[dict]:
    """구현 함수 없이 명세만으로 LLM용 형식을 만든다 (Tool 선택 확인용)."""
    return [to_llm_spec(spec) for spec in TOOL_SPECS]
