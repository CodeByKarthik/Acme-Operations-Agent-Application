from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Header

from acme_ops_agent.agent.service import AgentService
from acme_ops_agent.api.auth import extract_bearer_token, get_auth_context
from acme_ops_agent.schema.auth_schema import AuthContext
from acme_ops_agent.schema.chat_schema import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])

_agent_service = AgentService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
    auth_context: AuthContext = Depends(get_auth_context),
) -> ChatResponse:
    """
    Accept a user message, run the agent, and return the response.

    The bearer token is forwarded to the MCP server so that
    tool calls respect the user's RBAC permissions.
    """
    token = extract_bearer_token(authorization)
    conversation_id = request.conversation_id or uuid4()

    answer = await _agent_service.run(request.message, token)

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=uuid4(),
        answer=answer,
        authenticated_username=auth_context.username,
        authenticated_role=auth_context.role.value,
        created_at=datetime.now(UTC),
    )