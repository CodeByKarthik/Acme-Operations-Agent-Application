# Request Lifecycle & Component Relationship

## Overview

This document explains the system-level component relationships and runtime data flow of the **Acme Operations Agent Application**.

The diagram focuses on how a user request moves through the application from authentication to final response generation. It also shows how supporting services such as Keycloak, Redis, PostgreSQL, the MCP server, and LangSmith participate in the request lifecycle.

The purpose of this view is to show:

- How users authenticate before accessing the application
- How chat requests are sent from the frontend to the backend
- How the backend validates identity and loads conversation context
- How the agent routes and processes user requests
- How tool calls are executed through the MCP server
- How operational data is read from PostgreSQL
- How responses are returned to the user
- How traces and evaluation scores are logged asynchronously


## Request Lifecycle Diagram

<img width="868" height="770" alt="request-lifecycle" src="https://github.com/user-attachments/assets/88738e85-9888-473b-b504-3810a1105d3b" />



The request lifecycle diagram shows the runtime interaction between the following components:

| Component | Responsibility |
|---|---|
| User | Internal application user interacting through a browser |
| Streamlit | Frontend application that provides login and chat UI |
| Keycloak | Identity provider responsible for authentication and token issuance |
| Backend | FastAPI backend that validates requests, manages agent execution, and returns responses |
| Redis | Stores short-lived conversation history and runtime cache data |
| MCP Server | Executes controlled business tools on behalf of the backend agent |
| PostgreSQL | Stores durable application and business data |
| LangSmith | Receives asynchronous traces, evaluation results, and scoring logs |



## Request Flow 


### 1. Authentication Flow

When a user opens the application for the first time, the frontend starts the authentication flow.

```text
User → Streamlit → Keycloak → Streamlit
```

The authentication sequence is:

1. The user opens the Streamlit application.
2. Streamlit redirects the user to Keycloak using OAuth 2.0.
3. The user enters their username and password in Keycloak.
4. Keycloak redirects back to Streamlit with an authorization code.
5. Streamlit exchanges the authorization code for access and refresh tokens.
6. Streamlit stores the JWT in the user session.
7. Future backend requests include the JWT as a bearer token.

This ensures that every authenticated request sent to the backend carries the user identity and role information required for authorization.

---

### 2. Chat Request Flow

After authentication, the user can submit a natural-language message through the chat interface.

```text
User → Streamlit → Backend
```

The chat request sequence is:

1. The user sends a message from the Streamlit chat UI.
2. Streamlit sends a `POST /api/chat` request to the backend.
3. The request includes the bearer JWT.
4. The backend validates the JWT using Keycloak JWKS.
5. After validation, the backend resolves the application user and role.
6. The backend loads the existing conversation history from Redis.
7. The request is passed into the backend agent workflow.

At this point, the backend has:

- The user message
- The authenticated user identity
- The user role
- The current conversation context

---

### 3. Agent Processing Flow

The backend processes the request through the agent workflow.

```text
Backend → Input Guardrail → Router → Agent / Skill / Tool Path
```

The agent processing sequence is:

1. The input guardrail checks the message before reasoning begins.
2. The router classifies the user intent.
3. Based on the intent, the request is routed to the appropriate execution path.
4. The agent decides whether it can answer directly or needs to call a business tool.
5. If a tool is required, the backend sends a tool request to the MCP server.

The agent is responsible for reasoning and response composition, but it does not directly access PostgreSQL.

---

### 4. Tool Execution Flow

When the agent requires business data or an operational action, it calls the MCP server.

```text
Backend → MCP Server → PostgreSQL → MCP Server → Backend
```

The tool execution sequence is:

1. The backend sends a `call_tool` request to the MCP server.
2. The tool request includes the bearer token.
3. The MCP server validates the JWT.
4. The MCP server resolves the user and applies role-based access control.
5. If the user is authorized, the MCP server executes the requested business tool.
6. The MCP server queries PostgreSQL when business data is required.
7. PostgreSQL returns the query results.
8. The MCP server returns the structured tool result to the backend.
9. The backend agent uses the tool result for further reasoning and response generation.

This flow ensures that tool execution remains controlled by server-side authentication and authorization checks.

---

### 5. Conversation Persistence and Response Flow

After the agent completes its reasoning, the backend persists the updated conversation state and returns the response.

```text
Backend → Redis
Backend → Streamlit → User
```

The response sequence is:

1. The backend saves the updated conversation state in Redis.
2. The backend returns a JSON response to Streamlit.
3. Streamlit displays the final answer to the user.

Redis is used for runtime conversation state so that the backend can retrieve relevant chat history during future turns.

---

### 6. Observability and Evaluation Flow

The application logs trace and evaluation data asynchronously.

```text
Backend → LangSmith
```

After the response is returned to the user, the backend sends evaluation and logging data to LangSmith.

This asynchronous flow is intentionally outside the main response path, so it does not add latency to the user-facing chat experience.

LangSmith is used for:

- Agent trace visibility
- Tool call inspection
- Routing decision review
- Evaluation score logging
- Debugging and quality monitoring
