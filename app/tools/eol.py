"""get_eol: endoflife.date로 OS·Python 지원 종료일 조회 (F3004, 기준 차이 밝히기는 F3002)."""

from urllib.parse import quote

from app.tools import http
from app.tools.base import NO_EOL_DATE, PRODUCT_NOT_FOUND, UPSTREAM_ERROR, fail, ok
from app.tools.specs import EolInput

BASE_URL = "https://endoflife.date/api/v1/products"

# 줄기가 "주.부" 두 자리인 제품. 패치 번호가 붙어 오면 잘라서 조회한다.
TWO_PART_CYCLE_PRODUCTS = {"ubuntu", "python"}


def normalize_cycle(product: str, cycle: str) -> str:
    parts = cycle.split(".")
    if product in TWO_PART_CYCLE_PRODUCTS and len(parts) > 2:
        return ".".join(parts[:2])
    return cycle


def parse_eol(body: dict, *, product: str, requested_cycle: str, queried_cycle: str) -> dict:
    release = body.get("result", body) if isinstance(body, dict) else None
    if not isinstance(release, dict):
        return fail(UPSTREAM_ERROR, "endoflife.date 응답 형식이 예상과 다릅니다")

    eol_date = release.get("eolFrom")
    if not eol_date:
        return fail(NO_EOL_DATE, f"{product} {queried_cycle}의 지원 종료일 정보가 없습니다")

    latest = release.get("latest") or {}
    note = None
    if queried_cycle != requested_cycle:
        note = f"요청한 {requested_cycle} 대신 릴리스 줄기 {queried_cycle} 기준으로 조회했습니다"

    return ok(
        {
            "eol_date": eol_date,
            "esm_date": release.get("eoesFrom"),  # 없으면 null (확인 못 함)
            "is_eol": bool(release.get("isEol")),
            "lts": bool(release.get("isLts")),
            "latest_patch": latest.get("name"),
            "label": release.get("label") or f"{product} {queried_cycle}",
            "link": latest.get("link"),
            "queried_cycle": queried_cycle,
            "note": note,
        }
    )


def get_eol(params: EolInput) -> dict:
    product = params.product.lower()
    queried_cycle = normalize_cycle(product, params.cycle)
    url = f"{BASE_URL}/{quote(product, safe='')}/releases/{quote(queried_cycle, safe='')}"
    fetched = http.fetch_json(
        "GET",
        url,
        not_found_code=PRODUCT_NOT_FOUND,
        # endoflife.date는 제품이 없을 때와 줄기가 없을 때 둘 다 같은 404 페이지를 준다 (2026-11-18 확인)
        not_found_message=f"endoflife.date에 {product} {queried_cycle} 정보가 없습니다 (제품 이름이나 버전을 확인하세요)",
    )
    if not fetched["ok"]:
        return fetched
    return parse_eol(
        fetched["data"], product=product, requested_cycle=params.cycle, queried_cycle=queried_cycle
    )
