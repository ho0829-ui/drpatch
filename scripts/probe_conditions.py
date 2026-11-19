"""수동 점검 스크립트: tests/test_condition_phrases.py의 PHRASE_CASES를 실제 GmsBrain.analyze에 넣어 확인한다.

실행:
    .venv/bin/python scripts/probe_conditions.py
    .venv/bin/python scripts/probe_conditions.py --today 2026-11-19 --workers 6
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.brain import GmsBrain  # noqa: E402
from app.agent.graph import merge_conditions  # noqa: E402
from app.agent.state import Conditions  # noqa: E402
from tests.test_condition_phrases import PHRASE_CASES, PROBE_TODAY  # noqa: E402


def _check_one(brain: GmsBrain, today: date, phrase: str, expected: dict) -> tuple[str, list[str]]:
    base = Conditions(packages=[{"name": "requests", "version": "2.19.0"}])
    a = brain.analyze(phrase, base, today)
    merged = merge_conditions(base, a)
    diffs = []
    for k, exp in expected.items():
        if k == "interval_unsupported":
            got = a.interval_unsupported
        elif k == "first_date":
            got = merged.first_date.isoformat() if merged.first_date else None
        elif k == "os_version" and expected.get("os_name") == "windows":
            got = a.os_version
        else:
            got = getattr(merged, k)
            if k == "interval_days" and expected.get("weekdays"):
                # 요일과 같이 온 14는 week_interval=2로 바뀜
                got = 14 if merged.week_interval == 2 else (7 if merged.week_interval == 1 else None)
            elif k == "weekly_count" and expected.get("weekdays"):
                got = a.weekly_count
        if got != exp:
            diffs.append(f"{k}: expected={exp!r}, got={got!r} (raw={a.model_dump(exclude={'intent', 'intent_reason'})})")
    return phrase, diffs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=PROBE_TODAY.isoformat())
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    today = date.fromisoformat(args.today)
    brain = GmsBrain()

    mismatches = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(_check_one, brain, today, phrase, exp) for phrase, exp, _, _ in PHRASE_CASES]
        for f in as_completed(futs):
            phrase, diffs = f.result()
            if diffs:
                mismatches.append((phrase, diffs))

    print(f"총 {len(PHRASE_CASES)}건 점검 완료 — 일치 {len(PHRASE_CASES) - len(mismatches)}건, 불일치 {len(mismatches)}건")
    for phrase, diffs in mismatches:
        print(f"  [불일치] {phrase}")
        for d in diffs:
            print(f"    - {d}")


if __name__ == "__main__":
    main()
