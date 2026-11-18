"""sudo-patch 백엔드 진입점.

    uvicorn app.main:app --reload   →  http://localhost:8000

구조는 1일차 FastAPI 실습과 같다: 이 파일은 앱을 만들고 라우터를 붙이기만 한다.
라우터(/upload, /chat, /plans, /logs)는 spec "백엔드 API" 순서대로 app/api/ 에 하나씩 추가한다.
화면(HTML/CSS/JS)도 이 서버가 같이 내보낼 예정이라(같은 주소) CORS 설정은 두지 않는다.

앱이 켜질 때: DB 표 준비 → 이벤트 버스 생성 → 로깅 Agent(별도 스레드) 시작. 꺼질 때 로깅 Agent 정지.
로깅 Agent가 실패해도 앱은 뜬다 (로깅이 멈춰도 대화는 정상, F3013).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import repo
from app.events.bus import EventBus
from app.events.logger import LoggingAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bus = EventBus()
    app.state.logger = None
    try:
        repo.init_db()
        app.state.logger = LoggingAgent(app.state.bus).start()
    except Exception:
        pass  # 로깅 없이도 서비스는 동작
    yield
    if app.state.logger:
        app.state.logger.stop()


app = FastAPI(title="sudo-patch", description="서버 패치·EOL 점검 플래너", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    """서버가 켜져 있는지만 확인한다."""
    return {"ok": True}
