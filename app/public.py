"""공개 모드 (spec v1.24): Tailscale Funnel로 밖에 내놓을 때만 켠다 (`PUBLIC_MODE=1`).

- 내 데이터만: 요청 머리말 `X-Session-Id`(업로드·대화가 준 무작위 세션 아이디)로 계획·로그·일정을 거른다.
- 호출 상한: /chat·/upload를 IP와 하루 전체로 막는다 (메모리 — 서버를 다시 켜면 초기화).
로컬(기본)에서는 아무것도 바뀌지 않는다.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass

from dotenv import load_dotenv
from fastapi import HTTPException, Request

LIMIT_MESSAGE = "허허, 진료 대기가 길어졌네요. 잠시 뒤에 다시 오시죠."
SESSION_HEADER = "X-Session-Id"


def _int_env(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, "").strip() or default))
    except ValueError:
        return default


@dataclass(frozen=True)
class PublicSettings:
    enabled: bool = False
    chat_per_hour: int = 20
    chat_per_day: int = 300
    upload_per_hour: int = 60


def load_public_settings() -> PublicSettings:
    load_dotenv()
    enabled = os.getenv("PUBLIC_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    return PublicSettings(
        enabled=enabled,
        chat_per_hour=_int_env("PUBLIC_CHAT_PER_HOUR", 20),
        chat_per_day=_int_env("PUBLIC_CHAT_PER_DAY", 300),
        upload_per_hour=_int_env("PUBLIC_UPLOAD_PER_HOUR", 60),
    )


class RateLimiter:
    """창(초) 안의 횟수를 센다. 키마다 시각 목록을 두고 오래된 것은 버린다. 스레드 안전."""

    def __init__(self, limit: int, window_s: float, clock=time.monotonic):
        self.limit = limit
        self.window = window_s
        self.clock = clock
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True  # 0이면 상한 없음
        now = self.clock()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


class PublicGuard:
    def __init__(self, settings: PublicSettings, clock=time.monotonic):
        self.settings = settings
        self.chat_ip = RateLimiter(settings.chat_per_hour, 3600, clock)
        self.chat_day = RateLimiter(settings.chat_per_day, 86400, clock)
        self.upload_ip = RateLimiter(settings.upload_per_hour, 3600, clock)

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    def check_chat(self, request: Request) -> None:
        if not self.enabled:
            return
        ip = client_ip(request)
        # 전체 상한을 먼저 보면 IP 하나가 막혔을 때 전체 횟수를 깎지 않는다
        if not self.chat_ip.allow(f"chat:{ip}") or not self.chat_day.allow("chat:all"):
            raise HTTPException(status_code=429, detail=LIMIT_MESSAGE)

    def check_upload(self, request: Request) -> None:
        if not self.enabled:
            return
        if not self.upload_ip.allow(f"upload:{client_ip(request)}"):
            raise HTTPException(status_code=429, detail=LIMIT_MESSAGE)


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd.strip():
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def guard(request: Request) -> PublicGuard:
    g = getattr(request.app.state, "public", None)
    return g if g is not None else PublicGuard(PublicSettings())


def owner_of(request: Request) -> str | None:
    """공개 모드면 요청의 세션 아이디(없으면 빈 문자열 = 아무것도 못 봄), 로컬이면 None(거르지 않음)."""
    if not guard(request).enabled:
        return None
    return (request.headers.get(SESSION_HEADER) or "").strip()
