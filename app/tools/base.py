"""모든 Tool이 쓰는 응답 모양과 실패 코드 (F3001).

성공: {"ok": True, "data": {...}}
실패: {"ok": False, "error": {"code": "...", "message": "..."}}
Tool은 예외를 밖으로 던지지 않고 항상 이 둘 중 하나를 돌려준다.
"""

from typing import Any

# 공통 실패 코드: 레지스트리가 붙인다 (spec "Tool 명세" 공통 실패 코드)
INVALID_INPUT = "INVALID_INPUT"
UNKNOWN_TOOL = "UNKNOWN_TOOL"
INTERNAL_ERROR = "INTERNAL_ERROR"

# Tool별 실패 코드: Tool 구현이 붙인다
PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
NO_EOL_DATE = "NO_EOL_DATE"
PACKAGE_NOT_FOUND = "PACKAGE_NOT_FOUND"
UPSTREAM_ERROR = "UPSTREAM_ERROR"
TIMEOUT = "TIMEOUT"

COMMON_ERROR_CODES = (INVALID_INPUT, UNKNOWN_TOOL, INTERNAL_ERROR)


def ok(data: Any) -> dict:
    return {"ok": True, "data": data}


def fail(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def safe_parse(parse, *args, **kwargs) -> dict:
    """응답 형식이 예상과 달라 해석 중 오류가 나면 UPSTREAM_ERROR (리뷰 #7: 예외를 밖으로 던지지 않음)."""
    try:
        return parse(*args, **kwargs)
    except (AttributeError, TypeError, KeyError, ValueError, IndexError):
        return fail(UPSTREAM_ERROR, "외부 API 응답 형식이 예상과 다릅니다")
