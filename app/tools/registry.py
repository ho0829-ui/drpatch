"""Tool 명세를 이름으로 등록하고, 이름으로 안전하게 부르는 레지스트리 (F3001).

- LLM에는 이름·설명·입력 형식만 넘긴다 (`specs()`).
- `call()`은 이름 확인 → 입력 검사 → 실행 → 출력 모양 확인 순서로 돌고, 어떤 경우에도 예외를 던지지 않는다.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from app.tools.base import (
    COMMON_ERROR_CODES,
    INTERNAL_ERROR,
    INVALID_INPUT,
    UNKNOWN_TOOL,
    fail,
    ok,
)

ToolFunc = Callable[[Any], dict]


@dataclass(frozen=True)
class ToolSpec:
    """Tool 하나의 명세. 입력·출력 구조는 pydantic 모델 하나씩으로 정의한다."""

    name: str
    description: str  # Agent에게 주는 "언제 쓰나" 설명
    kind: Literal["external", "local"]
    input_model: type[BaseModel]
    output_model: type[BaseModel]  # 성공 시 data 모양
    error_codes: tuple[str, ...]  # 이 Tool이 직접 내는 실패 코드 (공통 코드 제외)

    @property
    def all_error_codes(self) -> tuple[str, ...]:
        return self.error_codes + COMMON_ERROR_CODES


def _clean_schema(schema: dict) -> dict:
    """pydantic이 붙이는 title을 빼서 LLM에 넘길 입력 형식을 짧게 만든다."""
    schema = {k: v for k, v in schema.items() if k != "title"}
    if "properties" in schema:
        schema["properties"] = {
            name: {k: v for k, v in prop.items() if k != "title"}
            for name, prop in schema["properties"].items()
        }
    return schema


def to_llm_spec(spec: ToolSpec) -> dict:
    """OpenAI function 형식. ChatOpenAI.bind_tools()에 그대로 넘길 수 있다."""
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": _clean_schema(spec.input_model.model_json_schema()),
        },
    }


def _input_error_message(e: ValidationError) -> str:
    fields = sorted({".".join(str(p) for p in err["loc"]) or "(입력)" for err in e.errors()})
    return f"입력을 확인하세요: {', '.join(fields)}"


def _is_result(value: Any) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("ok"), bool):
        return False
    if value["ok"]:
        return "data" in value
    error = value.get("error")
    return isinstance(error, dict) and isinstance(error.get("code"), str)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolSpec, ToolFunc]] = {}

    def register(self, spec: ToolSpec, func: ToolFunc) -> None:
        if spec.name in self._tools:
            raise ValueError(f"이미 등록된 Tool: {spec.name}")  # 개발 중 실수라 예외로 알림
        self._tools[spec.name] = (spec, func)

    def names(self) -> list[str]:
        return list(self._tools)

    def get_spec(self, name: str) -> ToolSpec | None:
        entry = self._tools.get(name)
        return entry[0] if entry else None

    def specs(self) -> list[dict]:
        return [to_llm_spec(spec) for spec, _ in self._tools.values()]

    def call(self, name: str, args: Any = None) -> dict:
        entry = self._tools.get(name)
        if entry is None:
            return fail(UNKNOWN_TOOL, f"등록되지 않은 Tool입니다: {name}")
        spec, func = entry

        try:
            params = spec.input_model.model_validate(args if args is not None else {})
        except ValidationError as e:
            return fail(INVALID_INPUT, _input_error_message(e))

        try:
            result = func(params)
        except Exception as e:  # Tool이 놓친 예외도 밖으로 내보내지 않는다
            return fail(INTERNAL_ERROR, f"{name} 실행 중 오류: {type(e).__name__}")

        if not _is_result(result):
            return fail(INTERNAL_ERROR, f"{name}의 응답 모양이 약속과 다릅니다")
        if not result["ok"]:
            return result
        try:
            data = spec.output_model.model_validate(result["data"])
        except ValidationError:
            return fail(INTERNAL_ERROR, f"{name}의 data 구조가 명세와 다릅니다")
        return ok(data.model_dump(mode="json"))
