# Acme-Operations-Agent-Application

Acme Operations Agent Application is an enterprise AI assistant for sales, support and operations teams. It helps internal users quickly understand customer health, active support risks, issue history and required follow-up actions in a secured, regulated and policy-governed manner.


## Quick start

- Clone the repository

- Update the `.env variables` by replace the .env.example (see attached notion pdf).

- Run the Docker Compose Stack

    ```bash
    docker compose up -d
    ```
    On first startup, Docker Compose will:

    1. Start PostgreSQL
    2. Start Keycloak and import the Acme realm
    3. Run Alembic migrations
    4. Seed app users, roles, customers, issues, updates, and next actions
    5. Start the MCP server
    6. Start the FastAPI backend
    7. Start the Streamlit frontend


---
### Login the Acme Operations Agent Application

Test users are pre-configured in Keycloak realm: 

| User | Password | Role | Permissions |
|------|----------|------|-------------|
| admin1 | AdminPass123 | admin | Full read/write/action management |
| support1 | SupportPass123 | support_user | Read + update issues |
| sales1 | SalesPass123 | sales_user | Read-only |




### Try Example Prompts: 

Use the following prompts to validate role-based behavior across read-only access, issue updates, next-action management and special escalation summary workflows (make sure to use respective credentials).


#### Sales User Examples

The `sales_user` has read-only access. This user can view customers, issues, issue updates, and next actions, but cannot modify operational records.

```bash
list all customers
```

```bash
Show me the open issues for Stark Industries.
```

```bash
Prepare an executive escalation summary for Globex Corporation.
```

```bash
Add an internal update to ISSUE-101 saying the customer requested a status update.
```

**Expected behavior:** The first three prompts should work because sales_user has read-only access. The last prompt should be denied because sales_user cannot update issue status.



#### Support User Example

The `support_user` can read customer and issue data, update issue status, and add issue updates. This user cannot create, update, or complete next actions.

```bash
list all customers
```

```bash
Add a customer-visible update to ISSUE-601 saying the email queue delay is under investigation and support is reviewing queue metrics.
```

```bash
Update ISSUE-102 to in_progress.
```

```bash
Create a next action for ISSUE-101 to schedule an executive follow-up meeting tomorrow.
```

**Expected behavior:** The first three prompts should work because support_user can read data and update issue status and add issue updates. The last prompt should be denied because support_user cannot manage next actions.



#### Admin User Example

The `admin_user` has full operational access. This user can read data, update issues, add issue updates, and manage next actions.

```bash copy
Show me the open issues for Stark Industries.
```

```bash
Prepare an executive escalation summary for Cyberdyne Systems.
```

```bash
List the latest updates and next actions for ISSUE-701.
```

```bash
Add an internal update to ISSUE-401 saying engineering escalation has been opened and mitigation is expected within four hours.
```

**Expected behavior:** All prompts should work because admin has full operational access, including reads, issue updates, and next-action management.


---

## Delivery Approach (Kanban Workflow)

The first step was to review the brief, understand the requirements and identify the mandatory capabilities. After identifying the required capabilities, the work was broken down into smaller tasks and sequenced based on dependency order. 

A Kanban board was used to track progress across the project to track what had been implemented, what was blocked, and what still needed to be completed. 

Project board: https://github.com/users/CodeByKarthik/projects/1/views/3



## Additional Resources

For more detailed information about the Acme Operations Agent Application, please refer to the project README files and the Nextra documentation. These resources cover the following topics:

- System Architecture Overview : https://github.com/CodeByKarthik/Acme-Operations-Agent-Application/blob/main/docs/system-architecture.md
- Request Lifecycle (Userflow) : https://github.com/CodeByKarthik/Acme-Operations-Agent-Application/blob/main/docs/request-lifecycle.md
- AI Agent Architecture Overview : https://github.com/CodeByKarthik/Acme-Operations-Agent-Application/blob/main/docs/agent-architecture.md
- Evaluation Summary : https://github.com/CodeByKarthik/Acme-Operations-Agent-Application/blob/main/docs/evaluation_report.md
- Trade-offs and Future Improvements : https://github.com/CodeByKarthik/Acme-Operations-Agent-Application/blob/main/docs/trade-off-statement.md
- AI Usage During Development : https://github.com/CodeByKarthik/Acme-Operations-Agent-Application/blob/main/docs/ai-usage.md
