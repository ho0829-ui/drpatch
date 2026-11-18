"""캘린더 일정 (심화 F3023): 내 기존 일정 넣기·보기·지우기. 회차와 겹치면 Agent가 다음 빈 날로 옮긴다."""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import CalendarEventIn

router = APIRouter(prefix="/calendar", tags=["calendar"])
OFF = "캘린더를 쓰지 않도록 설정돼 있어요 (.env CALENDAR_BACKEND)."
DEFAULT_DAYS = 62


def _calendar(request: Request):
    calendar = request.app.state.calendar
    if calendar is None:
        raise HTTPException(status_code=404, detail=OFF)
    return calendar


@router.get("/events")
def list_events(request: Request, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    date_from = date_from or date.today()
    date_to = date_to or date_from + timedelta(days=DEFAULT_DAYS)
    if date_to < date_from:
        raise HTTPException(status_code=422, detail="끝 날짜가 시작 날짜보다 빨라요.")
    return _calendar(request).list_events(date_from.isoformat(), date_to.isoformat())


@router.post("/events", status_code=201)
def add_event(body: CalendarEventIn, request: Request) -> dict:
    return _calendar(request).add_event(body.title, body.date.isoformat(), body.start, body.end)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, request: Request) -> None:
    if not _calendar(request).delete_event(event_id):
        raise HTTPException(status_code=404, detail="그런 일정이 없어요.")
