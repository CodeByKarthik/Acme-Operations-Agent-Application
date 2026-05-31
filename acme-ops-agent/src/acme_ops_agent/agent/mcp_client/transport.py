from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from acme_ops_agent.utils.logger import get_logger

from .client_connection import MCPConnection

logger = get_logger(__name__)


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
