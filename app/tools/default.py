"""Agent가 쓰는 기본 레지스트리: 필수 Tool 3종 + (캘린더가 있으면) 캘린더 Tool 2개."""

from app.tools.eol import get_eol
from app.tools.package_versions import get_package_versions
from app.tools.registry import ToolRegistry
from app.tools.specs import GET_EOL, GET_PACKAGE_VERSIONS, GET_VULNS
from app.tools.vulns import get_vulns


def build_registry(calendar=None, db_path: str | None = None) -> ToolRegistry:
    """calendar(CalendarBackend)를 주면 캘린더 Tool 2개도 등록한다 (심화 F3023)."""
    registry = ToolRegistry()
    registry.register(GET_EOL, get_eol)
    registry.register(GET_VULNS, get_vulns)
    registry.register(GET_PACKAGE_VERSIONS, get_package_versions)
    if calendar is not None:
        from app.db import repo
        from app.tools.calendar_tools import register_calendar_tools

        def get_plan(plan_id: int):
            with repo.connect(db_path) as conn:
                return repo.get_plan(conn, plan_id)

        register_calendar_tools(registry, calendar, get_plan)
    return registry
