"""기획 검증 (요구사항 2.7): Tool 없이 LLM만 답하면 무엇이 틀리는지 실제로 물어보는 수동 확인 스크립트.

    .venv/bin/python scripts/check_llm_only.py

LLM 답을 화면에 보여주고, 옆에 tests/fixtures/의 실제 API 응답(2026-11-18 저장본)에서 계산한 값을 같이 보여준다.
맞고 틀림은 사람이 읽고 docs/planning-check.md에 적는다. 테스트가 아니다.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.llm import LLMConfigError, get_llm  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def eol_fact(name: str) -> str:
    r = load(name)
    r = r.get("result", r)
    return f"일반 지원 종료 {r['eolFrom']}, ESM 종료 {r.get('eoesFrom') or '없음'}, 최신 패치 {r['latest']['name']}"


def django_max_for_py38() -> str:
    """확인용 대략 계산(>=3.N 하한만 봄). 실제 판정 코드는 packaging으로 따로 만든다."""
    data = load("pypi_django_all")
    best = None
    for version, files in data["releases"].items():
        if not files or not re.fullmatch(r"\d+(\.\d+)*", version):
            continue
        if all(f.get("yanked") for f in files):
            continue
        req = files[0].get("requires_python") or ""
        low = re.search(r">=\s*3\.(\d+)", req)
        if low and int(low.group(1)) > 8:
            continue
        key = tuple(int(p) for p in version.split("."))
        best = max(best or key, key)
    latest = data["info"]["version"]
    return f"Python 3.8에서 설치 가능한 최신 {'.'.join(map(str, best))} (전체 최신 {latest})"


def osv_fact(name: str) -> str:
    groups = []
    for v in load(name).get("vulns", []):
        ids = {v["id"], *v.get("aliases", [])}
        sev = (v.get("database_specific") or {}).get("severity")
        for g in groups:
            if g["ids"] & ids:
                g["ids"] |= ids
                g["sev"] = g["sev"] or sev
                break
        else:
            groups.append({"ids": ids, "sev": sev})
    order = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
    top = min((order.index(g["sev"]) for g in groups if g["sev"] in order), default=None)
    return f"묶은 뒤 {len(groups)}건, 최고 등급 {order[top] if top is not None else '미상'}"


CASES = [
    ("Ubuntu 20.04 언제까지 지원돼? 일반 지원과 ESM 종료일을 날짜로 알려줘.",
     lambda: eol_fact("eol_ubuntu_20.04")),
    ("Python 3.8 서버인데 django 몇 버전으로 올리면 돼? 설치 가능한 가장 최신 버전 번호로 알려줘.",
     django_max_for_py38),
    ("requests 2.19.0에 알려진 취약점은 몇 건이고, 가장 심한 등급은 뭐야?",
     lambda: osv_fact("osv_requests_2.19.0")),
    ("Python 3.8은 언제 지원 종료됐어?",
     lambda: eol_fact("eol_python_3.8")),
    ("계획 짜줘", lambda: "입력(파일·OS·Python)이 없으므로 Tool 없이 되물어야 함"),
]


def main() -> int:
    try:
        llm = get_llm()
    except LLMConfigError as e:
        print(f"[설정 오류] {e}")
        return 1
    for i, (question, fact) in enumerate(CASES, 1):
        try:
            answer = llm.invoke(question).text
        except Exception as e:
            answer = f"(호출 실패: {type(e).__name__}: {e})"
        print(f"── {i}. {question}")
        print(f"[LLM만] {answer.strip()}")
        print(f"[실제 API 저장본] {fact()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
