"""조건 칩 입력창 미리보기(conditionPreview.js) 정규식 예문 표 테스트 (네트워크 없음)."""

from __future__ import annotations

import re
from pathlib import Path

PREVIEW_JS = Path(__file__).resolve().parent.parent / "frontend" / "src" / "conditionPreview.js"

# frontend/src/conditionPreview.js PATTERNS와 같은 패턴 문자열
PATTERNS = {
    "os": r"(?:Ubuntu|우분투)\s+\d{2}\.\d{2}|(?:macOS|OS\s*X|맥OS|맥북|맥)\s+\d{2}(?:\.\d+)?|(?:Windows|윈도우)\s+1[01]\s+\d{2}H[12]|(?:세쿼이아|타호|소노마|벤투라)",
    "python_version": r"(?:Python|파이썬|py)\s*\d+\.\d+",
    "capacity": r"(?:한\s*번에\s*\d+\s*개(?:\s*까지)?|\d+\s*개씩|\d+\s*개\s*까지)",
    "first_date": r"(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}|\d{1,2}월\s*\d{1,2}일|다음\s*[월화수목금토일]요일|내일|모레|오늘)",
    "interval_days": r"(?:매주|격주|매달|매월|\d+\s*일\s*마다|\d+\s*주\s*마다)",
}

EXAMPLES = [
    (
        "Ubuntu 22.04, Python 3.10, 한 번에 2개, 첫 점검은 11/25부터 매주",
        {"os", "python_version", "capacity", "first_date", "interval_days"},
    ),
    (
        "우분투 20.04, 파이썬 3.8, 5개씩, 다음 화요일, 격주",
        {"os", "python_version", "capacity", "first_date", "interval_days"},
    ),
    (
        "맥북 15, py 3.11",
        {"os", "python_version"},
    ),
    (
        "세쿼이아, Python 3.12, 한 번에 3개까지, 12월 1일, 14일마다",
        {"os", "python_version", "capacity", "first_date", "interval_days"},
    ),
    (
        "윈도우 11 24H2, 2026-12-01, 매달",
        {"os", "first_date", "interval_days"},
    ),
    (
        "Ubuntu 18.04, Ubuntu 24.04, macOS 14",
        {"os"},
    ),
    (
        "안녕하세요",
        set(),
    ),
]


def _preview(text: str) -> set[str]:
    return {k for k, pat in PATTERNS.items() if re.search(pat, text, re.IGNORECASE)}


def test_condition_preview_js_has_matching_patterns():
    src = PREVIEW_JS.read_text(encoding="utf-8")
    for key, pat in PATTERNS.items():
        # JS 문자열 리터럴에서는 역슬래시가 두 번(\\) 적힌다
        js_escaped = pat.replace("\\", "\\\\")
        assert f"{key}: '{js_escaped}'" in src, f"pattern mismatch for {key}"


def test_condition_preview_example_table():
    for text, expected in EXAMPLES:
        assert _preview(text) == expected, text
