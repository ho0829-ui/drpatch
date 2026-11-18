"""기존 일정과 겹치는 회차를 다음 빈 날로 옮기기 (심화 F3023 "조회한 일정을 제약 판단에 반영"). 순수 함수.

- 회차 시간대(없으면 하루 전체)와 겹치는 일정이 있으면, 그 날부터 SEARCH_DAYS일 안에서 겹치지 않는 가장 가까운 날.
- 이 서비스가 등록한 일정(source=sudo-patch)은 충돌로 보지 않는다 (계획끼리 겹침은 /plans overlaps가 담당).
"""

from datetime import date, timedelta

from app.timewindow import window

SEARCH_DAYS = 7
APP_SOURCE = "sudo-patch"


def conflicts_on(day: date, start: str | None, end: str | None, events: list[dict]) -> list[dict]:
    w_start, w_end = window(start, end)
    found = []
    for e in events:
        if e.get("source") == APP_SOURCE or e["date"] != day.isoformat():
            continue
        e_start, e_end = window(e.get("start"), e.get("end"))
        if w_start < e_end and e_start < w_end:
            found.append(e)
    return found


def find_free_date(day: date, start: str | None, end: str | None, events: list[dict],
                   search_days: int = SEARCH_DAYS) -> date | None:
    """day가 비어 있으면 day, 아니면 search_days 안의 가장 가까운 빈 날. 없으면 None."""
    for offset in range(search_days + 1):
        candidate = day + timedelta(days=offset)
        if not conflicts_on(candidate, start, end, events):
            return candidate
    return None
