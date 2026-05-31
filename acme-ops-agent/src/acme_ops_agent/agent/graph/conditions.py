from __future__ import annotations
from typing import Literal

from langchain_core.messages import AIMessage
from acme_ops_agent.agent.shared.state import AgentState
from acme_ops_agent.agent.graph.routing import BLOCKED_ROUTE

MAX_TOOL_CALLS = 15


def route_after_guardrail(state: AgentState) -> Literal["safe", "blocked"]:
    """
    After the guardrail node, decide whether the request
    is safe to proceed or should be blocked.
    """
    if state["route"] == BLOCKED_ROUTE:
        return "blocked"
    return "safe"


def route_after_router(state: AgentState) -> str:
    """
    Read the route set by the router node and return it
    as the conditional edge key.
    """
    return state["route"]


def should_continue(
    state: AgentState,
) -> Literal["tools", "end"]:
    """
    After the agent node, decide whether to execute
    pending tool calls or finish the response.

    Returns 'end' if:
    - The LLM did not request any tool calls, or
    - The tool call safety limit has been reached
    """
    last_message = state["messages"][-1]

    has_tool_calls = (
        isinstance(last_message, AIMessage)
        and hasattr(last_message, "tool_calls")
        and last_message.tool_calls
    )

    if has_tool_calls and state["tool_call_count"] < MAX_TOOL_CALLS:
        return "tools"

    return "end"
