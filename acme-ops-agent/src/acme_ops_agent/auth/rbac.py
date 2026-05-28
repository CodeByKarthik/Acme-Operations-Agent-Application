from acme_ops_agent.common.enums import AppRole
from ..common.exceptions import PermissionDenied
from acme_ops_agent.schema.auth_schema import AuthContext


READ_ROLES = {
    AppRole.SALES_USER,
    AppRole.SUPPORT_USER,
    AppRole.ADMIN,
}

WRITE_ROLES = {
    AppRole.SUPPORT_USER,
    AppRole.ADMIN,
}

ADMIN_ROLES = {
    AppRole.ADMIN,
}


def require_role(context: AuthContext, allowed_roles: set[AppRole]) -> None:
    allowed = {role.value for role in allowed_roles}

    if context.role not in allowed:
        raise PermissionDenied("User does not have the required role")


def can_read(context: AuthContext) -> bool:
    return context.role in {role.value for role in READ_ROLES}


def can_write(context: AuthContext) -> bool:
    return context.role in {role.value for role in WRITE_ROLES}


def is_admin(context: AuthContext) -> bool:
    return context.role == AppRole.ADMIN.value