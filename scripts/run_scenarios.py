"""대표 시나리오를 켜져 있는 서버(실제 GMS + 실제 API)에 HTTP로 보내 확인하는 스크립트. 테스트가 아니다.

    (서버 켜기) .venv/bin/uvicorn app.main:app --port 8000
    .venv/bin/python scripts/run_scenarios.py            # 대표 시나리오 5개
    .venv/bin/python scripts/run_scenarios.py --big      # 패키지 20개 응답 시간
"""

import json
import sys
import time

import requests

BASE = "http://localhost:8000"

SMALL = """requests==2.19.0
django==2.2.0
flask==1.0
jinja2==2.10
urllib3==1.23
pyyaml==5.1
-e git+https://github.com/me/tool.git#egg=tool
celery>=4.0
"""

BIG = """requests==2.19.0
django==2.2.0
flask==1.0
jinja2==2.10
urllib3==1.23
pyyaml==5.1
pillow==6.0.0
cryptography==2.3
paramiko==2.4.1
sqlalchemy==1.3.0
werkzeug==0.15.0
idna==2.7
certifi==2018.8.24
chardet==3.0.4
six==1.12.0
click==7.0
itsdangerous==1.1.0
markupsafe==1.1.0
gunicorn==19.9.0
lxml==4.2.5
"""


def upload(text: str) -> str:
    r = requests.post(f"{BASE}/upload", data=text.encode(), timeout=30)
    r.raise_for_status()
    body = r.json()
    print(f"  업로드: 조회 {len(body['packages'])}개, 제외 {[(e['line_no'], e['reason']) for e in body['excluded']]}")
    return body["session_id"]


def chat(session_id: str | None, message: str) -> tuple[dict, list[dict], float]:
    start = time.perf_counter()
    events, final = [], None
    with requests.post(f"{BASE}/chat", json={"session_id": session_id, "message": message}, stream=True, timeout=300) as r:
        for line in r.iter_lines():
            if not line:
                continue
            e = json.loads(line)
            if e["type"] == "final":
                final = e
            else:
                events.append(e)
    return final, events, time.perf_counter() - start


def show(title: str, final: dict, events: list[dict], took: float) -> None:
    tools = [e for e in events if e["type"] == "tool_result"]
    failed = [e for e in tools if not e["ok"]]
    replans = [e for e in events if e["type"] == "replan"]
    print(f"\n### {title}\n  의도 {final['intent']} / {took:.1f}초 / Tool {len(tools)}번(실패 {len(failed)}) / 재계획 {len(replans)}번")
    if final.get("missing"):
        print(f"  되물음: {final['missing']}")
    plan = final.get("plan")
    if plan:
        for r in plan["rounds"]:
            print(f"  {r['round_no']}회차 {r['date']}: " + ", ".join(
                f"{i['name']} {i['current_version']}→{i['target_version']}({i['severity']})" for i in r["items"]))
        for key in ("unassigned", "safe", "unchecked", "held"):
            if plan[key]:
                print(f"  {key}: {plan[key]}")
    if final.get("confirmed") is not None:
        print(f"  저장: {[(p['round_no'], p['date'], len(p['overlaps'])) for p in final['confirmed']]}")
    print("  답: " + final["answer"].replace("\n", " ")[:300])


def scenarios() -> None:
    print("1) 파일 + '이번에 5개 올릴 계획'")
    sid = upload(SMALL)
    final, events, took = chat(sid, "Ubuntu 20.04, Python 3.8 서버야. 이 파일 기준으로 이번에 5개 올릴 계획 짜줘. 첫 점검은 11/21 22~24시, 격주로")
    show("1) 계획 5개까지", final, events, took)

    final, events, took = chat(sid, "1회차 확정해줘")
    show("5) 1회차 확정", final, events, took)

    final, events, took = chat(None, "Python 3.8 서버인데 django 몇으로 올리면 돼?")
    show("2) django 몇으로 (사실 조회)", final, events, took)

    sid3 = upload(SMALL)
    final, events, took = chat(sid3, "Ubuntu 20.04, Python 3.8 서버인데 지금 뭐부터 해야 돼?")
    show("3) 지금 뭐부터", final, events, took)

    final, events, took = chat(None, "계획 짜줘")
    show("4) 파일 없이 계획 짜줘", final, events, took)


def big() -> None:
    sid = upload(BIG)
    final, events, took = chat(sid, "Ubuntu 22.04, Python 3.8 서버야. 이번에 5개까지, 첫 점검은 11/21 22~24시, 격주로 계획 짜줘")
    show("패키지 20개", final, events, took)
    # 단계별 시간: step_start 사이 간격
    steps = [e for e in events if e["type"] in ("step_start",)]
    print("  단계 순서:", " → ".join(e["step"] for e in steps))


if __name__ == "__main__":
    big() if "--big" in sys.argv else scenarios()
