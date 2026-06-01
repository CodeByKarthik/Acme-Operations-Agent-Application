from acme_ops_shared.common.enums import AppRole
from ..common.exceptions import PermissionDenied
from acme_ops_shared.schema.auth_schema import AuthContext


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
    """
    Enforce that the authenticated user has one
    of the allowed roles.
    """
    if context.role not in allowed_roles:
        raise PermissionDenied("User does not have the required role")


def can_read(context: AuthContext) -> bool:
    """
    Check if the user has read permission.
    """
    return context.role in READ_ROLES


def can_write(context: AuthContext) -> bool:
    """
    Check if the user has write/modify permission.
    """
    return context.role in WRITE_ROLES


def is_admin(context: AuthContext) -> bool:
    """
    Check if the user has admin privileges.
    """
    return context.role == AppRole.ADMIN