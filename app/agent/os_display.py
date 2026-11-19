"""OS를 사용자에게 보이는 말로 (spec v1.17). 조회용 이름(macos, 11-24h2-w)을 그대로 화면·답에 내지 않는다."""

OS_NAMES = {"ubuntu": "Ubuntu", "macos": "macOS", "windows": "Windows"}

# 지원이 끝났을 때 올릴 곳. LTS는 Ubuntu에만 맞는 말이라 OS마다 따로 쓴다.
UPGRADE_HINTS = {
    "ubuntu": "지원 중인 다음 LTS로 올림 필요",
    "macos": "지원 중인 macOS로 올림 필요",
    "windows": "지원 중인 기능 업데이트로 올림 필요",
}

# Windows cycle 끝의 -w·-e (endoflife.date 기준)
WINDOWS_EDITIONS = {"w": "Home/Pro", "e": "Enterprise/Education"}


def os_display_name(os_name: str | None) -> str | None:
    if not os_name:
        return None
    return OS_NAMES.get(os_name, os_name.capitalize())


def os_display_version(os_name: str | None, version: str | None) -> str | None:
    """'11-24h2-w' → '11 24H2 (Home/Pro 기준)'. 다른 OS는 그대로."""
    if os_name != "windows" or not version:
        return version
    parts = version.split("-")
    if len(parts) != 3:
        return version
    major, feature, edition = parts
    return f"{major} {feature.upper()} ({WINDOWS_EDITIONS.get(edition, edition)} 기준)"


def upgrade_hint(os_name: str | None) -> str:
    return UPGRADE_HINTS.get(os_name or "", "지원 중인 다음 버전으로 올림 필요")
