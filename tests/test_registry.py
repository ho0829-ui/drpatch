"""F3001: Tool 공통 응답 형식과 레지스트리. 네트워크 없이 가짜 Tool 함수로 확인한다."""

import pytest

from app.tools.base import (
    INTERNAL_ERROR,
    INVALID_INPUT,
    UNKNOWN_TOOL,
    UPSTREAM_ERROR,
    fail,
    ok,
)
from app.tools.registry import ToolRegistry
from app.tools.specs import GET_EOL, GET_VULNS, TOOL_SPECS

EOL_DATA = {
    "eol_date": "2025-05-31",
    "esm_date": "2030-04-23",
    "is_eol": True,
    "lts": True,
    "latest_patch": "20.04.6",
    "label": "20.04 'Focal Fossa' (LTS)",
    "link": None,
    "queried_cycle": "20.04",
    "note": None,
}


def make_registry(eol_func) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(GET_EOL, eol_func)
    return reg


def test_ok_and_fail_shapes():
    assert ok({"a": 1}) == {"ok": True, "data": {"a": 1}}
    assert fail("X", "m") == {"ok": False, "error": {"code": "X", "message": "m"}}


def test_success_passes_validated_input_and_returns_data():
    seen = {}

    def eol(params):
        seen["product"], seen["cycle"] = params.product, params.cycle
        return ok(EOL_DATA)

    result = make_registry(eol).call("get_eol", {"product": " ubuntu ", "cycle": "20.04"})
    assert result == {"ok": True, "data": EOL_DATA}
    assert seen == {"product": "ubuntu", "cycle": "20.04"}  # 앞뒤 공백은 정리해서 넘김


def test_unknown_tool():
    result = make_registry(lambda p: ok(EOL_DATA)).call("get_weather", {})
    assert result["ok"] is False
    assert result["error"]["code"] == UNKNOWN_TOOL


@pytest.mark.parametrize(
    "args",
    [
        None,  # 입력 없음
        {"product": "ubuntu"},  # 필수 값 빠짐
        {"product": "", "cycle": "20.04"},  # 빈 값
        {"product": "   ", "cycle": "20.04"},  # 공백뿐
        {"product": "ubuntu", "cycle": "20.04", "extra": 1},  # 명세에 없는 값
        "ubuntu 20.04",  # dict가 아님
    ],
)
def test_invalid_input_does_not_call_tool(args):
    called = []
    result = make_registry(lambda p: called.append(p) or ok(EOL_DATA)).call("get_eol", args)
    assert result["ok"] is False
    assert result["error"]["code"] == INVALID_INPUT
    assert called == []


def test_invalid_input_message_names_fields_only():
    result = make_registry(lambda p: ok(EOL_DATA)).call("get_eol", {"product": "ubuntu"})
    assert "cycle" in result["error"]["message"]


def test_exception_inside_tool_becomes_internal_error():
    def boom(params):
        raise RuntimeError("secret detail")

    result = make_registry(boom).call("get_eol", {"product": "ubuntu", "cycle": "20.04"})
    assert result["ok"] is False
    assert result["error"]["code"] == INTERNAL_ERROR
    assert "secret detail" not in result["error"]["message"]


def test_tool_failure_is_passed_through():
    result = make_registry(lambda p: fail(UPSTREAM_ERROR, "응답 없음")).call(
        "get_eol", {"product": "ubuntu", "cycle": "20.04"}
    )
    assert result == {"ok": False, "error": {"code": UPSTREAM_ERROR, "message": "응답 없음"}}


@pytest.mark.parametrize(
    "bad_result",
    [
        None,
        {"eolFrom": "2025-05-31"},  # 응답 원본을 그대로 넘김
        {"ok": True},  # data 없음
        {"ok": False, "error": "문자열"},  # error 모양 틀림
    ],
)
def test_malformed_result_becomes_internal_error(bad_result):
    result = make_registry(lambda p: bad_result).call("get_eol", {"product": "ubuntu", "cycle": "20.04"})
    assert result["error"]["code"] == INTERNAL_ERROR


def test_data_not_matching_output_spec_becomes_internal_error():
    missing_eol_date = {k: v for k, v in EOL_DATA.items() if k != "eol_date"}
    result = make_registry(lambda p: ok(missing_eol_date)).call(
        "get_eol", {"product": "ubuntu", "cycle": "20.04"}
    )
    assert result["error"]["code"] == INTERNAL_ERROR


def test_null_allowed_where_spec_says_unknown():
    data = {**EOL_DATA, "esm_date": None, "latest_patch": None}
    result = make_registry(lambda p: ok(data)).call("get_eol", {"product": "python", "cycle": "3.8"})
    assert result == {"ok": True, "data": data}


def test_zero_vulns_is_success():
    reg = ToolRegistry()
    reg.register(GET_VULNS, lambda p: ok({"count": 0, "vulns": [], "truncated": False}))
    assert reg.call("get_vulns", {"name": "requests", "version": "2.34.2"}) == {
        "ok": True,
        "data": {"count": 0, "vulns": [], "truncated": False},
    }


def test_specs_for_llm_have_name_description_schema_only():
    reg = ToolRegistry()
    for spec in TOOL_SPECS:
        reg.register(spec, lambda p: ok({}))
    specs = reg.specs()
    assert [s["function"]["name"] for s in specs] == reg.names()
    eol = specs[0]["function"]
    assert set(eol) == {"name", "description", "parameters"}
    assert eol["parameters"]["required"] == ["product", "cycle"]
    assert eol["parameters"]["additionalProperties"] is False
    assert "title" not in eol["parameters"]


def test_duplicate_registration_is_rejected():
    reg = make_registry(lambda p: ok(EOL_DATA))
    with pytest.raises(ValueError):
        reg.register(GET_EOL, lambda p: ok(EOL_DATA))


def test_every_spec_lists_common_error_codes():
    for spec in TOOL_SPECS:
        assert {INVALID_INPUT, UNKNOWN_TOOL, INTERNAL_ERROR} <= set(spec.all_error_codes)
