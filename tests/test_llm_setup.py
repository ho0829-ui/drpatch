"""네트워크 없이 LLM 설정과 Tool 명세 형식을 확인한다. 실제 호출은 scripts/check_llm.py."""

import pytest

from app import llm as llm_module
from app.llm import REQUIRED_ENV, LLMConfigError, get_llm, load_llm_config
from app.tools.specs import TOOL_SPECS, llm_tool_specs


@pytest.fixture
def no_dotenv(monkeypatch):
    """실제 .env 파일을 읽지 않게 막는다."""
    monkeypatch.setattr(llm_module, "load_dotenv", lambda: None)


def test_missing_env_names_only(monkeypatch, no_dotenv):
    for name in REQUIRED_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GMS_KEY", "secret-value")
    with pytest.raises(LLMConfigError) as e:
        load_llm_config()
    assert "GMS_BASE_URL" in str(e.value) and "LLM_MODEL" in str(e.value)
    assert "secret-value" not in str(e.value)


def test_get_llm_uses_env(monkeypatch, no_dotenv):
    monkeypatch.setenv("GMS_KEY", "k")
    monkeypatch.setenv("GMS_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    llm = get_llm()
    assert llm.model_name == "test-model"
    assert llm.openai_api_base == "https://example.invalid/v1"
    # 추론형 모델 대응: temperature는 보내지 않고, Tool 호출은 Responses API로
    assert llm.temperature is None
    assert llm.use_responses_api is True


def test_tool_specs_match_spec():
    specs = llm_tool_specs()
    names = [s["function"]["name"] for s in specs]
    assert names == ["get_eol", "get_vulns", "get_package_versions"]
    required = {s["function"]["name"]: s["function"]["parameters"]["required"] for s in specs}
    assert all(s.kind == "external" for s in TOOL_SPECS)
    assert required == {
        "get_eol": ["product", "cycle"],
        "get_vulns": ["name", "version"],
        "get_package_versions": ["name"],
    }


def test_tool_specs_bind_without_network(monkeypatch, no_dotenv):
    monkeypatch.setenv("GMS_KEY", "k")
    monkeypatch.setenv("GMS_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    bound = get_llm().bind_tools(llm_tool_specs())
    sent = bound.kwargs["tools"]
    assert [t["function"]["name"] for t in sent] == ["get_eol", "get_vulns", "get_package_versions"]
