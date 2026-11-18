"""get_package_versions: PyPI JSON API로 버전별 requires_python·yanked 조회 (F3003 상세 속성)."""

from urllib.parse import quote

from app.tools import http
from app.tools.base import PACKAGE_NOT_FOUND, UPSTREAM_ERROR, safe_parse, fail, ok
from app.tools.specs import PackageVersionsInput

BASE_URL = "https://pypi.org/pypi"


def parse_versions(body: dict) -> dict:
    info = body.get("info") if isinstance(body, dict) else None
    releases = body.get("releases") if isinstance(body, dict) else None
    if not isinstance(info, dict) or not isinstance(releases, dict) or not info.get("version"):
        return fail(UPSTREAM_ERROR, "PyPI 응답 형식이 예상과 다릅니다")

    versions = []
    for version, files in releases.items():
        if not files:  # 올린 파일이 없으면 설치할 수 없다
            continue
        requires_python = next((f["requires_python"] for f in files if f.get("requires_python")), None)
        versions.append(
            {
                "version": version,
                "requires_python": requires_python,  # 비어 있으면 null = 호환 미확인. 채우지 않는다
                "yanked": all(f.get("yanked") for f in files),
            }
        )

    return ok(
        {
            "latest": info["version"],
            "project_url": info.get("project_url") or info.get("package_url"),
            "versions": versions,
        }
    )


def get_package_versions(params: PackageVersionsInput) -> dict:
    fetched = http.fetch_json(
        "GET",
        f"{BASE_URL}/{quote(params.name, safe='')}/json",
        not_found_code=PACKAGE_NOT_FOUND,
        not_found_message=f"PyPI에 {params.name} 패키지가 없습니다",
    )
    if not fetched["ok"]:
        return fetched
    return safe_parse(parse_versions, fetched["data"])
