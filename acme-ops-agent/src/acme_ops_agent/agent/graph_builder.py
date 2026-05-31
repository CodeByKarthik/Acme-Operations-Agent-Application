from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import SecretStr

from acme_ops_agent.config import settings
from acme_ops_agent.utils.logger import get_logger

from .graph.conditions import route_after_router, should_continue
from .graph.registry import build_skill_nodes
from .graph.routing import DEFAULT_ROUTE, SKILL_ROUTES
from .mcp_client import MCPConnection
from .nodes import create_agent_node, create_router_node, create_tool_node
from .shared.state import AgentState

logger = get_logger(__name__)


def build_graph(
    tools: list[BaseTool],
    connection: MCPConnection,
) -> Any:
    """
    Build and compile the full agent graph.

    Called once per request because:
    - Tools are discovered dynamically from the MCP server
    - The MCPConnection carries the user's auth token
    - Skill nodes need the connection for data gathering

    Returns a compiled LangGraph ready for ainvoke().
    """

    # --- Shared LLM ---
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    )
    llm_with_tools = llm.bind_tools(tools)
    tool_executor = ToolNode(tools)

    # --- Create nodes ---
    router = create_router_node(llm)
    agent = create_agent_node(llm, llm_with_tools)
    tools_node = create_tool_node(tool_executor)
    skill_nodes = build_skill_nodes(connection=connection, llm=llm)

    # --- Assemble graph ---
    graph = StateGraph(AgentState)

    graph.add_node("router", router)
    graph.add_node("agent", agent)
    graph.add_node("tools", tools_node)

    for name, node_fn in skill_nodes.items():
        graph.add_node(name, node_fn)

    # --- Edges ---
    graph.add_edge(START, "router")

    # Router → branch
    route_map: dict[str, str] = {
        DEFAULT_ROUTE: "agent",
        **SKILL_ROUTES,
    }
    graph.add_conditional_edges("router", route_after_router, route_map)

    # Agent ReAct loop
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")

    # Skills → END
    for name in skill_nodes:
        graph.add_edge(name, END)

    compiled = graph.compile()

    logger.info(
        "Built agent graph | %d tools | %d skill routes",
        len(tools),
        len(skill_nodes),
    )

    return compiled
