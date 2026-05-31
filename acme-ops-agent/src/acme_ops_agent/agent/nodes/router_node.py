from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from acme_ops_agent.agent.graph.routing import DEFAULT_ROUTE, VALID_ROUTES
from acme_ops_agent.agent.prompts import ROUTER_PROMPT
from acme_ops_agent.agent.shared.state import AgentState
from acme_ops_agent.utils.logger import get_logger

logger = get_logger(__name__)


def create_router_node(llm: ChatOpenAI) -> Any:
    """
    Factory that returns a router node function.

    The router classifies the user's message into a route
    name that determines which graph branch handles the request.
    """

    async def router_node(
        state: AgentState, config: RunnableConfig
    ) -> dict[str, Any]:
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

    return router_node
