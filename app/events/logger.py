"""로깅 Agent (F3013): 이벤트 버스를 구독해 받은 이벤트를 그대로 SQLite events 표에 덧붙인다.

- LLM을 부르지 않는다. 요약·가공 없이 발생한 사실을 그대로 남긴다.
- 메인 Agent와 다른 스레드에서 돈다. 저장에 실패해도 세고 넘어가며, 대화에는 영향이 없다.
"""

import threading

from app.db import repo
from app.events.bus import EventBus, Subscription

_STOP = object()


class LoggingAgent:
    def __init__(self, bus: EventBus, db_path: str | None = None, queue_size: int | None = None):
        self.bus = bus
        self.db_path = db_path
        self.queue_size = queue_size
        self.saved = 0
        self.failed = 0
        self._sub: Subscription | None = None
        self._thread: threading.Thread | None = None

    @property
    def dropped(self) -> int:
        return self._sub.dropped if self._sub else 0

    def start(self) -> "LoggingAgent":
        self._sub = self.bus.subscribe(self.queue_size) if self.queue_size else self.bus.subscribe()
        self._thread = threading.Thread(target=self._run, name="logging-agent", daemon=True)
        self._thread.start()
        return self

    def stop(self, timeout: float = 5.0) -> None:
        """남은 이벤트를 다 저장하고 멈춘다."""
        if not self._sub or not self._thread:
            return
        self.bus.unsubscribe(self._sub)  # 새 이벤트는 그만 받기
        try:
            self._sub.queue.put(_STOP, timeout=timeout)
        except Exception:
            return  # 큐가 끝내 안 비면 포기 (daemon 스레드라 앱 종료를 막지 않음)
        self._thread.join(timeout)

    def _run(self) -> None:
        conn = None
        try:
            conn = repo.connect(self.db_path)
        except Exception:
            conn = None  # 연결 실패해도 큐는 계속 비운다 (메인이 막히지 않게)
        while True:
            event = self._sub.queue.get()
            if event is _STOP:
                break
            try:
                if conn is None:
                    raise RuntimeError("DB 연결 없음")
                repo.insert_event(conn, event.to_dict())
                self.saved += 1
            except Exception:
                self.failed += 1
        if conn is not None:
            conn.close()
