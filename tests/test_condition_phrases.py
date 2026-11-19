"""조건 표현 표 테스트 (네트워크 없음, spec v1.21 N).

PHRASE_CASES는 scripts/probe_conditions.py에서도 import해 실제 GmsBrain.analyze 점검에 쓴다.
각 항목: (입력 문장, 기대 Analysis 필드 dict, 기대 fmt_schedule 결과, interval_days가 missing인지)
"""

from __future__ import annotations

from datetime import date

from app.agent.brain import Analysis
from app.agent.graph import merge_conditions
from app.agent.schedule_text import fmt_schedule
from app.agent.state import Conditions, missing_inputs

PROBE_TODAY = date(2026, 11, 19)  # 목요일 (spec v1.21 실측 기준일)

# (phrase, expected_fields, expected_schedule_text, expect_interval_missing)
PHRASE_CASES: list[tuple[str, dict, str | None, bool]] = [
    # ── 간격 (실측 35개 중 간격) ────────────────────────────
    ("매일 점검", {"interval_days": 1}, "매일", False),
    ("격일로 진행", {"interval_days": 2}, "격일", False),
    ("이틀에 한 번", {"interval_days": 2}, "격일", False),
    ("사흘마다", {"interval_days": 3}, "3일마다", False),
    ("5일마다", {"interval_days": 5}, "5일마다", False),
    ("매주", {"interval_days": 7}, "매주", False),
    ("주 1회", {"interval_days": 7}, "매주", False),
    ("격주", {"interval_days": 14}, "격주", False),
    ("2주에 한 번", {"interval_days": 14}, "격주", False),
    ("3주 간격", {"interval_days": 21}, "3주마다", False),
    ("매월", {"interval_days": 30}, "매월", False),
    ("한 달에 한 번", {"interval_days": 30}, "매월", False),
    ("분기마다", {"interval_days": 90}, "분기마다", False),
    # ── 날짜 (오늘 2026-11-19 목요일 기준) ───────────────────
    ("다음 주 월요일부터", {"first_date": "2026-11-23"}, None, True),
    ("이번 주 금요일부터", {"first_date": "2026-11-20"}, None, True),
    ("내일부터", {"first_date": "2026-11-20"}, None, True),
    ("모레부터", {"first_date": "2026-11-21"}, None, True),
    ("25일부터", {"first_date": "2026-11-25"}, None, True),
    ("11/25부터", {"first_date": "2026-11-25"}, None, True),
    ("다음 달 3일부터", {"first_date": "2026-12-03"}, None, True),
    # ── 개수 ────────────────────────────────────────────────
    ("한 번에 다섯 개까지", {"capacity": 5}, None, True),
    ("세 개씩 올려줘", {"capacity": 3}, None, True),
    ("10개 이하로", {"capacity": 10}, None, True),
    ("최대 4개", {"capacity": 4}, None, True),
    # ── 시각 ────────────────────────────────────────────────
    ("밤 10시~자정", {"window_start": "22:00", "window_end": "24:00"}, None, True),
    ("새벽 2~4시", {"window_start": "02:00", "window_end": "04:00"}, None, True),
    ("22시부터 2시간", {"window_start": "22:00", "window_end": "24:00"}, None, True),
    # ── OS·Python ───────────────────────────────────────────
    ("우분투 22", {"os_name": "ubuntu", "os_version": "22.04"}, None, True),
    ("Ubuntu jammy", {"os_name": "ubuntu", "os_version": "22.04"}, None, True),
    ("Ubuntu noble", {"os_name": "ubuntu", "os_version": "24.04"}, None, True),
    ("맥북 세쿼이아", {"os_name": "macos", "os_version": "15"}, None, True),
    ("윈도우 11 24H2", {"os_name": "windows", "os_version": "11 24H2"}, None, True),
    ("py311", {"python_version": "3.11"}, None, True),
    ("파이썬3.11", {"python_version": "3.11"}, None, True),
    ("12월 첫째 주에 시작", {"first_date": None}, None, True),
    # ── 요일 규칙 (spec v1.21 M, 10개 이상) ─────────────────
    ("매주 화·목", {"weekdays": [1, 3]}, "매주 화·목", False),
    ("화요일 목요일마다", {"weekdays": [1, 3]}, "매주 화·목", False),
    ("월수금으로 해줘", {"weekdays": [0, 2, 4]}, "매주 월·수·금", False),
    ("평일마다 점검", {"weekdays": [0, 1, 2, 3, 4]}, "평일", False),
    ("주말에만 점검", {"weekdays": [5, 6]}, "주말", False),
    ("격주 화·금", {"weekdays": [1, 4], "interval_days": 14}, "격주 화·금", False),
    ("매주 금요일", {"weekdays": [4]}, "매주 금", False),
    ("매주 월·수", {"weekdays": [0, 2]}, "매주 월·수", False),
    ("주 2회로 해줘", {"weekly_count": 2}, "주 2회 (요일 필요)", True),
    ("일주일에 두 번", {"weekly_count": 2}, "주 2회 (요일 필요)", True),
    ("주 3회 월수금", {"weekdays": [0, 2, 4]}, "매주 월·수·금", False),
    ("매달 첫째 주 화요일", {"interval_unsupported": True}, "", True),
]


def test_condition_phrases_table_merge_missing_and_format():
    assert len(PHRASE_CASES) >= 45
    base = Conditions(
        packages=[{"name": "requests", "version": "2.19.0"}],
        os_name="ubuntu",
        os_version="22.04",
        python_version="3.11",
        capacity=3,
        first_date=date(2026, 11, 24),
    )

    for phrase, fields, expected_sched, expect_interval_missing in PHRASE_CASES:
        analysis = Analysis(intent="plan", intent_reason="테스트", **fields)
        merged = merge_conditions(base, analysis)
        missing = missing_inputs(merged)
        assert ("interval_days" in missing) is expect_interval_missing, phrase
        if expected_sched is not None:
            assert fmt_schedule(merged) == expected_sched, phrase
