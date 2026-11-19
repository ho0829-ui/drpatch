"""sudo-patch 백엔드 진입점.

    uvicorn app.main:app --reload   →  http://localhost:8000

구조는 1일차 FastAPI 실습과 같다: 이 파일은 앱을 만들고 라우터를 붙이기만 한다.
화면은 이 서버가 같이 내보내고(로컬·같은 주소), 배포 때는 GitHub Pages가 내보낸다(spec v1.25).
그래서 CORS는 Pages 주소(`ALLOWED_ORIGINS`, 기본 https://ho0829-ui.github.io)만 허용한다.

앱이 켜질 때: DB 표 준비 → 이벤트 버스 → 로깅 Agent(별도 스레드) → LLM(GmsBrain) 준비.
- 로깅 Agent가 실패해도 앱은 뜬다 (로깅이 멈춰도 대화는 정상, F3013).
- API 키가 없으면 brain=None → /chat이 "서버 설정(API 키) 확인" 안내만 보낸다 (F3019).
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import calendar, chat, logs, plans, upload
from app.db import repo
from app.events.bus import EventBus
from app.events.logger import LoggingAgent
from app.public import PublicGuard, load_public_settings

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "frontend" / "dist"
WEB_DIR = DIST_DIR if DIST_DIR.is_dir() else ROOT_DIR / "web"


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
    app.state.public = PublicGuard(load_public_settings())  # 공개 모드 (spec v1.24), 기본은 꺼짐
    app.state.db_path = repo.db_path()
    app.state.bus = EventBus()
    app.state.logger = None
    try:
        repo.init_db(app.state.db_path)
        if app.state.public.enabled:  # 공개 모드만: 오래된 방문자 데이터 정리 (로컬 DB는 건드리지 않음)
            with repo.connect(app.state.db_path) as conn:
                repo.purge_older_than(conn, app.state.public.settings.retention_days)
        app.state.logger = LoggingAgent(app.state.bus, app.state.db_path).start()
    except Exception:
        pass  # 로깅 없이도 서비스는 동작
    app.state.brain = make_brain()
    app.state.calendar = make_calendar_backend(app.state.db_path)
    yield
    if app.state.logger:
        app.state.logger.stop()


app = FastAPI(title="sudo-patch", description="서버 패치·EOL 점검 플래너", lifespan=lifespan)

DEFAULT_ORIGINS = "https://ho0829-ui.github.io"


def allowed_origins() -> list[str]:
    """화면을 다른 주소(GitHub Pages)에서 내보낼 때 API를 부를 수 있는 주소. 쉼표로 여러 개."""
    from dotenv import load_dotenv

    load_dotenv()
    raw = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS)
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


ORIGINS = allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Session-Id"],
    # Chrome: 공개 페이지(Pages)가 사설 주소로 풀리는 이 Mac을 부를 때의 사전 확인에 '허용' (sudo-quest 때와 같은 처리)
    allow_private_network=True,
    max_age=600,
)




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
    """서버가 켜져 있는지, 공개 모드인지 (화면이 "모든 계획 보기"를 숨길지 정함)."""
    guard = getattr(app.state, "public", None)
    return {"ok": True, "public": bool(guard and guard.enabled)}


# 화면(web/)은 API 라우터 뒤에 붙인다 → /plans 등 API 경로가 먼저 잡힌다
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
