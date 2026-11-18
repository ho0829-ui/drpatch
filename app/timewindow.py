"""시각 구간 계산 (계획 겹침·캘린더 충돌이 같이 씀). 어떤 모듈에도 의존하지 않는다."""

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
