"""Google Calendar 구현체 (심화 F3023). LocalCalendar와 같은 인터페이스·같은 일정 모양을 돌려준다.

- Google Calendar API v3를 `requests`로 직접 부른다 (새 라이브러리 없음).
- 인증: `.env`의 `GOOGLE_CALENDAR_TOKEN`(OAuth 2.0 access token, 범위 calendar.events). 토큰 발급·갱신은 이 코드 밖에서 한다.
- `GOOGLE_CALENDAR_ID`(기본 primary), `GOOGLE_CALENDAR_TZ`(기본 Asia/Seoul).
- 이 서비스가 넣은 일정은 extendedProperties.private에 source·plan_id를 남겨 LocalCalendar의 source·plan_id와 같게 읽는다.
- 실패(토큰 없음·HTTP 오류·연결 실패)는 예외로 올리고, 캘린더 Tool이 CALENDAR_ERROR로 바꾼다 (Tool은 예외를 밖으로 내지 않음).

일정 모양: {id, title, date(YYYY-MM-DD), start(HH:MM|None), end(HH:MM|None), source, plan_id}
"""

import os
from datetime import date as Date
from datetime import datetime, timedelta
from typing import Any, Callable
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

from app.calendar.backend import SOURCE_USER

API = "https://www.googleapis.com/calendar/v3"
TIMEOUT = 10.0

# (method, url, params, json_body, headers) -> (status, body)
Send = Callable[[str, str, dict | None, Any, dict], tuple[int, Any]]


def requests_send(method: str, url: str, params: dict | None, json_body: Any, headers: dict) -> tuple[int, Any]:
    r = requests.request(method, url, params=params, json=json_body, headers=headers, timeout=TIMEOUT)
    body = r.json() if r.content and "json" in r.headers.get("content-type", "") else None
    return r.status_code, body


class GoogleCalendarError(RuntimeError):
    pass


class GoogleCalendar:
    name = "google"

    def __init__(self, token: str | None = None, calendar_id: str | None = None, tz: str | None = None,
                 send: Send = requests_send):
        self.token = (token if token is not None else os.getenv("GOOGLE_CALENDAR_TOKEN", "")).strip()
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "").strip() or "primary"
        self.tz = ZoneInfo(tz or os.getenv("GOOGLE_CALENDAR_TZ", "").strip() or "Asia/Seoul")
        self.send = send

    # ── HTTP ───────────────────────────────────────────
    def _call(self, method: str, path: str, params: dict | None = None, body: Any = None,
              ok: tuple[int, ...] = (200,)) -> tuple[int, Any]:
        if not self.token:
            raise GoogleCalendarError("GOOGLE_CALENDAR_TOKEN이 없습니다")
        url = f"{API}/calendars/{quote(self.calendar_id, safe='')}/events{path}"
        try:
            status, data = self.send(method, url, params, body, {"Authorization": f"Bearer {self.token}"})
        except requests.RequestException as e:
            raise GoogleCalendarError(f"연결 실패: {type(e).__name__}") from e
        if status not in ok:
            raise GoogleCalendarError(f"Google Calendar 응답 {status}")
        return status, data

    # ── 모양 바꾸기 ──────────────────────────────────────
    def _event(self, g: dict) -> dict:
        private = (g.get("extendedProperties") or {}).get("private") or {}
        plan_id = private.get("plan_id")
        start, end = g.get("start") or {}, g.get("end") or {}
        if "dateTime" in start:
            s = datetime.fromisoformat(start["dateTime"]).astimezone(self.tz)
            e = datetime.fromisoformat(end["dateTime"]).astimezone(self.tz)
            day, start_hm = s.date().isoformat(), s.strftime("%H:%M")
            end_hm = "24:00" if e.date() > s.date() and e.strftime("%H:%M") == "00:00" else e.strftime("%H:%M")
        else:  # 하루 종일
            day, start_hm, end_hm = start.get("date"), None, None
        return {"id": g["id"], "title": g.get("summary", ""), "date": day, "start": start_hm, "end": end_hm,
                "source": private.get("source", SOURCE_USER), "plan_id": int(plan_id) if plan_id else None}

    def _when(self, day: str, hm: str) -> str:
        d = Date.fromisoformat(day)
        if hm == "24:00":
            d, hm = d + timedelta(days=1), "00:00"
        h, m = map(int, hm.split(":"))
        return datetime(d.year, d.month, d.day, h, m, tzinfo=self.tz).isoformat()

    # ── CalendarBackend ──────────────────────────────────
    def list_events(self, date_from: str, date_to: str) -> list[dict]:
        params = {"timeMin": self._when(date_from, "00:00"), "timeMax": self._when(date_to, "24:00"),
                  "singleEvents": "true", "orderBy": "startTime", "maxResults": 250}
        _, data = self._call("GET", "", params=params)
        events = [self._event(g) for g in (data or {}).get("items", []) if g.get("status") != "cancelled"]
        return [e for e in events if date_from <= e["date"] <= date_to]

    def add_event(self, title, date, start=None, end=None, source=SOURCE_USER, plan_id=None) -> dict:
        if start and end:
            when = {"start": {"dateTime": self._when(date, start)}, "end": {"dateTime": self._when(date, end)}}
        else:
            nxt = (Date.fromisoformat(date) + timedelta(days=1)).isoformat()
            when = {"start": {"date": date}, "end": {"date": nxt}}
        private = {"source": source}
        if plan_id is not None:
            private["plan_id"] = str(plan_id)
        body = {"summary": title, **when, "extendedProperties": {"private": private}}
        _, data = self._call("POST", "", body=body)
        return self._event(data)

    def find_by_plan(self, plan_id: int) -> dict | None:
        params = {"privateExtendedProperty": f"plan_id={plan_id}", "singleEvents": "true", "maxResults": 1}
        _, data = self._call("GET", "", params=params)
        items = [g for g in (data or {}).get("items", []) if g.get("status") != "cancelled"]
        return self._event(items[0]) if items else None

    def delete_event(self, event_id) -> bool:
        status, _ = self._call("DELETE", f"/{quote(str(event_id), safe='')}", ok=(204, 200, 404, 410))
        return status in (200, 204)
