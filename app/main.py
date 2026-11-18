"""sudo-patch 백엔드 진입점.

    uvicorn app.main:app --reload   →  http://localhost:8000

구조는 1일차 FastAPI 실습과 같다: 이 파일은 앱을 만들고 라우터를 붙이기만 한다.
화면(HTML/CSS/JS)도 이 서버가 같이 내보낼 예정이라(같은 주소) CORS 설정은 두지 않는다.

앱이 켜질 때: DB 표 준비 → 이벤트 버스 → 로깅 Agent(별도 스레드) → LLM(GmsBrain) 준비.
- 로깅 Agent가 실패해도 앱은 뜬다 (로깅이 멈춰도 대화는 정상, F3013).
- API 키가 없으면 brain=None → /chat이 "서버 설정(API 키) 확인" 안내만 보낸다 (F3019).
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import calendar, chat, logs, plans, upload
from app.db import repo
from app.events.bus import EventBus
from app.events.logger import LoggingAgent

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def make_calendar_backend(db_path: str):
    from app.calendar.backend import make_calendar

    try:
        return make_calendar(db_path)
    except Exception:  # Google 구현체 미준비 등 → 캘린더 없이 동작
        return None


def make_brain():
    from app.agent.brain import GmsBrain

    try:
        return GmsBrain()
    except Exception:  # 키·주소·모델 이름 누락 (LLMConfigError) 등
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_path = repo.db_path()
    app.state.bus = EventBus()
    app.state.logger = None
    try:
        repo.init_db(app.state.db_path)
        app.state.logger = LoggingAgent(app.state.bus, app.state.db_path).start()
    except Exception:
        pass  # 로깅 없이도 서비스는 동작
    app.state.brain = make_brain()
    app.state.calendar = make_calendar_backend(app.state.db_path)
    yield
    if app.state.logger:
        app.state.logger.stop()


app = FastAPI(title="sudo-patch", description="서버 패치·EOL 점검 플래너", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def short_validation_error(request: Request, exc: RequestValidationError):
    """입력 오류는 고칠 칸 이름과 짧은 안내만 (NF3002)."""
    fields = sorted({".".join(str(p) for p in err["loc"] if p != "body") for err in exc.errors()})
    return JSONResponse(status_code=422, content={"detail": "입력 형식을 확인해 주세요.", "fields": fields})


app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(plans.router)
app.include_router(logs.router)
app.include_router(calendar.router)


@app.get("/health")
def health() -> dict:
    """서버가 켜져 있는지만 확인한다."""
    return {"ok": True}


# 화면(web/)은 API 라우터 뒤에 붙인다 → /plans 등 API 경로가 먼저 잡힌다
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
