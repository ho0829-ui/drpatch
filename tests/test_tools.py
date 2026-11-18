"""F3002~F3004: Tool 3종을 저장된 실제 응답(tests/fixtures)으로 확인한다. 네트워크를 쓰지 않는다.

모두 기본 레지스트리(build_registry)를 거쳐 부른다 → 출력이 명세(pydantic 모델)와 맞는지도 함께 확인된다.
"""

import json
from pathlib import Path

import pytest
import requests

from app.tools import http
from app.tools.base import (
    NO_EOL_DATE,
    PACKAGE_NOT_FOUND,
    PRODUCT_NOT_FOUND,
    TIMEOUT,
    UPSTREAM_ERROR,
)
from app.tools.default import build_registry
from app.tools.eol import normalize_cycle
from app.tools.vulns import MAX_PAGES

FIX = Path(__file__).parent / "fixtures"


def fixture(name: str) -> tuple[int, object]:
    """0일차 저장본은 본문만, 실패 응답 저장본은 {status, body} 형식."""
    data = json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))
    if isinstance(data, dict) and set(data) == {"status", "body", "text"}:
        return data["status"], data["body"]
    return 200, data


class FakeTransport:
    """URL(또는 요청 본문) → 응답. 부른 기록을 남긴다."""

    def __init__(self, responder):
        self.responder = responder
        self.calls = []

    def __call__(self, method, url, json_body, timeout):
        self.calls.append((method, url, json_body))
        result = self.responder(method, url, json_body)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def use(monkeypatch):
    def install(responder):
        fake = FakeTransport(responder)
        monkeypatch.setattr(http, "transport", fake)
        return fake

    return install


@pytest.fixture
def registry():
    return build_registry()


# ── get_eol ──────────────────────────────────────────────
def test_eol_ubuntu(use, registry):
    fake = use(lambda m, url, b: fixture("eol_ubuntu_20.04"))
    result = registry.call("get_eol", {"product": "ubuntu", "cycle": "20.04"})
    assert result["ok"] is True
    data = result["data"]
    assert data["eol_date"] == "2025-05-31"
    assert data["esm_date"] == "2030-04-23"
    assert data["is_eol"] is True and data["lts"] is True
    assert data["latest_patch"] == "20.04.6"
    assert data["label"] == "20.04 'Focal Fossa' (LTS)"
    assert data["link"].startswith("https://")
    assert data["note"] is None
    assert fake.calls[0][1] == "https://endoflife.date/api/v1/products/ubuntu/releases/20.04"


def test_eol_without_esm_is_null_not_invented(use, registry):
    use(lambda m, url, b: fixture("eol_python_3.8"))
    data = registry.call("get_eol", {"product": "python", "cycle": "3.8"})["data"]
    assert data["eol_date"] == "2024-10-07"
    assert data["esm_date"] is None


def test_eol_not_yet_ended(use, registry):
    use(lambda m, url, b: fixture("eol_python_3.14"))
    data = registry.call("get_eol", {"product": "python", "cycle": "3.14"})["data"]
    assert data["is_eol"] is False
    assert data["eol_date"] == "2030-10-31"


def test_eol_patch_version_is_normalized_and_disclosed(use, registry):
    fake = use(lambda m, url, b: fixture("eol_python_3.8"))
    data = registry.call("get_eol", {"product": "Python", "cycle": "3.8.10"})["data"]
    assert fake.calls[0][1].endswith("/python/releases/3.8")
    assert data["queried_cycle"] == "3.8"
    assert "3.8.10" in data["note"] and "3.8" in data["note"]


@pytest.mark.parametrize(
    "product,cycle,expected",
    [("ubuntu", "20.04.6", "20.04"), ("python", "3.12", "3.12"), ("debian", "12.5", "12.5")],
)
def test_normalize_cycle(product, cycle, expected):
    assert normalize_cycle(product, cycle) == expected


@pytest.mark.parametrize("name", ["eol_no_product", "eol_no_cycle"])
def test_eol_not_found(use, registry, name):
    use(lambda m, url, b: fixture(name))
    result = registry.call("get_eol", {"product": "ubuntu", "cycle": "99.99"})
    assert result["error"]["code"] == PRODUCT_NOT_FOUND


def test_eol_without_eol_date(use, registry):
    status, body = fixture("eol_ubuntu_20.04")
    body = {"result": {**body["result"], "eolFrom": None}}
    use(lambda m, url, b: (status, body))
    assert registry.call("get_eol", {"product": "ubuntu", "cycle": "20.04"})["error"]["code"] == NO_EOL_DATE


# ── get_vulns ────────────────────────────────────────────
def test_vulns_grouped_by_aliases(use, registry):
    fake = use(lambda m, url, b: fixture("osv_requests_2.19.0"))
    data = registry.call("get_vulns", {"name": "requests", "version": "2.19.0"})["data"]
    assert data["count"] == 5  # 원래 10건 → GHSA·PYSEC 묶어서 5건
    assert data["truncated"] is False
    assert {v["severity"] for v in data["vulns"]} == {"HIGH", "MODERATE"}
    high = next(v for v in data["vulns"] if v["severity"] == "HIGH")
    assert high["fixed_versions"] == ["2.20.0"]
    method, url, body = fake.calls[0]
    assert (method, url) == ("POST", "https://api.osv.dev/v1/query")
    assert body == {"package": {"name": "requests", "ecosystem": "PyPI"}, "version": "2.19.0"}


def test_vulns_django_many_fixed_versions(use, registry):
    use(lambda m, url, b: fixture("osv_django_2.2.0"))
    data = registry.call("get_vulns", {"name": "django", "version": "2.2.0"})["data"]
    assert data["count"] == 43
    assert "CRITICAL" in {v["severity"] for v in data["vulns"]}
    assert all(v["fixed_versions"] for v in data["vulns"])


def test_vulns_severity_taken_from_alias_that_has_it(use, registry):
    use(lambda m, url, b: fixture("osv_requests_2.32.5"))
    data = registry.call("get_vulns", {"name": "requests", "version": "2.32.5"})["data"]
    assert data["count"] == 1  # GHSA(MODERATE) + PYSEC(등급 없음) → 1건
    assert data["vulns"][0]["severity"] == "MODERATE"


@pytest.mark.parametrize("name", ["osv_requests_2.34.2", "osv_no_package"])
def test_zero_vulns_is_success(use, registry, name):
    use(lambda m, url, b: fixture(name))
    result = registry.call("get_vulns", {"name": "requests", "version": "2.34.2"})
    assert result == {"ok": True, "data": {"count": 0, "vulns": [], "truncated": False}}


def test_unknown_severity_stays_null(use, registry):
    vuln = {"id": "X-1", "aliases": [], "affected": []}
    use(lambda m, url, b: (200, {"vulns": [vuln]}))
    data = registry.call("get_vulns", {"name": "pkg", "version": "1.0"})["data"]
    assert data["vulns"] == [{"id": "X-1", "severity": None, "fixed_versions": []}]


def test_vulns_follow_pages(use, registry):
    pages = {
        None: {"vulns": [{"id": "A"}], "next_page_token": "p2"},
        "p2": {"vulns": [{"id": "B"}]},
    }
    fake = use(lambda m, url, b: (200, pages[b.get("page_token")]))
    data = registry.call("get_vulns", {"name": "pkg", "version": "1.0"})["data"]
    assert [v["id"] for v in data["vulns"]] == ["A", "B"]
    assert data["truncated"] is False
    assert len(fake.calls) == 2


def test_vulns_page_limit_marks_truncated(use, registry):
    fake = use(lambda m, url, b: (200, {"vulns": [{"id": f"V{len(fake.calls)}"}], "next_page_token": "more"}))
    data = registry.call("get_vulns", {"name": "pkg", "version": "1.0"})["data"]
    assert len(fake.calls) == MAX_PAGES
    assert data["truncated"] is True


# ── get_package_versions ─────────────────────────────────
def test_package_versions_django(use, registry):
    fake = use(lambda m, url, b: fixture("pypi_django_all"))
    data = registry.call("get_package_versions", {"name": "django"})["data"]
    assert data["latest"] == "6.1.3"
    assert data["project_url"] == "https://pypi.org/project/Django/"
    by_version = {v["version"]: v for v in data["versions"]}
    assert by_version["4.2"]["requires_python"] == ">=3.8"
    assert by_version["5.0"]["requires_python"] == ">=3.10"
    assert "1.0.1" not in by_version  # 파일 없는 버전은 뺌
    assert fake.calls[0][1] == "https://pypi.org/pypi/django/json"


def test_package_versions_missing_requires_python_stays_null(use, registry):
    use(lambda m, url, b: fixture("pypi_requests_all"))
    data = registry.call("get_package_versions", {"name": "requests"})["data"]
    assert data["latest"] == "2.34.2"
    assert any(v["requires_python"] is None for v in data["versions"])  # 옛 버전은 정보 없음 → 채우지 않음


def test_package_versions_yanked_only_when_all_files_yanked(use, registry):
    body = {
        "info": {"version": "2.0", "project_url": "https://pypi.org/project/pkg/"},
        "releases": {
            "1.0": [{"yanked": True}, {"yanked": False}],
            "2.0": [{"yanked": True, "requires_python": ">=3.9"}],
        },
    }
    use(lambda m, url, b: (200, body))
    versions = registry.call("get_package_versions", {"name": "pkg"})["data"]["versions"]
    assert versions == [
        {"version": "1.0", "requires_python": None, "yanked": False},
        {"version": "2.0", "requires_python": ">=3.9", "yanked": True},
    ]


def test_package_not_found(use, registry):
    use(lambda m, url, b: fixture("pypi_no_package"))
    result = registry.call("get_package_versions", {"name": "no-such-package-xyz-123"})
    assert result["error"]["code"] == PACKAGE_NOT_FOUND


# ── 통신 실패 (세 Tool 공통) ─────────────────────────────
CALLS = [
    ("get_eol", {"product": "ubuntu", "cycle": "20.04"}),
    ("get_vulns", {"name": "requests", "version": "2.19.0"}),
    ("get_package_versions", {"name": "django"}),
]


@pytest.mark.parametrize("tool,args", CALLS)
@pytest.mark.parametrize(
    "response,code",
    [
        (requests.Timeout(), TIMEOUT),
        (requests.ConnectionError(), UPSTREAM_ERROR),
        ((429, None), UPSTREAM_ERROR),
        ((503, None), UPSTREAM_ERROR),
        ((200, None), UPSTREAM_ERROR),  # JSON이 아님
        ((200, ["예상과 다른 모양"]), UPSTREAM_ERROR),
    ],
)
def test_transport_failures(use, registry, tool, args, response, code):
    use(lambda m, url, b: response)
    result = registry.call(tool, args)
    assert result["ok"] is False
    assert result["error"]["code"] == code


def test_one_tool_failure_does_not_affect_others(use, registry):
    def responder(method, url, body):
        if "osv" in url:
            return requests.Timeout()
        return fixture("eol_ubuntu_20.04") if "endoflife" in url else fixture("pypi_django_all")

    use(responder)
    assert registry.call("get_vulns", {"name": "django", "version": "2.2.0"})["error"]["code"] == TIMEOUT
    assert registry.call("get_eol", {"product": "ubuntu", "cycle": "20.04"})["ok"] is True
    assert registry.call("get_package_versions", {"name": "django"})["ok"] is True


def test_user_agent_is_set():
    assert http.USER_AGENT.startswith("sudo-patch/")


# ── 2일차 리뷰 #7: 이상한 응답 형식은 예외가 아니라 UPSTREAM_ERROR ──
@pytest.mark.parametrize(
    "tool,args,body",
    [
        ("get_eol", {"product": "ubuntu", "cycle": "20.04"}, {"result": {"eolFrom": "2025-05-31", "latest": "문자열"}}),
        ("get_vulns", {"name": "requests", "version": "1.0"}, {"vulns": ["문자열"]}),
        ("get_vulns", {"name": "requests", "version": "1.0"}, {"vulns": [{"id": "X", "database_specific": "문자열"}]}),
        ("get_package_versions", {"name": "django"}, {"info": {"version": "1.0"}, "releases": {"1.0": ["문자열"]}}),
    ],
)
def test_malformed_upstream_is_upstream_error(use, registry, tool, args, body):
    use(lambda m, url, b: (200, body))
    result = registry.call(tool, args)
    assert result["ok"] is False and result["error"]["code"] == UPSTREAM_ERROR


def test_tool_functions_do_not_raise_when_called_directly(use):
    from app.tools.eol import get_eol
    from app.tools.specs import EolInput

    use(lambda m, url, b: (200, {"result": {"eolFrom": "2025-05-31", "latest": "문자열"}}))
    assert get_eol(EolInput(product="ubuntu", cycle="20.04"))["error"]["code"] == UPSTREAM_ERROR


def test_bad_charset_json_is_upstream_error(monkeypatch):
    class BadResponse:
        status_code = 200

        def json(self):
            raise LookupError("unknown encoding")

    monkeypatch.setattr(http.requests, "request", lambda *a, **k: BadResponse())
    assert http.fetch_json("GET", "https://example.invalid")["error"]["code"] == UPSTREAM_ERROR
