"""
Agent service that orchestrates the full execution pipeline.

Sequence per request:
1. Open an authenticated MCP session (bearer token forwarded)
2. Discover and wrap MCP tools as LangChain tools
3. Build the LangGraph ReAct agent
4. Invoke the agent with the user's message
5. Extract and return the final answer
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from acme_ops_agent.config import settings
from acme_ops_agent.utils.logger import get_logger

from .graph import build_agent
from .mcp_client import connect_mcp
from .tool_adapter import create_mcp_tools

logger = get_logger(__name__)


class AgentService:
    """
    Stateless service — a new MCP session and agent are created
    per request so that each call carries the correct user token.
    """

    def __init__(self) -> None:
        self.mcp_url = (
            f"http://{settings.mcp_host}:{settings.mcp_port}/mcp"
        )

    async def run(self, message: str, token: str) -> str:
        """
        Execute the agent for a single user query.

        Returns the agent's final text answer.
        """
        logger.info("Agent run started | message: %.100s", message)

        async with connect_mcp(self.mcp_url, token) as connection:
            tools = await create_mcp_tools(connection)
            agent = build_agent(tools)

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
            )

            messages = result.get("messages", [])

            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    logger.info("Agent run completed successfully")
                    return str(msg.content)

        logger.warning("Agent produced no final response")
        return "I was unable to process your request. Please try again."