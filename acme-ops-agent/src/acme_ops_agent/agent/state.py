from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages  # type: ignore[import-untyped]
from typing_extensions import NotRequired, TypedDict


class AgentState(TypedDict):
    """
    State that flows through every node in the agent graph.

    messages:
        Conversation history. LangGraph's add_messages reducer handles append
        and dedup behavior.

    route:
        Intent route selected by the router. Example: "general" or
        "escalation_summary".

    tool_call_count:
        Count of general ReAct tool calls.

    skill_name / skill_completed / skill_error:
        Optional skill metadata for observability and debugging.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    route: str
    tool_call_count: int

    skill_name: NotRequired[str]
    skill_completed: NotRequired[bool]
    skill_error: NotRequired[str]