from sqlalchemy import select
from sqlalchemy.orm import Session

from acme_ops_agent.db.models import AppRole, AppUser
from acme_ops_agent.schema.auth_schema import AppUserDTO
from acme_ops_agent.common.exceptions import AppUserNotFoundError





class AppUserRepository:
    """
    Repository for performing database operations related
    to application users.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_user_by_username(self, username: str) -> AppUserDTO:
        """
        Retrieve an active app user by their username.
        
        Attributes:
        -----------
        - username: The username of the app user to retrieve.
        
        Returns:
        --------
        - An AppUserDTO containing the user's details.
        """
        stmt = (
            select(
                AppUser.id,
                AppUser.username,
                AppUser.email,
                AppUser.full_name,
                AppUser.is_active,
                AppRole.name.label("role"),
            )
            .join(AppRole, AppUser.role_id == AppRole.id)
            .where(AppUser.username == username)
            .where(AppUser.is_active.is_(True))
        )

        row = self.db.execute(stmt).mappings().one_or_none()

        if row is None:
            raise AppUserNotFoundError(f"Active app user not found: {username}")

        return AppUserDTO(
            id=str(row["id"]),
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=row["is_active"],
        )