"""외부 API 통신을 한곳에서 처리한다. User-Agent·타임아웃·HTTP 상태 → 실패 코드 변환.

Tool은 `fetch_json()`만 부른다. 테스트는 `transport`를 가짜로 바꿔 네트워크 없이 돈다.
"""

from collections.abc import Callable
from typing import Any

import requests

from app.tools.base import TIMEOUT, UPSTREAM_ERROR, fail, ok

# PyPI는 요청을 고유하게 식별하는 User-Agent를 권한다 (docs/research/api-terms.md)
USER_AGENT = "sudo-patch/0.1 (study project; patch planner)"
DEFAULT_TIMEOUT = 10.0

# (method, url, json_body, timeout) -> (HTTP 상태, JSON 본문 또는 None)
Transport = Callable[[str, str, Any, float], tuple[int, Any]]


def requests_transport(method: str, url: str, json_body: Any, timeout: float) -> tuple[int, Any]:
    r = requests.request(
        method, url, json=json_body, timeout=timeout, headers={"User-Agent": USER_AGENT}
    )
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


transport: Transport = requests_transport


def fetch_json(
    method: str,
    url: str,
    *,
    json_body: Any = None,
    not_found_code: str | None = None,
    not_found_message: str = "찾는 대상이 없습니다",
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """성공이면 ok(JSON 본문), 아니면 fail(code). 예외를 던지지 않는다."""
    try:
        status, body = transport(method, url, json_body, timeout)
    except requests.Timeout:
        return fail(TIMEOUT, "외부 API 응답 시간이 초과됐습니다")
    except requests.RequestException:
        return fail(UPSTREAM_ERROR, "외부 API에 연결하지 못했습니다")

    if status == 404 and not_found_code:
        return fail(not_found_code, not_found_message)
    if status == 429:
        return fail(UPSTREAM_ERROR, "외부 API 요청이 많아 잠시 거절됐습니다 (HTTP 429)")
    if status != 200:
        return fail(UPSTREAM_ERROR, f"외부 API가 오류로 응답했습니다 (HTTP {status})")
    if body is None:
        return fail(UPSTREAM_ERROR, "외부 API 응답이 JSON 형식이 아닙니다")
    return ok(body)
