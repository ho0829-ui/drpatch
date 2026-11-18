"""캘린더 Tool 2개 (심화 F3023, 종류 local). 명세 → docs/spec.md "심화: 캘린더 연동".

구현체(CalendarBackend)를 받아 Tool 함수를 만든다 → 로컬·Google을 바꿔 끼워도 Tool 모양은 그대로.
"""

from datetime import date as Date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.tools.base import fail, ok
from app.tools.registry import ToolRegistry, ToolSpec

CALENDAR_ERROR = "CALENDAR_ERROR"
PLAN_NOT_FOUND = "PLAN_NOT_FOUND"
MAX_RANGE_DAYS = 62


class ListEventsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date_from: Date = Field(description="시작 날짜 YYYY-MM-DD")
    date_to: Date = Field(description="끝 날짜 YYYY-MM-DD (포함)")

    @model_validator(mode="after")
    def check_range(self):
        if self.date_to < self.date_from:
            raise ValueError("date_to는 date_from보다 빠를 수 없습니다")
        if (self.date_to - self.date_from).days > MAX_RANGE_DAYS:
            raise ValueError(f"한 번에 {MAX_RANGE_DAYS}일까지 조회합니다")
        return self


class CalendarEvent(BaseModel):
    id: int | str
    title: str
    date: Date
    start: str | None
    end: str | None
    source: str


class ListEventsData(BaseModel):
    events: list[CalendarEvent]


class AddEventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_id: Annotated[int, Field(ge=1, description="저장된 계획 id. 제목·시각은 서버가 계획에서 읽는다")]


class AddEventData(BaseModel):
    event_id: int | str
    title: str
    date: Date
    start: str | None
    end: str | None
    created: bool = Field(description="새로 만들었으면 true, 이미 등록돼 있었으면 false")


LIST_CALENDAR_EVENTS = ToolSpec(
    name="list_calendar_events",
    description="점검 회차 날짜에 다른 일정이 있는지 알아야 할 때 쓴다. 기간 안의 일정을 돌려준다.",
    kind="local",
    input_model=ListEventsInput,
    output_model=ListEventsData,
    error_codes=(CALENDAR_ERROR,),
)

ADD_CALENDAR_EVENT = ToolSpec(
    name="add_calendar_event",
    description="확정한 패치 계획을 일정으로 등록할 때 쓴다. 계획 id만 받는다.",
    kind="local",
    input_model=AddEventInput,
    output_model=AddEventData,
    error_codes=(PLAN_NOT_FOUND, CALENDAR_ERROR),
)


def plan_title(plan: dict) -> str:
    names = ", ".join(i["name"] for i in plan.get("items", [])[:4])
    more = f" 외 {len(plan['items']) - 4}개" if len(plan.get("items", [])) > 4 else ""
    prefix = f"{plan['round_no']}회차 " if plan.get("round_no") else ""
    return f"[패치] {prefix}{names}{more}"


def register_calendar_tools(registry: ToolRegistry, calendar, get_plan) -> None:
    """calendar: CalendarBackend, get_plan(plan_id) -> dict|None (저장된 계획 읽기)."""
    from app.calendar.backend import SOURCE_APP

    def list_calendar_events(params: ListEventsInput) -> dict:
        try:
            events = calendar.list_events(params.date_from.isoformat(), params.date_to.isoformat())
        except Exception:
            return fail(CALENDAR_ERROR, "캘린더를 조회하지 못했습니다")
        return ok({"events": events})

    def add_calendar_event(params: AddEventInput) -> dict:
        try:
            plan = get_plan(params.plan_id)
        except Exception:
            return fail(CALENDAR_ERROR, "계획을 읽지 못했습니다")
        if plan is None:
            return fail(PLAN_NOT_FOUND, "그런 계획이 없습니다")
        try:
            existing = calendar.find_by_plan(params.plan_id)
            event, created = (existing, False) if existing else (
                calendar.add_event(plan_title(plan), plan["date"], plan.get("window_start"), plan.get("window_end"),
                                   source=SOURCE_APP, plan_id=params.plan_id), True)
        except Exception:
            return fail(CALENDAR_ERROR, "캘린더에 등록하지 못했습니다")
        return ok({"event_id": event["id"], "title": event["title"], "date": event["date"],
                   "start": event["start"], "end": event["end"], "created": created})

    registry.register(LIST_CALENDAR_EVENTS, list_calendar_events)
    registry.register(ADD_CALENDAR_EVENT, add_calendar_event)



