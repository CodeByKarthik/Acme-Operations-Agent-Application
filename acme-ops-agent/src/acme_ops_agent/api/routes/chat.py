from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends

from acme_ops_agent.api.auth import get_auth_context
from acme_ops_agent.schema.auth_schema import AuthContext
from acme_ops_agent.schema.chat_schema import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> ChatResponse:
    """
    Accept a user message and return a stubbed authenticated response.

    This proves the API chat boundary before LLM orchestration is added.
    """
    conversation_id = request.conversation_id or uuid4()

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=uuid4(),
        answer=(
            "Chat endpoint is working."
        ),
        authenticated_username=auth_context.username,
        authenticated_role=auth_context.role.value,
        created_at=datetime.now(UTC),
    )