from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from acme_ops_shared.auth.keycloak import KeycloakTokenVerifier
from acme_ops_shared.common.exceptions import AuthError, PermissionDenied
from acme_ops_shared.db.repositories.business_read_repository import \
    BusinessReadRepository
from acme_ops_shared.db.repositories.business_write_repository import \
    BusinessWriteRepository
from acme_ops_shared.db.repositories.user_repository import AppUserRepository
from acme_ops_shared.db.session import SessionLocal
from acme_ops_shared.services.auth_context_service import AuthContextService
from acme_ops_shared.services.business_service import BusinessService
from fastmcp.dependencies import CurrentHeaders
from fastmcp.exceptions import ToolError


def extract_bearer_token(headers: dict[str, str]) -> str:
    """
    Extract a bearer token from HTTP Authorization headers.
    """
    authorization = headers.get("authorization") or headers.get("Authorization")

    if not authorization:
        raise ToolError("Missing Authorization header")

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise ToolError("Authorization header must use Bearer token format")

    return token


@asynccontextmanager
async def get_business_service(
    headers: dict[str, str] = CurrentHeaders(),  # type: ignore[reportCallIssue]
) -> AsyncIterator[BusinessService]:
    """
    Build a permission-aware BusinessService for the current MCP request.
    """
    token = extract_bearer_token(headers)

    with SessionLocal() as session:
        try:
            auth_service = AuthContextService(
                token_verifier=KeycloakTokenVerifier(),
                user_repository=AppUserRepository(session),
            )
            auth_context = auth_service.authenticate(token)

            yield BusinessService(
                read_repository=BusinessReadRepository(session),
                write_repository=BusinessWriteRepository(session),
                auth_context=auth_context,
            )

            session.commit()

        except (AuthError, PermissionDenied) as exc:
            session.rollback()
            raise ToolError(str(exc)) from exc

        except Exception:
            session.rollback()
            raise