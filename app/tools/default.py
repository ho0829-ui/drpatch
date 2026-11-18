"""Agent가 쓰는 기본 레지스트리: Tool 3종을 명세와 구현 함수로 등록한다."""

from app.tools.eol import get_eol
from app.tools.package_versions import get_package_versions
from app.tools.registry import ToolRegistry
from app.tools.specs import GET_EOL, GET_PACKAGE_VERSIONS, GET_VULNS
from app.tools.vulns import get_vulns


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GET_EOL, get_eol)
    registry.register(GET_VULNS, get_vulns)
    registry.register(GET_PACKAGE_VERSIONS, get_package_versions)
    return registry
