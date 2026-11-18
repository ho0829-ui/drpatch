"""우선순위 정렬 (spec "우선순위").

CRITICAL > HIGH > MODERATE > LOW > 심각도 미상 → 같으면 지원 종료까지 남은 날이 적은 순 (종료일 없으면 뒤로).
"""

from datetime import date

from app.agent.planner.items import SEVERITIES, Item


def sort_items(items: list[Item], today: date) -> list[Item]:
    def key(item: Item):
        days_left = (item.eol_date - today).days if item.eol_date else float("inf")
        return (SEVERITIES.index(item.severity), days_left)

    return sorted(items, key=key)  # 같은 키면 원래 순서 유지 (안정 정렬)
