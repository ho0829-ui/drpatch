"""LLM 클라이언트를 만드는 유일한 곳.

GMS는 OpenAI 호환 API라서 ChatOpenAI에 접속 주소만 바꿔 넘긴다.
키·주소·모델 이름은 모두 .env에서 읽고 코드에 쓰지 않는다.
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

REQUIRED_ENV = ("GMS_KEY", "GMS_BASE_URL", "LLM_MODEL")


class LLMConfigError(RuntimeError):
    """필요한 환경변수가 비어 있을 때. 메시지에는 변수 이름만 담고 값은 담지 않는다."""


def load_llm_config() -> dict[str, str]:
    load_dotenv()
    values = {name: os.getenv(name, "").strip() for name in REQUIRED_ENV}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise LLMConfigError(f".env에 값이 없습니다: {', '.join(missing)}")
    return values


def get_llm(temperature: float = 0, timeout: float = 30) -> ChatOpenAI:
    config = load_llm_config()
    return ChatOpenAI(
        api_key=config["GMS_KEY"],
        base_url=config["GMS_BASE_URL"],
        model=config["LLM_MODEL"],
        temperature=temperature,
        timeout=timeout,
        max_retries=1,
    )
