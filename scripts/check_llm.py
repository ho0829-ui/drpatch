"""도구 연결 확인 (요구사항 2.7): 실제 GMS를 부르는 수동 확인 스크립트. 테스트가 아니다.

    .venv/bin/python scripts/check_llm.py

① LLM을 한 번 호출해 응답을 받는다.
② Tool 명세를 넘기고 대표 요청마다 LLM이 어떤 Tool을 고르는지 본다. Tool은 실행하지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm import LLMConfigError, get_llm, load_llm_config  # noqa: E402
from app.tools.specs import TOOL_SPECS  # noqa: E402

SYSTEM = (
    "너는 서버 패치 계획을 돕는 Agent다. 필요한 정보가 있으면 주어진 Tool을 골라 호출을 요청한다. "
    "requirements.txt 파일이나 OS·Python 버전처럼 Tool 입력에 필요한 값이 없으면 Tool을 부르지 말고 먼저 되묻는다."
)

CASES = [
    ("Ubuntu 20.04 언제까지 지원돼?", {"get_eol"}),
    ("requests 2.19.0 버전 써도 안전해?", {"get_vulns"}),
    ("Python 3.8 서버인데 django 몇 버전까지 설치할 수 있어?", {"get_package_versions"}),
    ("계획 짜줘", set()),
]


def main() -> int:
    try:
        config = load_llm_config()
        llm = get_llm()
    except LLMConfigError as e:
        print(f"[설정 오류] {e}")
        return 1
    print(f"모델: {config['LLM_MODEL']} / 주소: {config['GMS_BASE_URL']}\n")

    print("① LLM 한 번 호출")
    try:
        reply = llm.invoke("한 문장으로 인사해줘.")
    except Exception as e:  # 확인 스크립트라 원인을 그대로 보여준다
        print(f"  실패: {type(e).__name__}: {e}")
        return 1
    print(f"  응답: {reply.text}\n")

    print("② Tool 선택 확인")
    llm_with_tools = llm.bind_tools(TOOL_SPECS)
    passed = 0
    for question, expected in CASES:
        try:
            msg = llm_with_tools.invoke([("system", SYSTEM), ("human", question)])
        except Exception as e:
            print(f"  [실패] {question}\n      {type(e).__name__}: {e}")
            continue
        chosen = {call["name"] for call in msg.tool_calls}
        ok = chosen == expected
        passed += ok
        print(f"  [{'OK' if ok else '다름'}] {question}")
        print(f"      예상: {sorted(expected) or '호출 없음'} / 실제: {sorted(chosen) or '호출 없음'}")
        for call in msg.tool_calls:
            print(f"      {call['name']}({call['args']})")
        if not msg.tool_calls:
            print(f"      응답: {msg.text[:150]}")
    print(f"\n결과: {passed}/{len(CASES)} 예상대로")
    return 0 if passed == len(CASES) else 2


if __name__ == "__main__":
    sys.exit(main())
