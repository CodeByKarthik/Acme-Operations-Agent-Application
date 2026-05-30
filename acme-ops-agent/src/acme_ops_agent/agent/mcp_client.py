import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Tool as MCPToolDefinition, TextContent

from acme_ops_agent.utils.logger import get_logger

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

        texts: list[str] = []
        for block in result.content:
            if isinstance(block, TextContent):
                texts.append(block.text)

        response = "\n".join(texts) if texts else "No output returned"

        if result.isError:
            logger.warning("MCP tool %s returned error: %s", name, response)
            return f"Error: {response}"

        logger.info("MCP tool %s completed successfully", name)
        return response


@asynccontextmanager
async def connect_mcp(
    url: str,
    token: str,
) -> AsyncIterator[MCPConnection]:
    """
    Open an authenticated MCP client session.

    The bearer token is forwarded to the MCP server on every
    request so that server-side RBAC can enforce permissions.

    The connection remains open for the lifetime of the context
    manager, allowing the agent to make multiple tool calls
    within a single reasoning loop.
    """
    headers = {"Authorization": f"Bearer {token}"}
    http_client = httpx.AsyncClient(headers=headers)

    async with http_client:
        async with streamable_http_client(
            url=url,
            http_client=http_client,
        ) as (read_stream, write_stream, _):

            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                logger.info("MCP session established: %s", url)
                yield MCPConnection(session)