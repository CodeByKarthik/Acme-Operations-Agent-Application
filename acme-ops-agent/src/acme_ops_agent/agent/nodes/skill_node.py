from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from acme_ops_agent.agent.mcp_client import MCPConnection
from acme_ops_agent.agent.skills.escalation_summary import EscalationSummarySkill
from acme_ops_agent.agent.shared.state import AgentState


def create_escalation_summary_node(
    connection: MCPConnection,
    llm: ChatOpenAI,
) -> Any:
    """
    Factory that returns the escalation summary skill node.

    This node runs a deterministic multi-step workflow:
    data gathering via MCP tools, then LLM synthesis.
    """

    async def escalation_summary_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        skill = EscalationSummarySkill(connection=connection, llm=llm)

        last_message = state["messages"][-1]
        user_text = (
            last_message.content
            if isinstance(last_message.content, str)  # type: ignore
            else str(last_message.content)  # type: ignore
        )

        summary = await skill.execute(user_text)
        return {"messages": [AIMessage(content=summary)]}

    return escalation_summary_node
