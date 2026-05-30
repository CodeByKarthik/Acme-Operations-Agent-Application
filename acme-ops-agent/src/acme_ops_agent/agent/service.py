"""
Agent service that orchestrates the full execution pipeline.

Sequence per request:
1. Open an authenticated MCP session (bearer token forwarded)
2. Discover and wrap MCP tools as LangChain tools
3. Build the LangGraph ReAct agent
4. Invoke the agent with the user's message and trace config
5. Extract and return the final answer
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from acme_ops_agent.config import settings
from acme_ops_agent.schema.auth_schema import AuthContext
from acme_ops_agent.utils.logger import get_logger

from .graph import build_agent
from .mcp_client import connect_mcp
from .tool_adapter import create_mcp_tools

logger = get_logger(__name__)

_RBAC_ERROR_MARKERS = [
    "does not have the required role",
    "permission denied",
    "not permitted",
]


def _detect_rbac_denial(messages: list[Any]) -> bool:
    """
    Scan tool responses for RBAC denial indicators.
    """
    for msg in messages:
        if isinstance(msg, ToolMessage) and isinstance(msg.content, str):
            content_lower = msg.content.lower()
            if any(marker in content_lower for marker in _RBAC_ERROR_MARKERS):
                return True
    return False


def _collect_tool_names(messages: list[Any]) -> list[str]:
    """
    Extract unique tool names from the message history.
    """
    seen: set[str] = set()
    names: list[str] = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name and msg.name not in seen:
            seen.add(msg.name)
            names.append(msg.name)
    return names


class AgentService:
    """
    Stateless service — a new MCP session and agent are created
    per request so that each call carries the correct user token.
    """

    def __init__(self) -> None:
        self.mcp_url = (
            f"http://{settings.mcp_host}:{settings.mcp_port}/mcp"
        )

    def _build_trace_config(
        self,
        auth_context: AuthContext | None,
        conversation_id: str | None,
    ) -> dict[str, Any]:
        """
        Build LangSmith-compatible RunnableConfig with metadata and tags.

        Metadata attaches structured data to the trace root.
        Tags enable filtering and grouping in the LangSmith UI.
        """
        metadata: dict[str, Any] = {
            "route": "/api/chat",
            "app_version": settings.app_version,
        }

        tags: list[str] = ["api_chat"]

        if auth_context:
            metadata["username"] = auth_context.username
            metadata["user_id"] = auth_context.app_user_id
            metadata["role"] = auth_context.role.value
            tags.append(f"role:{auth_context.role.value}")

        if conversation_id:
            metadata["conversation_id"] = conversation_id

        return {
            "run_name": "acme_ops_chat",
            "metadata": metadata,
            "tags": tags,
        }

    async def run(
        self,
        message: str,
        token: str,
        auth_context: AuthContext | None = None,
        conversation_id: str | None = None,
    ) -> str:
        """
        Execute the agent for a single user query.

        Returns the agent's final text answer.
        """
        logger.info(
            "Agent run started | user: %s | message: %.100s",
            auth_context.username if auth_context else "unknown",
            message,
        )

        trace_config = self._build_trace_config(auth_context, conversation_id)

        async with connect_mcp(self.mcp_url, token) as connection:
            tools = await create_mcp_tools(connection)
            agent = build_agent(tools)

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=trace_config,
            )

            messages = result.get("messages", [])

            # --- Post-run trace enrichment ---
            tool_names = _collect_tool_names(messages)
            for name in tool_names:
                trace_config["tags"].append(f"tool:{name}")

            if _detect_rbac_denial(messages):
                trace_config["tags"].append("rbac_denied")
                logger.info("RBAC denial detected in tool responses")

            logger.info(
                "Agent run completed | tools_called: %s | tags: %s",
                tool_names,
                trace_config["tags"],
            )

            # --- Extract final answer ---
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    return str(msg.content)

        logger.warning("Agent produced no final response")
        return "I was unable to process your request. Please try again."