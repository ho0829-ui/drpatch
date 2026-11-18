"""Tool 펼쳐 부르기: 동시 호출 수 제한 + 요청 안 캐시 + 호출 이벤트 (spec F3007, architecture.md 5절).

LLM은 Tool 종류·순서만 정하고, 패키지마다 반복 호출하는 건 여기서 한다.
"""

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

from app.tools.registry import ToolRegistry

Emit = Callable[[str, dict], None]  # (이벤트 종류, 내용) — 기다리지 않는 발행. 기본은 아무것도 안 함

MAX_WORKERS = 4  # PyPI 직렬 권장을 고려해 작게 (spec 외부 API)


def no_emit(event_type: str, payload: dict) -> None:
    return None


class ToolRunner:
    def __init__(self, registry: ToolRegistry, emit: Emit = no_emit, max_workers: int = MAX_WORKERS):
        self.registry = registry
        self.emit = emit
        self.max_workers = max_workers
        self._cache: dict[str, dict] = {}
        self._lock = Lock()
        self.calls = 0  # 실제로 Tool을 부른 횟수 (캐시 적중 제외)

    @staticmethod
    def _key(name: str, args: dict) -> str:
        return name + json.dumps(args, sort_keys=True, ensure_ascii=False)

    def call(self, name: str, args: dict) -> dict:
        key = self._key(name, args)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        self.emit("tool_call", {"tool": name, "args": args})
        start = time.perf_counter()
        result = self.registry.call(name, args)
        took_ms = round((time.perf_counter() - start) * 1000)
        self.emit(
            "tool_result",
            {"tool": name, "args": args, "ok": result["ok"], "ms": took_ms,
             "error_code": None if result["ok"] else result["error"]["code"]},
        )
        with self._lock:
            self._cache[key] = result
            self.calls += 1
        return result

    def call_many(self, calls: list[tuple[str, dict]]) -> list[dict]:
        """순서대로 결과를 돌려준다. 하나가 실패해도 나머지는 계속 (결과에 ok:false로 남음)."""
        if len(calls) <= 1:
            return [self.call(name, args) for name, args in calls]
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            return list(pool.map(lambda c: self.call(*c), calls))

    # planner가 넘겨받는 함수 모양으로 감싸기
    def vuln_count(self, name: str, version: str) -> int | None:
        result = self.call("get_vulns", {"name": name, "version": version})
        return result["data"]["count"] if result["ok"] else None

    def python_eol(self, cycle: str) -> dict[str, Any] | None:
        result = self.call("get_eol", {"product": "python", "cycle": cycle})
        return {"eol_date": result["data"]["eol_date"], "is_eol": result["data"]["is_eol"]} if result["ok"] else None
