from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from acme_ops_agent.config import settings
from acme_ops_agent.schema.auth_schema import AuthContext
from acme_ops_agent.utils.logger import get_logger

from .graph_builder import build_graph
from .mcp_client import connect_mcp
from .shared.tool_adapter import create_mcp_tools

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
        if isinstance(msg, ToolMessage) and isinstance(msg.content, str):  # type: ignore[reportUnknownMemberType]
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
    Stateless service — a new MCP session and agent graph are
    created per request so each call carries the correct user token.
    """

    def __init__(self) -> None:
        self.mcp_url = f"http://{settings.mcp_host}:{settings.mcp_port}/mcp"

    def _build_config(
        self,
        auth_context: AuthContext | None,
        conversation_id: str | None,
    ) -> dict[str, Any]:
        """
        Build the RunnableConfig passed to graph.ainvoke().

        Serves three purposes:
        - configurable: runtime values nodes need (auth context)
        - metadata: attached to the LangSmith trace root
        - tags: filterable labels in LangSmith
        """
        username = auth_context.username if auth_context else "unknown"
        role = auth_context.role.value if auth_context else "unknown"
        user_id = auth_context.app_user_id if auth_context else ""

        return {
            "run_name": "acme_ops_chat",
            "configurable": {
                "username": username,
                "role": role,
                "user_id": user_id,
                "conversation_id": conversation_id or "",
            },
            "metadata": {
                "username": username,
                "user_id": user_id,
                "role": role,
                "conversation_id": conversation_id or "",
                "route": "/api/chat",
                "app_version": settings.app_version,
            },
            "tags": [
                "api_chat",
                f"role:{role}",
            ],
        }

    async def run(
        self,
        message: str,
        token: str,
        auth_context: AuthContext | None = None,
        conversation_id: str | None = None,
    ) -> str:
        """
        Execute the agent graph for a single user query.

        Returns the agent's final text answer.
        """
        username = auth_context.username if auth_context else "unknown"
        logger.info("Agent run started | user: %s | message: %.100s", username, message)

        config = self._build_config(auth_context, conversation_id)

        async with connect_mcp(self.mcp_url, token) as connection:
            tools = await create_mcp_tools(connection)
            graph = build_graph(tools, connection)

            result = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=message)],
                    "route": "",
                    "tool_call_count": 0,
                },
                config=config,
            )

            messages = result.get("messages", [])

            # --- Post-run logging ---
            tool_names = _collect_tool_names(messages)
            for name in tool_names:
                config["tags"].append(f"tool:{name}")

            if _detect_rbac_denial(messages):
                config["tags"].append("rbac_denied")
                logger.info("RBAC denial detected in tool responses")

            route = result.get("route", "unknown")
            logger.info(
                "Agent run completed | route: %s | tools_called: %s | tags: %s",
                route,
                tool_names,
                config["tags"],
            )

            # --- Extract final answer ---
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:  # type: ignore[reportUnknownMemberType]
                    return str(msg.content)  # type: ignore[reportUnknownMemberType,reportUnknownArgumentType]

        logger.warning("Agent produced no final response")
        return "I was unable to process your request. Please try again."
