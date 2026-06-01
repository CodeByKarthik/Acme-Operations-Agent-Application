from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from acme_ops_agent.agent.mcp_client import MCPConnection
from acme_ops_agent.agent.shared.parsing import content_to_text
from acme_ops_agent.agent.shared.skill_limits import DEFAULT_SKILL_LIMITS, SkillLimits
from acme_ops_agent.agent.skills.escalation_summary import EscalationSummarySkill
from acme_ops_agent.agent.shared.state import AgentState


def create_escalation_summary_node(
    connection: MCPConnection,
    llm: ChatOpenAI,
    limits: SkillLimits = DEFAULT_SKILL_LIMITS,
) -> Any:
    """
    Factory that returns the escalation summary skill node.

    This node runs a deterministic multi-step workflow:
    data gathering via MCP tools, then LLM synthesis.
    """

    async def escalation_summary_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        skill = EscalationSummarySkill(
            connection=connection,
            llm=llm,
            limits=limits,
        )

        last_message = state["messages"][-1]
        user_text = content_to_text(getattr(last_message, "content"))  # type: ignore[arg-type]

        result = await skill.execute(user_text)

        messages: list[Any] = []
        if result.raw_data: # type: ignore
            messages.append(
                ToolMessage(
                    content=result.raw_data, # type: ignore
                    tool_call_id="skill_context",
                    name="escalation_summary",
                )
            )
        messages.append(AIMessage(content=result.answer)) # type: ignore
        return {"messages": messages}

    return escalation_summary_node
