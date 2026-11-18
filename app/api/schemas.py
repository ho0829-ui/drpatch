"""API 요청·응답 형식 (F3017). 화면에는 짧은 안내만 보낸다 (NF3002)."""

from datetime import date as Date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.api.overlap import TIME_PATTERN, to_minutes

Time = Annotated[str, StringConstraints(pattern=TIME_PATTERN)]


class ChatIn(BaseModel):
    session_id: str | None = Field(None, description="없으면 서버가 새로 만든다")
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class UploadOut(BaseModel):
    session_id: str
    packages: list[dict]
    excluded: list[dict]
    saved: bool


def _check_window(start: str | None, end: str | None) -> None:
    if start and end and to_minutes(start, 0) >= to_minutes(end, 0):
        raise ValueError("시작 시각은 종료 시각보다 빨라야 합니다")


class PlanIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = None
    round_no: int | None = Field(None, ge=0)
    date: Date
    window_start: Time | None = None
    window_end: Time | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_window(self):
        _check_window(self.window_start, self.window_end)
        return self


class PlanUpdate(BaseModel):
    """계획의 핵심 값(날짜·시각·항목) 수정. 넘긴 것만 바꾼다 (F3016)."""

    model_config = ConfigDict(extra="forbid")

    date: Date | None = None
    window_start: Time | None = None
    window_end: Time | None = None
    items: list[dict[str, Any]] | None = None


class PlanOut(BaseModel):
    id: int
    session_id: str
    round_no: int
    date: str
    window_start: str | None
    window_end: str | None
    items: list[dict[str, Any]]
    created_at: str
    updated_at: str
    overlaps: list[dict] = Field(default_factory=list, description="같은 날 시간이 겹치는 다른 계획 (저장은 됨)")
