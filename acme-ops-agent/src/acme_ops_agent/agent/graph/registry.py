from __future__ import annotations
from typing import Any, Callable
from langchain_openai import ChatOpenAI

from acme_ops_agent.agent.mcp_client import MCPConnection
from acme_ops_agent.agent.nodes.skill_node import create_escalation_summary_node

# Type alias for skill node builder functions
SkillNodeBuilder = Callable[..., Any]

SKILL_NODE_BUILDERS: dict[str, SkillNodeBuilder] = {
    "escalation_summary": create_escalation_summary_node,
    # "next_skill": create_next_skill_node,   ← register new skills here
}


def build_skill_nodes(
    connection: MCPConnection,
    llm: ChatOpenAI,
) -> dict[str, Any]:
    """
    Instantiate all registered skill nodes with their dependencies.

    Returns a dict of {route_name: node_function} ready to
    be added to the StateGraph.
    """
    nodes: dict[str, Any] = {}

    for name, builder in SKILL_NODE_BUILDERS.items():
        nodes[name] = builder(connection=connection, llm=llm)

    return nodes
