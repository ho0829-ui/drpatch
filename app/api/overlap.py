"""계획 시간 겹침 (spec "겹침"): 같은 날 + 시각 구간이 겹치면 경고. 시각이 없으면 하루 전체. 저장은 막지 않는다."""

import re

TIME_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$|^24:00$"
DAY_MINUTES = 24 * 60


def to_minutes(hhmm: str | None, default: int) -> int:
    if not hhmm:
        return default
    if not re.fullmatch(TIME_PATTERN, hhmm):
        raise ValueError(f"시각 형식이 아님: {hhmm}")
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def window(start: str | None, end: str | None) -> tuple[int, int]:
    """[시작, 끝) 분 단위. 둘 다 없으면 하루 전체, 하나만 있으면 그쪽만 열린 끝으로."""
    return to_minutes(start, 0), to_minutes(end, DAY_MINUTES)


def overlaps(a: dict, b: dict) -> bool:
    if a["date"] != b["date"]:
        return False
    a_start, a_end = window(a.get("window_start"), a.get("window_end"))
    b_start, b_end = window(b.get("window_start"), b.get("window_end"))
    return a_start < b_end and b_start < a_end


def find_overlaps(plan: dict, others: list[dict]) -> list[dict]:
    """plan과 겹치는 다른 계획 (자기 자신 제외). 화면 안내용으로 짧게."""
    return [
        {"id": o["id"], "round_no": o["round_no"], "date": o["date"],
         "window_start": o["window_start"], "window_end": o["window_end"]}
        for o in others
        if o["id"] != plan.get("id") and overlaps(plan, o)
    ]
