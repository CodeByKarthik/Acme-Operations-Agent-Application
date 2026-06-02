# System Architecture

The Acme Operations Agent is an enterprise AI assistant that enables internal staff to query customer accounts, manage support issues and generate executive escalation summaries using natural language. 

The system is designed as a multi-layered architecture where every layer enforces its own authentication and authorisation boundary, ensuring the agent operates in a secured, regulated, and policy-governed manner.


 
## Five Layer Architecture

The application follows a five-layer architecture:

1. Presentation Layer
2. Backend/API Layer
3. Intelligence Layer
4. Tool Layer
5. Data Layer

This extends a traditional web application architecture by adding an intelligence layer for agent reasoning and a tool layer for controlled business operation execution and separation of concern.


![Five Layer Architecture Diagram](./docs/diagrams/five-layer-architecture.png)


### 1. Presentation Layer

The **Streamlit frontend** provides the conversational user interface for internal users.

Users authenticate through **Keycloak** using the OAuth 2.0 authorization code flow. After successful login, the frontend receives an access token and forwards it with API requests to the backend.

The frontend is responsible for:

- Login flow
- User session handling
- Chat interface
- Calling backend APIs

The frontend does not access the database or MCP tools directly.


### 2. Backend/API Layer

The **FastAPI backend** is the main entry point for authenticated application requests.

For each request, the backend validates the user token, resolves the authenticated application user, and determines the user’s role, such as `sales_user`, `support_user`, or `admin`.

The backend is responsible for:

- Chat API requests
- Health and user information endpoints
- Authentication validation
- Request middleware
- Observability and structured logging
- Passing authenticated user context into the agent workflow

This ensures the agent receives both the user message and the user’s authorization context before any tool or business operation is attempted.


### 3. Intelligence Layer

The LangGraph agent is the reasoning engine of the application. It is built as a custom StateGraph to provide explicit control over the execution flow. 

The agent workflow includes:

- Input guardrails
- Router node
- ReAct agent node
- Skill node
- Tool node
- Escalation summary skill
- MCP client

Every user message passes through a two-layer input guardrail (pattern-based detection followed by an LLM classifier) before reaching the intent router. The router decides whether the request should be handled by a general reasoning path, a specialized skill such as escalation summary generation, or a tool-backed operation.

The agent can then reason over the user request and compose responses, but it does not directly access the database. Any operational data access must go through the MCP tool layer.


### 4. Tool Layer

The **MCP server** exposes controlled business tools used by the backend agent.

The MCP layer is responsible for:

- Registering available tools
- Executing business tool calls
- Passing requests into shared business services
- Enforcing tool-level access rules before sensitive operations are performed

Tool calls are executed with the authenticated user context. This ensures that read and write operations follow the permissions associated with the user’s role. 

For example:

- `sales_user` can perform read-only operations
- `support_user` can read data and update support issues
- `admin` can perform full operational actions, including next-action management

This prevents the agent from bypassing application permissions, even if the agent's reasoning is manipulated through prompt injection, it is not permitted by the tool-layer authorization checks.


### 5. Data Layer

The **PostgreSQL database** stores durable application data such as:

- Application users
- Roles
- Customers
- Issues
- Issue updates
- Next actions

Redis provides an ephemeral caching layer for conversation memory (thirty-minute TTL) and read-only tool result caching (five-minute TTL), reducing redundant database queries during multi-turn conversations. Write operations are never cached and error responses are never persisted, ensuring data consistency.



## Security model

The Acme Operations Agent Application enforces series of independent enforcement points across the architecture. 

The frontend authenticates users through Keycloak OAuth 2.0 and never exposes raw credentials. The API layer validates every JWT independently and resolves the user's application role. The intelligence layer applies input guardrails that block prompt injection, jailbreak attempts, and social engineering before the agent begins reasoning. The tool layer re-validates the JWT and enforces role-based access control on every individual tool call. The data layer is only accessible through the repository and service layers, never directly from the agent.

This defence-in-depth approach means that compromising any single layer does not grant access to the layers below it. The bearer token flows through every layer, and permissions are enforced at the point of execution.


## Governance and Policies

The application is designed with enterprise AI governance at its core, ensuring that every interaction with the LLM is controlled, auditable and compliant with organisational policies.

The agent is not treated as a trusted actor. Instead, it operates within the permissions of the authenticated user and must use approved tools to access or modify business data.

- The application  serves OpenAI as the primary provider for development and demonstration, with Azure OpenAI configured as an automatic fallback.

- In a production enterprise deployment, this ordering would be reversed as Azure OpenAI would serve as the primary provider to leverage data residency controls, enterprise SLAs, private endpoint support and extended to manage key rotation through Azure Active Directory and compliance certifications. 


## Observability & Evaluation

Every agent interaction is traced end-to-end through LangSmith, capturing each LLM call, tool invocation and routing decision with full metadata including the authenticated user, their role, the conversation identifier, and the graph route taken. 

After every response is delivered to the user, a background evaluation task scores the response across five dimensions: 
- groundedness
- relevance
- hallucination (assessed by an LLM-as-judge)
- tool selection correctness
- RBAC compliance (assessed deterministically).

These scores are logged as feedback on each trace, enabling quality monitoring, debugging and rapid identification of responses that may contain hallucinated information. The evaluation runs asynchronously with zero latency impact on the end user. 


Examples of LangSmith logs are shown below:

- https://eu.smith.langchain.com/public/e4af02ca-2972-4fe7-ada0-b1cfc73c0c3b/r

- https://eu.smith.langchain.com/public/a53b41a3-ab06-456f-8d7c-9c01df7d7ce2/r



## Deployment

The system is containerized and orchestrated using **Docker Compose**. The Docker Compose stack starts the main application services, including:

- PostgreSQL
- Keycloak
- Alembic migration and seed process
- MCP server
- FastAPI backend
- Streamlit frontend

The application can be started with `docker compose up`.

The architecture is stateless at the application layer so that all session state resides in Redis and all operational data in PostgreSQL so that the backend can be horizontally scaled behind a load balancer without architectural changes.