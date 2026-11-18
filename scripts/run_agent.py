"""실제 GMS LLM + 실제 API로 메인 Agent를 한 번 돌려보는 확인 스크립트. 테스트가 아니다.

    .venv/bin/python scripts/run_agent.py
    .venv/bin/python scripts/run_agent.py "Ubuntu 20.04 언제까지 지원돼?"
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.brain import GmsBrain  # noqa: E402
from app.agent.graph import run_agent  # noqa: E402
from app.agent.state import Conditions  # noqa: E402
from app.parsing.requirements import parse  # noqa: E402

FILE = "requests==2.19.0\ndjango==2.2.0\n-e git+https://github.com/me/tool.git#egg=tool\n"
MESSAGE = "우분투 20 서버, 파이썬 3.8이야. 이번에 2개까지, 첫 점검은 11/21 22~24시, 격주로 계획 짜줘"

message = sys.argv[1] if len(sys.argv) > 1 else MESSAGE
parsed = parse(FILE).to_dict()
conditions = Conditions(
    packages=[{"name": p["name"], "version": p["version"]} for p in parsed["packages"]],
    excluded=parsed["excluded"],
)


def show(event_type: str, payload: dict) -> None:
    if event_type in ("step_start", "step_end"):
        if event_type == "step_start":
            print(f"▶ {payload['step']}")
        return
    if event_type == "tool_result":
        status = "ok" if payload["ok"] else payload["error_code"]
        print(f"   {payload['tool']}({payload['args']}) {status} {payload['ms']}ms")
        return
    if event_type != "tool_call":
        print(f"   [{event_type}] {json.dumps(payload, ensure_ascii=False)}")


start = time.perf_counter()
out = run_agent(message, conditions, GmsBrain(), emit=show)
print(f"\n=== 의도: {out['intent']} / Tool 호출 {out['tool_calls']}번 / {time.perf_counter() - start:.1f}초")
print(f"=== 조건: {out['conditions'].model_dump(mode='json', exclude={'packages', 'excluded'})}")
print(f"=== 답:\n{out['answer']}")
