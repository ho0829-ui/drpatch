"""회차 나누기 (spec "회차 나누기").

1. 우선순위대로 정렬된 항목을 받는다.
2. 순서 제약이 먼저: Python 업그레이드가 앞 회차에 들어가기 전엔, 그게 필요한 항목을 넣지 않는다.
3. 회차마다 N개까지 (Python·OS 항목도 하나로 셈), 최대 3회차. 넘친 것은 미배정.
4. 회차 날짜가 항목의 지원 종료일 뒤면 "종료 이후 처리" 표시.
"""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from app.agent.planner.items import FLAG_AFTER_EOL, Item

MAX_ROUNDS = 3


@dataclass
class Round:
    round_no: int
    date: date
    items: list[Item]
    moved_from: date | None = None  # 캘린더 일정과 겹쳐 옮겼으면 원래 날짜 (F3023)
    calendar_conflicts: list[str] = field(default_factory=list)  # 옮기지 못한 겹치는 일정 제목


@dataclass
class RoundsResult:
    rounds: list[Round] = field(default_factory=list)
    unassigned: list[Item] = field(default_factory=list)


def move_round(r: Round, new_date: date) -> None:
    """회차 날짜를 옮기고 '종료 이후 처리' 표시를 새 날짜로 다시 계산한다."""
    r.moved_from, r.date = r.date, new_date
    r.items = [_mark_after_eol(i, new_date) for i in r.items]


def _mark_after_eol(item: Item, when: date) -> Item:
    if item.eol_date and when > item.eol_date and FLAG_AFTER_EOL not in item.flags:
        return replace(item, flags=(*item.flags, FLAG_AFTER_EOL))
    return item


def next_matching_date(start: date, weekdays: list[int], week_interval: int = 1, anchor_monday: date | None = None) -> date:
    """start 이상에서 weekdays에 속하고 week_interval 주기에 맞는 가장 가까운 날짜."""
    allowed = set(weekdays)
    step = 2 if week_interval == 2 else 1
    d = start
    while True:
        if d.weekday() in allowed:
            if anchor_monday is None or step == 1:
                return d
            monday = d - timedelta(days=d.weekday())
            if ((monday - anchor_monday).days // 7) % step == 0:
                return d
        d += timedelta(days=1)


def _round_dates(
    first_date: date,
    count: int,
    interval_days: int | None,
    weekdays: list[int] | None = None,
    week_interval: int = 1,
) -> list[date]:
    if weekdays:
        first_hit = next_matching_date(first_date, weekdays)
        anchor_monday = first_hit - timedelta(days=first_hit.weekday())
        dates = [first_hit]
        cur = first_hit
        while len(dates) < count:
            cur = next_matching_date(cur + timedelta(days=1), weekdays, week_interval, anchor_monday)
            dates.append(cur)
        return dates
    step = interval_days or 1
    return [first_date + timedelta(days=step * i) for i in range(count)]


def split_rounds(
    items: list[Item],
    capacity: int,
    first_date: date,
    interval_days: int | None,
    max_rounds: int = MAX_ROUNDS,
    weekdays: list[int] | None = None,
    week_interval: int = 1,
) -> RoundsResult:
    if capacity < 1:
        raise ValueError("capacity(N)는 1 이상이어야 합니다")  # 입력 검사는 앞 단계에서. 여기 오면 코드 실수
    result = RoundsResult()
    remaining = list(items)
    upgrade_round: int | None = None
    dates = _round_dates(first_date, max_rounds, interval_days, weekdays=weekdays, week_interval=week_interval)

    for round_no in range(1, max_rounds + 1):
        if not remaining:
            break
        when = dates[round_no - 1]
        chosen: list[Item] = []
        for item in remaining:
            if len(chosen) == capacity:
                break
            if item.needs_python_upgrade and (upgrade_round is None or upgrade_round >= round_no):
                continue  # 업그레이드보다 같은·앞 회차에 올 수 없음
            chosen.append(item)
        if any(i.kind == "python_upgrade" for i in chosen):
            upgrade_round = round_no
        remaining = [i for i in remaining if i not in chosen]
        result.rounds.append(Round(round_no, when, [_mark_after_eol(i, when) for i in chosen]))

    result.unassigned = remaining
    return result
