from uuid import UUID
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from acme_ops_shared.common.enums import (
    CustomerHealthEnum,
    CustomerTierEnum,
    IssuePriorityEnum,
    IssueStatusEnum,
    NextActionStatusEnum,
    NextActionTypeEnum,
)
from acme_ops_shared.db.models.business import Customer, Issue, IssueUpdate, NextAction
from acme_ops_shared.db.models.user import AppUser
from acme_ops_shared.db.session import SessionLocal


def get_user_by_username(session: Session, username: str) -> AppUser:
    """
    Helper function to retrieve a user by username. Raises an
    exception if the user is not found. 
    
    Attributes:
    -----------
    - session: SQLAlchemy Session object for database access.
    - username: The username of the user to retrieve.
    """
    user = session.scalar(select(AppUser).where(AppUser.username == username))
    if user is None:
        raise RuntimeError(
            f"Required seed user '{username}' not found. "
            "Run seed_users before seed_business_data."
        )
    return user


def get_or_create_customer(
    session: Session,
    *,
    name: str,
    industry: str,
    tier: CustomerTierEnum,
    health_status: CustomerHealthEnum,
    account_owner_user_id: UUID | None,
    contract_value: Decimal,
    notes: str,
) -> Customer:
    """
    Retrieves an existing customer by name or creates a new 
    one if it doesn't exist.
    
    Attributes:
    - session: SQLAlchemy Session object for database access.
    - name: Name of the customer (must be unique).
    - industry: Industry vertical of the customer.
    - tier: Customer tier (e.g., enterprise, mid-market).
    - health_status: Current health status of the customer.
    - account_owner_user_id: User ID of the account 
      owner (sales representative).
    - contract_value: Total contract value for the customer.
    - notes: Additional notes about the customer.
    """
    existing = session.scalar(select(Customer).where(Customer.name == name))
    if existing is not None:
        return existing

    customer = Customer(
        name=name,
        industry=industry,
        tier=tier,
        health_status=health_status,
        account_owner_user_id=account_owner_user_id,
        contract_value=contract_value,
        notes=notes,
    )
    session.add(customer)
    session.flush()
    return customer


def get_or_create_issue(
    session: Session,
    *,
    external_ref: str,
    customer_id : UUID,
    title: str,
    description: str,
    status: IssueStatusEnum,
    priority: IssuePriorityEnum,
    assigned_to_user_id : UUID | None,
    source_system: str,
    opened_at: datetime,
    due_at: datetime | None,
) -> Issue:
    """
    Retrieves an existing issue by external reference or creates a new
    one if it doesn't exist.
    
    Attributes:
    -----------
    - session: SQLAlchemy Session object for database access.
    - external_ref: Unique external reference for the 
      issue (e.g., from a support system).
    - customer_id: ID of the associated customer.
    - title: Short title describing the issue.
    - description: Detailed description of the issue.
    - status: Current status of the issue (e.g., open, in progress).
    - priority: Priority level of the issue (e.g., P1, P2).
    - assigned_to_user_id: User ID of the support agent 
      assigned to the issue.
    - source_system: Name of the external system where 
      the issue originated.
    - opened_at: Timestamp when the issue was opened.
    - due_at: Timestamp when the issue is due to be resolved.
    """
    existing = session.scalar(select(Issue).where(Issue.external_ref == external_ref))
    if existing is not None:
        return existing

    issue = Issue(
        external_ref=external_ref,
        customer_id=customer_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        assigned_to_user_id=assigned_to_user_id,
        source_system=source_system,
        opened_at=opened_at,
        due_at=due_at,
    )
    session.add(issue)
    session.flush()
    return issue


def add_issue_update_if_missing(
    session: Session,
    *,
    issue_id : UUID,
    author_user_id : UUID | None,
    author_name: str,
    author_role: str,
    update_text: str,
    is_customer_visible: bool,
    created_at: datetime,
) -> None:
    """
    Adds an issue update if an identical update does not
    already exist for the issue.
    
    Attributes:
    -----------
    - session: SQLAlchemy Session object for database access.
    - issue_id: ID of the issue to which the update belongs.
    - author_user_id: User ID of the update author 
      (can be null for system updates).
    - author_name: Name of the update author (for display purposes).
    - author_role: Role of the update author (e.g., support_user, admin).
    - update_text: Text content of the issue update.
    - is_customer_visible: Whether this update should be 
      visible to the customer.
    - created_at: Timestamp when the update was created.
    """
    existing = session.scalar(
        select(IssueUpdate).where(
            IssueUpdate.issue_id == issue_id,
            IssueUpdate.update_text == update_text,
        )
    )
    if existing is not None:
        return

    session.add(
        IssueUpdate(
            issue_id=issue_id,
            author_user_id=author_user_id,
            author_name=author_name,
            author_role=author_role,
            update_text=update_text,
            is_customer_visible=is_customer_visible,
            created_at=created_at,
        )
    )


def add_next_action_if_missing(
    session: Session,
    *,
    issue_id : UUID,
    action_type: NextActionTypeEnum,
    action_text: str,
    owner_user_id : UUID | None,
    due_at: datetime | None,
    status: NextActionStatusEnum,
    created_by_user_id : UUID | None,
    created_by_role: str,
) -> None:
    """
    Adds a next action to an issue if an identical action does not
    already exist for the issue.
    
    Attributes:
    -----------
    - session: SQLAlchemy Session object for database access.
    - issue_id: ID of the issue to which the next action belongs.
    - action_type: Type of the next action (e.g., 
      technical investigation, customer update).
    - action_text: Text describing the next action to be taken.
    - owner_user_id: User ID of the person responsible for the next action.
    - due_at: Timestamp when the next action is due.
    - status: Current status of the next action (e.g., open, completed).
    - created_by_user_id: User ID of the person who created the next action.
    - created_by_role: Role of the person who created the 
      next action (e.g., support_user, admin).
    """
    existing = session.scalar(
        select(NextAction).where(
            NextAction.issue_id == issue_id,
            NextAction.action_text == action_text,
        )
    )
    if existing is not None:
        return

    session.add(
        NextAction(
            issue_id=issue_id,
            action_type=action_type,
            action_text=action_text,
            owner_user_id=owner_user_id,
            due_at=due_at,
            status=status,
            created_by_user_id=created_by_user_id,
            created_by_role=created_by_role,
        )
    )


def seed_business_data() -> None:
    """
    Seeds the database with sample business data
    including customers, issues, issue updates
    and next actions.
    """
    now = datetime.now(UTC)

    with SessionLocal() as session:
        sales_user = get_user_by_username(session, "sales1")
        support_user = get_user_by_username(session, "support1")
        admin_user = get_user_by_username(session, "admin1")

        globex = get_or_create_customer(
            session,
            name="Globex Corporation",
            industry="Financial Services",
            tier=CustomerTierEnum.ENTERPRISE,
            health_status=CustomerHealthEnum.AT_RISK,
            account_owner_user_id=sales_user.id,
            contract_value=Decimal("250000.00"),
            notes="Strategic enterprise customer. Executive team is sensitive to support delays.",
        )

        initech = get_or_create_customer(
            session,
            name="Initech",
            industry="Technology",
            tier=CustomerTierEnum.MID_MARKET,
            health_status=CustomerHealthEnum.HEALTHY,
            account_owner_user_id=sales_user.id,
            contract_value=Decimal("85000.00"),
            notes="Generally healthy account with moderate product usage growth.",
        )

        umbrella = get_or_create_customer(
            session,
            name="Umbrella Retail",
            industry="Retail",
            tier=CustomerTierEnum.ENTERPRISE,
            health_status=CustomerHealthEnum.WATCH,
            account_owner_user_id=sales_user.id,
            contract_value=Decimal("175000.00"),
            notes="Expansion opportunity, but recent integration issues need close monitoring.",
        )

        issue_101 = get_or_create_issue(
            session,
            external_ref="ISSUE-101",
            customer_id=globex.id,
            title="Billing exports failing for enterprise finance team",
            description=(
                "Scheduled billing exports are timing out before completion. "
                "Customer finance team cannot close monthly reporting."
            ),
            status=IssueStatusEnum.OPEN,
            priority=IssuePriorityEnum.P1,
            assigned_to_user_id=support_user.id,
            source_system="acme-support",
            opened_at=now - timedelta(days=2),
            due_at=now + timedelta(days=1),
        )

        issue_102 = get_or_create_issue(
            session,
            external_ref="ISSUE-102",
            customer_id=globex.id,
            title="SSO login failures after certificate rotation",
            description=(
                "Several Globex users cannot authenticate through SAML SSO "
                "after the customer rotated their identity provider certificate."
            ),
            status=IssueStatusEnum.IN_PROGRESS,
            priority=IssuePriorityEnum.P2,
            assigned_to_user_id=support_user.id,
            source_system="acme-support",
            opened_at=now - timedelta(days=5),
            due_at=now + timedelta(days=3),
        )

        issue_201 = get_or_create_issue(
            session,
            external_ref="ISSUE-201",
            customer_id=initech.id,
            title="Dashboard filters slow on large date ranges",
            description=(
                "Customer reports that dashboard filtering becomes slow when "
                "using date ranges longer than six months."
            ),
            status=IssueStatusEnum.OPEN,
            priority=IssuePriorityEnum.P3,
            assigned_to_user_id=support_user.id,
            source_system="acme-support",
            opened_at=now - timedelta(days=1),
            due_at=now + timedelta(days=7),
        )

        issue_301 = get_or_create_issue(
            session,
            external_ref="ISSUE-301",
            customer_id=umbrella.id,
            title="Inventory sync delayed for regional stores",
            description=(
                "Inventory updates from regional stores are delayed before "
                "appearing in the operations dashboard."
            ),
            status=IssueStatusEnum.BLOCKED,
            priority=IssuePriorityEnum.P2,
            assigned_to_user_id=support_user.id,
            source_system="acme-support",
            opened_at=now - timedelta(days=4),
            due_at=now + timedelta(days=2),
        )

        add_issue_update_if_missing(
            session,
            issue_id=issue_101.id,
            author_user_id=support_user.id,
            author_name="Support User",
            author_role="support_user",
            update_text=(
                "Confirmed export job timeout in production logs. "
                "Customer is blocked on month-end finance reporting."
            ),
            is_customer_visible=True,
            created_at=now - timedelta(days=2, hours=-2),
        )

        add_issue_update_if_missing(
            session,
            issue_id=issue_101.id,
            author_user_id=support_user.id,
            author_name="Support User",
            author_role="support_user",
            update_text=(
                "Temporary workaround identified, but customer has not confirmed "
                "whether the workaround satisfies finance reporting requirements."
            ),
            is_customer_visible=True,
            created_at=now - timedelta(days=1),
        )

        add_issue_update_if_missing(
            session,
            issue_id=issue_101.id,
            author_user_id=admin_user.id,
            author_name="Admin User",
            author_role="admin",
            update_text=(
                "Executive update requested because this is a P1 issue on an "
                "at-risk enterprise account."
            ),
            is_customer_visible=False,
            created_at=now - timedelta(hours=12),
        )

        add_issue_update_if_missing(
            session,
            issue_id=issue_102.id,
            author_user_id=support_user.id,
            author_name="Support User",
            author_role="support_user",
            update_text=(
                "Initial investigation points to a SAML certificate mismatch. "
                "Waiting for customer IdP metadata confirmation."
            ),
            is_customer_visible=True,
            created_at=now - timedelta(days=4),
        )

        add_issue_update_if_missing(
            session,
            issue_id=issue_201.id,
            author_user_id=support_user.id,
            author_name="Support User",
            author_role="support_user",
            update_text=(
                "Reproduced dashboard slowdown using a nine-month date range. "
                "Need to inspect query performance logs."
            ),
            is_customer_visible=True,
            created_at=now - timedelta(hours=20),
        )

        add_issue_update_if_missing(
            session,
            issue_id=issue_301.id,
            author_user_id=support_user.id,
            author_name="Support User",
            author_role="support_user",
            update_text=(
                "Issue is blocked pending store connector logs from the customer."
            ),
            is_customer_visible=True,
            created_at=now - timedelta(days=3),
        )

        add_next_action_if_missing(
            session,
            issue_id=issue_201.id,
            action_type=NextActionTypeEnum.TECHNICAL_INVESTIGATION,
            action_text=(
                "Review dashboard query performance logs and confirm whether "
                "caching should be adjusted."
            ),
            owner_user_id=support_user.id,
            due_at=now + timedelta(days=2),
            status=NextActionStatusEnum.OPEN,
            created_by_user_id=support_user.id,
            created_by_role="support_user",
        )

        add_next_action_if_missing(
            session,
            issue_id=issue_101.id,
            action_type=NextActionTypeEnum.CUSTOMER_UPDATE,
            action_text=(
                "Send Globex a concise status update covering impact, workaround "
                "status, and next engineering step."
            ),
            owner_user_id=support_user.id,
            due_at=now + timedelta(hours=8),
            status=NextActionStatusEnum.OPEN,
            created_by_user_id=admin_user.id,
            created_by_role="admin",
        )

        session.commit()

    print("Seeded business data.")


if __name__ == "__main__":
    seed_business_data()