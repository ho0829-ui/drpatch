"""이벤트 버스 (F3012). 발행하는 쪽은 누가 구독하는지 모른다.

- publish()는 구독자 큐에 put_nowait만 하고 바로 돌아온다. 큐가 가득 차면 버리고 센다 → 메인 Agent는 절대 기다리지 않는다.
- publish()는 어떤 경우에도 예외를 던지지 않는다.
- 이벤트: {session_id, seq, type, payload, created_at}. seq는 세션 안에서 1부터.
"""

import queue
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.agent.runner import Emit

DEFAULT_QUEUE_SIZE = 10_000


@dataclass(frozen=True)
class Event:
    session_id: str
    seq: int
    type: str
    payload: dict[str, Any]
    created_at: str  # UTC ISO 8601

    def to_dict(self) -> dict:
        return asdict(self)


class Subscription:
    def __init__(self, bus: "EventBus", maxsize: int):
        self._bus = bus
        self.queue: queue.Queue[Event] = queue.Queue(maxsize=maxsize)
        self.dropped = 0  # 큐가 가득 차서 버린 수

    def get(self, timeout: float | None = None) -> Event | None:
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        self._bus.unsubscribe(self)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Subscription] = []
        self._seq: dict[str, int] = {}
        self._lock = Lock()

    def subscribe(self, maxsize: int = DEFAULT_QUEUE_SIZE) -> Subscription:
        sub = Subscription(self, maxsize)
        with self._lock:
            self._subscribers.append(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)

    def publish(self, session_id: str, event_type: str, payload: dict | None = None) -> Event | None:
        try:
            with self._lock:
                seq = self._seq.get(session_id, 0) + 1
                self._seq[session_id] = seq
                subscribers = list(self._subscribers)
            event = Event(session_id, seq, event_type, dict(payload or {}),
                          datetime.now(timezone.utc).isoformat(timespec="milliseconds"))
            for sub in subscribers:
                try:
                    sub.queue.put_nowait(event)
                except queue.Full:
                    sub.dropped += 1
            return event
        except Exception:  # 발행 실패가 대화를 멈추게 하지 않는다
            return None

    def emitter(self, session_id: str) -> Emit:
        """그래프·runner의 emit 자리에 꽂는 함수."""
        return lambda event_type, payload: self.publish(session_id, event_type, payload)
