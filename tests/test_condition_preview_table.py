"""조건 칩 입력창 미리보기(conditionPreview.js) 정규식·표시 예문 표 테스트 (네트워크 없음, spec v1.21 M·N)."""

from __future__ import annotations

import re
from pathlib import Path

from app.agent.schedule_text import fmt_schedule

PREVIEW_JS = Path(__file__).resolve().parent.parent / "frontend" / "src" / "conditionPreview.js"

# frontend/src/conditionPreview.js PATTERNS와 같은 패턴 문자열
PATTERNS = {
    "os": r"(?:Ubuntu|우분투)\s+\d{2}(?:\.\d{2})?|(?:jammy|noble|focal|bionic)|(?:macOS|OS\s*X|맥OS|맥북|맥)\s+\d{2}(?:\.\d+)?|(?:Windows|윈도우)\s+1[01]\s+\d{2}H[12]|(?:세쿼이아|타호|소노마|벤투라)",
    "python_version": r"(?:Python|파이썬|py)\s*\d+(?:\.\d+|\d{2})",
    "capacity": r"(?:한\s*번에\s*(?:\d+|한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*개(?:\s*까지)?|(?:\d+|한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*개씩|(?:최대\s*)?\d+\s*개(?:\s*(?:까지|이하))?|(?:다섯|여섯|일곱|여덟|아홉|열)\s*개)",
    "first_date": r"(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}|(?:다음\s*달|\d{1,2}월)\s*\d{1,2}일|(?:다음\s*주|이번\s*주|다음)\s*[월화수목금토일]요일|(?<!\d)\d{1,2}일(?!\s*마다)|내일|모레|오늘)",
    "interval_days": r"(?:매일|격일|이틀에\s*한\s*번|사흘\s*마다|매주|격주|매달|매월|한\s*달에\s*한\s*번|분기\s*마다|주\s*\d+\s*회|일주일에\s*(?:\d+|한|두|세|네|다섯)\s*번|\d+\s*일\s*마다|\d+\s*주\s*(?:마다|간격|에\s*한\s*번)|평일|주말|[월화수목금토일](?:·[월화수목금토일])+|[월화수목금토일]{2,7}(?=\s|$|으로|마다)|[월화수목금토일]요일(?:\s*[,·]?\s*[월화수목금토일]요일)+)",
}
UNSUPPORTED_WEEK_ORDINAL = r"(?:매달|매월|\d{1,2}월)\s*(?:첫|둘|셋|넷|마지막|\d+)째?\s*주"

EXAMPLES = [
    ("Ubuntu 22.04, Python 3.10, 한 번에 2개, 첫 점검은 11/25부터 매주",
     {"os", "python_version", "capacity", "first_date", "interval_days"}),
    ("우분투 20.04, 파이썬 3.8, 5개씩, 다음 화요일, 격주",
     {"os", "python_version", "capacity", "first_date", "interval_days"}),
    ("맥북 15, py 3.11", {"os", "python_version"}),
    ("세쿼이아, Python 3.12, 한 번에 3개까지, 12월 1일, 14일마다",
     {"os", "python_version", "capacity", "first_date", "interval_days"}),
    ("윈도우 11 24H2, 2026-12-01, 매달", {"os", "first_date", "interval_days"}),
    ("Ubuntu 18.04, Ubuntu 24.04, macOS 14", {"os"}),
    # spec v1.21 N 확장 표현
    ("매일", {"interval_days"}),
    ("격일", {"interval_days"}),
    ("이틀에 한 번", {"interval_days"}),
    ("사흘마다", {"interval_days"}),
    ("3주 간격", {"interval_days"}),
    ("2주에 한 번", {"interval_days"}),
    ("한 달에 한 번", {"interval_days"}),
    ("분기마다", {"interval_days"}),
    ("주 2회", {"interval_days"}),
    ("평일", {"interval_days"}),
    ("주말", {"interval_days"}),
    ("매주 화·목", {"interval_days"}),
    ("화요일 목요일", {"interval_days"}),
    ("월수금", {"interval_days"}),
    ("다음 주 월요일", {"first_date"}),
    ("이번 주 금요일", {"first_date"}),
    ("25일", {"first_date"}),
    ("다음 달 3일", {"first_date"}),
    ("다섯 개", {"capacity"}),
    ("최대 4개", {"capacity"}),
    ("10개 이하", {"capacity"}),
    ("jammy", {"os"}),
    ("noble", {"os"}),
    ("우분투 22", {"os"}),
    ("py311", {"python_version"}),
    ("파이썬3.11", {"python_version"}),
    # 서버가 못 정하는 표현 → ○를 띄우지 않음
    ("12월 첫째 주", set()),
    ("매달 첫째 주 화요일", set()),
    ("안녕하세요", set()),
]

# app/agent/schedule_text.py와 frontend/src/conditionPreview.js fmtSchedule 공통 예 표
SCHEDULE_FORMAT_EXAMPLES = [
    ({"interval_days": 1}, "매일"),
    ({"interval_days": 2}, "격일"),
    ({"interval_days": 7}, "매주"),
    ({"interval_days": 14}, "격주"),
    ({"interval_days": 21}, "3주마다"),
    ({"interval_days": 30}, "매월"),
    ({"interval_days": 90}, "분기마다"),
    ({"interval_days": 5}, "5일마다"),
    ({"weekdays": [1, 3], "week_interval": 1}, "매주 화·목"),
    ({"weekdays": [0, 1, 2, 3, 4], "week_interval": 1}, "평일"),
    ({"weekdays": [5, 6], "week_interval": 1}, "주말"),
    ({"weekdays": [1, 4], "week_interval": 2}, "격주 화·금"),
    ({"weekly_count": 2}, "주 2회 (요일 필요)"),
]


def _preview(text: str) -> set[str]:
    unsupported = bool(re.search(UNSUPPORTED_WEEK_ORDINAL, text, re.IGNORECASE))
    found = set()
    for k, pat in PATTERNS.items():
        if unsupported and k == "interval_days":
            continue
        if re.search(pat, text, re.IGNORECASE):
            found.add(k)
    return found


def test_condition_preview_js_has_matching_patterns():
    src = PREVIEW_JS.read_text(encoding="utf-8")
    for key, pat in PATTERNS.items():
        js_escaped = pat.replace("\\", "\\\\")
        assert f"{key}: '{js_escaped}'" in src, f"pattern mismatch for {key}"
    ord_escaped = UNSUPPORTED_WEEK_ORDINAL.replace("\\", "\\\\")
    assert f"UNSUPPORTED_WEEK_ORDINAL = '{ord_escaped}'" in src


def test_condition_preview_example_table():
    for text, expected in EXAMPLES:
        assert _preview(text) == expected, text


def test_schedule_format_matches_server_and_js_doc():
    src = PREVIEW_JS.read_text(encoding="utf-8")
    for cond, expected in SCHEDULE_FORMAT_EXAMPLES:
        assert fmt_schedule(cond) == expected, cond
        assert f'→ "{expected}"' in src, f"missing doc entry for {expected}"
