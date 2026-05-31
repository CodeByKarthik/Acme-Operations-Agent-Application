from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import SecretStr

from acme_ops_agent.config import settings
from acme_ops_agent.utils.logger import get_logger

from .mcp_client import MCPConnection
from .prompts import ROUTER_PROMPT, SYSTEM_PROMPT, TOOL_LIMIT_MESSAGE
from .skills.escalation_summary import EscalationSummarySkill
from .state import AgentState

logger = get_logger(__name__)

# ---- Configuration -----

MAX_TOOL_CALLS = 15

SKILL_ROUTES: dict[str, str] = {
    "escalation_summary": "escalation_summary",
    # "next_skill": "next_skill_node_name",   ← add new skills here
}

DEFAULT_ROUTE = "general"
VALID_ROUTES = set(SKILL_ROUTES.keys()) | {DEFAULT_ROUTE}


# ---- Graph builder -----


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
    """
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    )

    llm_with_tools = llm.bind_tools(tools)
    tool_executor = ToolNode(tools)


    # ---- Node: Router — classify intent -----

    async def router_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Lightweight LLM call to classify the user's intent.
        Defaults to 'general' for unrecognised routes.
        """
        last_message = state["messages"][-1]
        user_text = (
            last_message.content
            if isinstance(last_message.content, str)
            else str(last_message.content)
        )

        response = await llm.ainvoke(
            [
                SystemMessage(content=ROUTER_PROMPT),
                HumanMessage(content=user_text),
            ],
            config=config,
        )

        route = response.content.strip().lower().strip('"').strip("'")

        if route not in VALID_ROUTES:
            logger.warning(
                "Router returned unknown route '%s', defaulting to '%s'",
                route,
                DEFAULT_ROUTE,
            )
            route = DEFAULT_ROUTE

        logger.info("Router classified intent as: %s", route)
        return {"route": route}


    # ---- Node: Agent — LLM reasoning with tool selection -----


    async def agent_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Call the LLM with the conversation history.

        If the tool call limit has been reached, the LLM is
        called without tool bindings, forcing it to respond
        with the information gathered so far.
        """
        configurable = config.get("configurable", {})
        username = configurable.get("username", "unknown")
        role = configurable.get("role", "unknown")

        system_prompt = SYSTEM_PROMPT.format(username=username, role=role)
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

        if state["tool_call_count"] >= MAX_TOOL_CALLS:
            logger.warning("Tool call limit reached (%d), forcing response", MAX_TOOL_CALLS)
            messages.append(SystemMessage(content=TOOL_LIMIT_MESSAGE))
            response = await llm.ainvoke(messages, config=config)
        else:
            response = await llm_with_tools.ainvoke(messages, config=config)

        return {"messages": [response]}


    # ---- Node: Tools — execute tool calls + count -----

    async def tool_node_with_count(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Execute pending tool calls and increment the counter.
        """
        result = await tool_executor.ainvoke(state, config=config)
        new_messages = result.get("messages", [])

        return {
            "messages": new_messages,
            "tool_call_count": state["tool_call_count"] + len(new_messages),
        }


    # ---- Node: Escalation Summary Skill ----

    async def escalation_summary_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Run the Customer Escalation Summary skill.

        This is a deterministic multi-step workflow, not a
        reasoning loop. The skill controls the data-gathering
        sequence; the LLM only handles extraction and synthesis.
        """
        skill = EscalationSummarySkill(connection=connection, llm=llm)

        last_message = state["messages"][-1]
        user_text = (
            last_message.content
            if isinstance(last_message.content, str)
            else str(last_message.content)
        )

        summary = await skill.execute(user_text)
        return {"messages": [AIMessage(content=summary)]}


    # ---- Edge conditions ----

    def route_after_router(state: AgentState) -> str:
        """Direct traffic based on the router's classification."""
        return state["route"]

    def should_continue(
        state: AgentState,
    ) -> Literal["tools", "end"]:
        """
        After the agent node, decide whether to execute
        tool calls or finish.
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

    # ---- Assemble graph ----

    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("router", router_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node_with_count)
    graph.add_node("escalation_summary", escalation_summary_node)

    # Entry point
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

    # Skill → END
    graph.add_edge("escalation_summary", END)

    compiled = graph.compile()

    logger.info(
        "Built custom agent graph | %d tools | %d skill routes | max_tool_calls=%d",
        len(tools),
        len(SKILL_ROUTES),
        MAX_TOOL_CALLS,
    )

    return compiled