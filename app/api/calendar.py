"""캘린더 일정 (심화 F3023): 내 기존 일정 넣기·보기·지우기. 회차와 겹치면 Agent가 다음 빈 날로 옮긴다."""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import CalendarEventIn
from app.calendar.backend import scoped
from app.public import owner_of

router = APIRouter(prefix="/calendar", tags=["calendar"])
OFF = "캘린더를 쓰지 않도록 설정돼 있어요 (.env CALENDAR_BACKEND)."
DEFAULT_DAYS = 62


NO_SESSION = "허허, 먼저 파일을 올리거나 예시를 골라 주시죠. 그래야 일정을 차트에 붙일 수 있습니다."


def _calendar(request: Request):
    """공개 모드면 요청한 세션의 일정만 다루는 캘린더 (spec v1.24). 로컬은 전체."""
    calendar = request.app.state.calendar
    if calendar is None:
        raise HTTPException(status_code=404, detail=OFF)
    return scoped(calendar, owner_of(request))


@router.get("/events")
def list_events(request: Request, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    date_from = date_from or date.today()
    date_to = date_to or date_from + timedelta(days=DEFAULT_DAYS)
    if date_to < date_from:
        raise HTTPException(status_code=422, detail="끝 날짜가 시작 날짜보다 빨라요.")
    return _calendar(request).list_events(date_from.isoformat(), date_to.isoformat())


@router.post("/events", status_code=201)
def add_event(body: CalendarEventIn, request: Request) -> dict:
    if owner_of(request) == "":
        raise HTTPException(status_code=400, detail=NO_SESSION)
    return _calendar(request).add_event(body.title, body.date.isoformat(), body.start, body.end)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, request: Request) -> None:
    if not _calendar(request).delete_event(event_id):
        raise HTTPException(status_code=404, detail="그런 일정이 없어요.")
