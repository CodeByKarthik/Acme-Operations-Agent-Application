from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from acme_ops_agent.agent.graph.conditions import MAX_TOOL_CALLS
from acme_ops_agent.agent.prompts import SYSTEM_PROMPT, TOOL_LIMIT_MESSAGE
from acme_ops_agent.agent.shared.state import AgentState
from acme_ops_agent.utils.logger import get_logger

logger = get_logger(__name__)


def create_agent_node(llm: ChatOpenAI, llm_with_tools: Any) -> Any:
    """
    Factory that returns the ReAct agent node function.

    Parameters:
        llm:            Base LLM (no tools bound) for forced responses.
        llm_with_tools: LLM with MCP tools bound for normal reasoning.
    """

    async def agent_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        configurable = config.get("configurable", {})
        username = configurable.get("username", "unknown")
        role = configurable.get("role", "unknown")

        system_prompt = SYSTEM_PROMPT.format(username=username, role=role)
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

        if state["tool_call_count"] >= MAX_TOOL_CALLS:
            logger.warning(
                "Tool call limit reached (%d), forcing response",
                MAX_TOOL_CALLS,
            )
            messages.append(SystemMessage(content=TOOL_LIMIT_MESSAGE))
            response = await llm.ainvoke(messages, config=config)
        else:
            response = await llm_with_tools.ainvoke(messages, config=config)

        return {"messages": [response]}

    return agent_node
