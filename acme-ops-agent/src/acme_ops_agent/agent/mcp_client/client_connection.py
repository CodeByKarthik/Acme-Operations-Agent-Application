from __future__ import annotations

import json
from typing import Any

from mcp import ClientSession
from mcp.types import Tool as MCPToolDefinition

from acme_ops_agent.utils.logger import get_logger

from .result_parser import extract_text_content

logger = get_logger(__name__)


class MCPConnection:
    """
    Active authenticated connection to the MCP server.

    Provides tool discovery (cached per connection) and
    tool invocation with result serialisation.
    """

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._tools: list[MCPToolDefinition] | None = None

    async def list_tools(self) -> list[MCPToolDefinition]:
        """
        Discover available MCP tools.

        Results are cached for the lifetime of the connection so
        multiple calls within a single agent run do not re-fetch.
        """
        if self._tools is None:
            result = await self._session.list_tools()
            self._tools = result.tools
            logger.info("Discovered %d MCP tools", len(self._tools))
        return self._tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> str:
        """
        Invoke an MCP tool and return the serialised text result.

        If the MCP server returns an error (e.g. RBAC denial),
        the error message is prefixed with ``Error:`` so the
        agent can reason about it.
        """
        logger.info(
            "MCP tool call: %s | args: %s",
            name,
            json.dumps(arguments, default=str),
        )

        result = await self._session.call_tool(name, arguments)
        response = extract_text_content(result.content)

        if result.isError:
            logger.warning("MCP tool %s returned error: %s", name, response)
            return f"Error: {response}"

        logger.info("MCP tool %s completed successfully", name)
        return response
