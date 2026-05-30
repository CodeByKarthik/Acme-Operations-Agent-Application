from typing import Any, cast

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent # type: ignore[attr-defined]
from pydantic import SecretStr

from acme_ops_agent.config import settings
from acme_ops_agent.utils.logger import get_logger

from .prompts import SYSTEM_PROMPT

logger = get_logger(__name__)


def build_agent(tools: list[BaseTool]) -> Any:
    """
    Build a ReAct agent wired to the provided tools.

    The agent uses the system prompt from ``prompts.py``
    and the LLM configured in application settings.
    """
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    )

    agent = create_react_agent( # type: ignore[no-untyped-call]
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )

    logger.info(
        "Built ReAct agent with %d tools (model=%s)",
        len(tools),
        settings.llm_model,
    )

    return cast(Any, agent)