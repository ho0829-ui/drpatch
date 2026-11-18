"""실제 GMS + API로 한 세션에서 두 턴을 돌려 Memory(F3010)를 확인하는 스크립트. 테스트가 아니다.

    .venv/bin/python scripts/run_session.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.brain import GmsBrain  # noqa: E402
from app.agent.session import chat_turn, load_session, new_session_id, save_upload  # noqa: E402
from app.db import repo  # noqa: E402
from app.parsing.requirements import parse  # noqa: E402

FILE = "requests==2.19.0\ndjango==2.2.0\n-e git+https://github.com/me/tool.git#egg=tool\n"
TURNS = [
    "우분투 20 서버, 파이썬 3.8이야. 이번에 2개까지, 첫 점검은 11/21 22~24시, 격주로 계획 짜줘",
    "회차당 3개까지로 바꿔서 다시 짜줘",
]

repo.init_db()
sid = new_session_id()
parsed = parse(FILE).to_dict()
save_upload(sid, [{"name": p["name"], "version": p["version"]} for p in parsed["packages"]], parsed["excluded"])
brain = GmsBrain()
for message in TURNS:
    start = time.perf_counter()
    out = chat_turn(sid, message, brain)
    c = load_session(sid)["conditions"]
    rounds = [[i["name"] for i in r["items"]] for r in (out["plan"] or {}).get("rounds", [])]
    print(f"\n> {message}\n  의도 {out['intent']} / {time.perf_counter() - start:.1f}초 / 저장 {out['saved']}")
    print(f"  조건: OS {c.os_name} {c.os_version}, Python {c.python_version}, N={c.capacity}, "
          f"{c.first_date} {c.window_start}~{c.window_end}, {c.interval_days}일 간격, 패키지 {len(c.packages)}개")
    print(f"  회차: {rounds}")
