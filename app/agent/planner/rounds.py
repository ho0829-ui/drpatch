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


@dataclass
class RoundsResult:
    rounds: list[Round] = field(default_factory=list)
    unassigned: list[Item] = field(default_factory=list)


def _mark_after_eol(item: Item, when: date) -> Item:
    if item.eol_date and when > item.eol_date and FLAG_AFTER_EOL not in item.flags:
        return replace(item, flags=(*item.flags, FLAG_AFTER_EOL))
    return item


def split_rounds(
    items: list[Item], capacity: int, first_date: date, interval_days: int, max_rounds: int = MAX_ROUNDS
) -> RoundsResult:
    if capacity < 1:
        raise ValueError("capacity(N)는 1 이상이어야 합니다")  # 입력 검사는 앞 단계에서. 여기 오면 코드 실수
    result = RoundsResult()
    remaining = list(items)
    upgrade_round: int | None = None

    for round_no in range(1, max_rounds + 1):
        if not remaining:
            break
        when = first_date + timedelta(days=interval_days * (round_no - 1))
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
