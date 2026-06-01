from sqlalchemy import select

from ..models import AppRole, AppUser
from ..session import SessionLocal

ROLES = [
    ("sales_user", "Read-only access to customer and issue data"),
    ("support_user", "Read and update access for support issues"),
    ("admin", "Full administrative access"),
]

USERS = [
    {
        "username": "sales1",
        "email": "sales1@acme.test",
        "full_name": "Sarah Sales",
        "role": "sales_user",
    },
    {
        "username": "support1",
        "email": "support1@acme.test",
        "full_name": "Sam Support",
        "role": "support_user",
    },
    {
        "username": "admin1",
        "email": "admin1@acme.test",
        "full_name": "Anita Admin",
        "role": "admin",
    },
]


def main() -> None:
    db = SessionLocal()

    try:
        role_by_name: dict[str, AppRole] = {}

        for role_name, description in ROLES:
            role = db.scalar(select(AppRole).where(AppRole.name == role_name))

            if role is None:
                role = AppRole(
                    name=role_name,
                    description=description,
                )
                db.add(role)
                db.flush()

            role_by_name[role_name] = role

        for user_data in USERS:
            user = db.scalar(select(AppUser).where(AppUser.email == user_data["email"]))

            if user is None:
                role = role_by_name[user_data["role"]]

                db.add(
                    AppUser(
                        keycloak_user_id=None,
                        username=user_data["username"],
                        email=user_data["email"],
                        full_name=user_data["full_name"],
                        role_id=role.id,
                        is_active=True,
                    )
                )

        db.commit()
        print("Seeded app roles and users.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
