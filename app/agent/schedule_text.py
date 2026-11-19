"""일정 간격·요일 규칙을 사람이 읽는 짧은 한글 문구로 바꾼다 (spec v1.21 M).

조건 한 줄(render.py), 화면 칩(I19), 테스트 모두 같은 규칙을 따른다.
"""

from __future__ import annotations

WEEKDAYS_KO = "월화수목금토일"

INTERVAL_LABELS = {
    1: "매일",
    2: "격일",
    7: "매주",
    14: "격주",
    21: "3주마다",
    30: "매월",
    90: "분기마다",
}


def _get(obj, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def fmt_schedule(conditions) -> str:
    """Conditions 또는 dict에서 간격·요일 표시 문자열을 만든다."""
    if not conditions:
        return ""
    raw_days = _get(conditions, "weekdays")
    weekdays = sorted({d for d in raw_days if isinstance(d, int) and 0 <= d <= 6}) if raw_days else []
    week_interval = _get(conditions, "week_interval") or 1
    interval_days = _get(conditions, "interval_days")
    weekly_count = _get(conditions, "weekly_count")

    if weekdays:
        if weekdays == [0, 1, 2, 3, 4] and week_interval == 1:
            return "평일"
        if weekdays == [5, 6] and week_interval == 1:
            return "주말"
        prefix = "격주" if week_interval == 2 else "매주"
        days_str = "·".join(WEEKDAYS_KO[d] for d in weekdays)
        return f"{prefix} {days_str}"

    if interval_days and interval_days > 0:
        return INTERVAL_LABELS.get(interval_days, f"{interval_days}일마다")

    if weekly_count and weekly_count > 0:
        return f"주 {weekly_count}회 (요일 필요)"

    return ""
