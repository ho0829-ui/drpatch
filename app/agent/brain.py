"""LLM이 맡는 판단만 모은 곳 (spec "LLM이 하는 일"). 그래프는 AgentBrain 인터페이스만 안다.

- 의도 분류 + 조건 추출 (analyze)
- Tool 종류·순서 계획 (plan_tools)
- 재계획 방식 선택 (choose_replan)
- 사실 조회 답 (answer_fact): LLM이 Tool을 고르고, 실행은 우리 코드(runner)가
- 최종 응답 문장 (write_response), 그 밖의 대화 (chat)

계산(버전 비교·정렬·회차)은 여기 없다. 테스트는 이 인터페이스를 가짜로 바꿔 끼운다.
"""

import json
from datetime import date
from typing import Literal, Protocol

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field

from app.agent.runner import ToolRunner
from app.agent.state import Conditions

ToolName = Literal["get_eol", "get_vulns", "get_package_versions"]
FACT_TOOL_ROUNDS = 3  # 사실 조회에서 Tool을 이어 부를 수 있는 횟수


class Analysis(BaseModel):
    intent: Literal["plan", "fact", "confirm", "other"] = Field(
        description="plan=패치 계획 세우기·고치기, fact=OS·Python 지원 기간이나 패키지 취약점·버전 같은 사실 질문, "
        "confirm=제안한 계획을 확정·저장해 달라는 요청, other=그 밖의 대화"
    )
    intent_reason: str = Field(description="그렇게 분류한 이유 한 문장")
    os_name: str | None = Field(None, description="이번 메시지에 나온 OS 이름(소문자). 예: ubuntu. 없으면 null")
    os_version: str | None = Field(None, description="OS 버전. '우분투 20'이면 20.04. 없으면 null")
    python_version: str | None = Field(None, description="Python 버전. 예: 3.8. 없으면 null")
    capacity: int | None = Field(None, description="'이번에 5개까지' → 5. 없으면 null")
    first_date: str | None = Field(None, description="첫 점검 날짜 YYYY-MM-DD. 연도가 없으면 오늘 이후 가장 가까운 날. 없으면 null")
    window_start: str | None = Field(None, description="시작 시각 HH:MM. '22~24시'면 22:00. 없으면 null")
    window_end: str | None = Field(None, description="끝 시각 HH:MM. '22~24시'면 24:00. 없으면 null")
    interval_days: int | None = Field(None, description="매주=7, 격주=14, 매월=30, 'N일마다'=N. 없으면 null")
    confirm_rounds: list[int] | None = Field(
        None, description="확정 요청에서 회차를 말했으면 그 번호들. '1회차 확정해줘' → [1]. 회차를 말하지 않았으면 null(전체)")


class ToolPlan(BaseModel):
    steps: list[ToolName] = Field(description="부를 Tool 이름을 부를 순서대로. 필요 없는 Tool은 빼기")
    reason: str = Field(description="이 순서로 정한 이유 한 문장")


class ReplanChoice(BaseModel):
    strategy: Literal["upgrade_python", "hold"] = Field(
        description="upgrade_python=Python을 올려 안전한 버전으로 가는 계획을 세움, hold=이 패키지들은 보류"
    )
    reason: str = Field(description="고른 이유 한 문장")


class AgentBrain(Protocol):
    def analyze(self, message: str, conditions: Conditions, today: date,
                last_turn: dict | None = None) -> Analysis: ...
    def plan_tools(self, conditions: Conditions) -> ToolPlan: ...
    def choose_replan(self, violations: list[dict], python_version: str, message: str = "") -> ReplanChoice: ...
    def answer_fact(self, message: str, runner: ToolRunner, conditions: Conditions | None = None) -> str: ...
    def write_response(self, summary: dict) -> str: ...
    def chat(self, message: str) -> str: ...


SYSTEM = (
    "너는 서버 패치·EOL 점검 플래너의 Agent다. 사용자는 pip freeze로 만든 requirements.txt와 OS·Python 버전을 주고, "
    "회차별 패치 계획을 받는다. 계산(버전 비교, 정렬, 회차 나누기)은 코드가 하므로 너는 하지 않는다. "
    "API로 확인하지 않은 값(날짜, 등급, 버전)을 지어내지 않는다."
)


class GmsBrain:
    """SSAFY GMS(OpenAI 호환) LLM으로 구현."""

    def __init__(self, llm=None, tool_specs: list[dict] | None = None):
        from app.llm import get_llm
        from app.tools.specs import llm_tool_specs

        self.llm = llm or get_llm()
        self.tool_specs = tool_specs or llm_tool_specs()

    def _structured(self, schema, prompt: str):
        return self.llm.with_structured_output(schema).invoke([SystemMessage(SYSTEM), HumanMessage(prompt)])

    def analyze(self, message: str, conditions: Conditions, today: date,
                last_turn: dict | None = None) -> Analysis:
        known = conditions.model_dump(mode="json", exclude={"packages", "excluded"})
        previous = ""
        if last_turn and last_turn.get("message"):
            previous = (f"직전 대화 — 사용자: {last_turn['message']} / 너의 답(앞부분): "
                        f"{(last_turn.get('answer') or '')[:400]}\n")
        prompt = (
            f"오늘은 {today.isoformat()}이다. 지금까지 알고 있는 조건: {json.dumps(known, ensure_ascii=False)}. "
            f"올린 패키지 수: {len(conditions.packages)}개.\n{previous}"
            "아래 사용자 메시지의 의도를 분류하고, **이번 메시지에 새로 나온 조건만** 채워라. 나오지 않은 값은 null.\n"
            f"사용자 메시지: {message}"
        )
        return self._structured(Analysis, prompt)

    def plan_tools(self, conditions: Conditions) -> ToolPlan:
        tools = "\n".join(f"- {t['function']['name']}: {t['function']['description']}" for t in self.tool_specs)
        names = ", ".join(f"{p['name']}=={p['version']}" for p in conditions.packages[:20])
        prompt = (
            f"OS {conditions.os_name} {conditions.os_version}, Python {conditions.python_version} 서버의 패치 계획을 세운다.\n"
            f"코드가 이미 가지고 있는 패키지 {len(conditions.packages)}개: {names}"
            f"{' 외' if len(conditions.packages) > 20 else ''}\n쓸 수 있는 Tool:\n{tools}\n"
            "어떤 Tool을 어떤 순서로 부를지 정하라. 패키지마다 반복 호출하는 것은 코드가 하므로 Tool 이름만 쓴다."
        )
        return self._structured(ToolPlan, prompt)

    def choose_replan(self, violations: list[dict], python_version: str, message: str = "") -> ReplanChoice:
        prompt = (
            f"Python {python_version}에서는 아래 패키지를 취약점 없는 버전으로 올릴 수 없다: "
            f"{json.dumps(violations, ensure_ascii=False)}.\n"
            f"사용자 메시지: {message}\n"
            "기본은 upgrade_python(Python을 올려 안전한 버전으로 가는 계획)이다. "
            "사용자가 'Python은 못 올린다', '버전 유지' 처럼 Python 업그레이드를 명시적으로 거부했을 때만 hold를 골라라."
        )
        return self._structured(ReplanChoice, prompt)

    def answer_fact(self, message: str, runner: ToolRunner, conditions: Conditions | None = None) -> str:
        """LLM이 Tool을 고르고(최소 1번), 실행·계산은 코드가 한다. 버전 목록 원본은 LLM에 주지 않는다."""
        from app.agent.fact_tools import run_fact_tool

        python = conditions.python_version if conditions else None
        messages = [
            SystemMessage(SYSTEM + " 사실 질문에는 반드시 Tool 결과를 근거로 답한다. 'installable_latest'처럼 "
                          "코드가 계산한 값은 그대로 쓰고, 버전을 스스로 비교하거나 고르지 않는다. "
                          f"사용자의 Python 버전: {python or '모름'}."),
            HumanMessage(message),
        ]
        tool_llm = self.llm.bind_tools(self.tool_specs)
        reply = self.llm.bind_tools(self.tool_specs, tool_choice="required").invoke(messages)
        for _ in range(FACT_TOOL_ROUNDS):
            if not reply.tool_calls:
                break
            messages.append(reply)
            for call in reply.tool_calls:
                result = run_fact_tool(runner, call["name"], call["args"], python)
                messages.append(ToolMessage(json.dumps(result, ensure_ascii=False), tool_call_id=call["id"]))
            reply = tool_llm.invoke(messages)
        if reply.tool_calls:  # 횟수를 다 쓰고도 더 부르려 하면 지금까지 결과로 답하게 한다
            messages.append(HumanMessage("지금까지의 Tool 결과만으로 답하라."))
            reply = self.llm.invoke(messages)
        return reply.text

    def write_response(self, summary: dict) -> str:
        prompt = (
            "아래는 코드가 계산한 패치 계획이다. 숫자·버전·날짜를 바꾸지 말고, 사용자에게 한국어로 짧게 설명하라. "
            "rounds가 비어 있고 priority가 있으면 회차 대신 priority 순서대로 '무엇부터' 할지 설명하라 (일정은 코드가 따로 묻는다). "
            "rounds·priority·held 같은 필드 이름은 사용자에게 말하지 말고 우리말로 풀어 써라. "
            "회차별 항목(현재 → 목표 버전)과 이유, Python 업그레이드가 들어갔다면 그 이유, "
            "안전·확인 못 함·보류·미배정 목록이 있으면 함께 밝혀라.\n"
            f"{json.dumps(summary, ensure_ascii=False)}"
        )
        return self.llm.invoke([SystemMessage(SYSTEM), HumanMessage(prompt)]).text

    def chat(self, message: str) -> str:
        return self.llm.invoke([SystemMessage(SYSTEM + " 계획과 관계없는 말에는 짧게 답하고, 할 수 있는 일을 안내한다."),
                                HumanMessage(message)]).text
