# Trade-offs and Design Decisions

## Overview

This document explains the main engineering trade-offs made while designing and building the **Acme Operations Agent Application**.

The objective of this project was to build a functional, end-to-end enterprise AI assistant prototype within a limited assessment window. When implementing the solution, I proiritised the following: 

- Secure end-to-end demonstration
- Clear separation of responsibilities
- Agentic AI implementation with zero compromise 
- Scalable Architecture and Codebase
- Following Governance and Guardrails
- Reproducibility through Docker Compose
- End-to-End observability and evaluation

This prototype application is designed to demonstrate the architectural patterns, security controls, Agentic AI Implementation
in regulated and Secured Data Environments that would be expanded in a production implementation. 

Even though all the criteria were fulfilled by the implementation, there were areas where, from my perspective, I could have improved further and made the implementation more production-ready. Addressing these areas would reduce technical debt and these learnings provide a clear path for future iterations and enterprise hardening.

## Decision & Tradeoff

### 1. Streamlit Frontend vs Production Web Frontend

The application uses **Streamlit** as the frontend for login, session handling, and chat interaction. 

Streamlit is suitable for a time-boxed prototype because it allows the user experience to be built quickly while still demonstrating end to end application flow. 

This allowed more engineering effort to be focused on the scalable architecture, backend, agent workflow, MCP tools, RBAC, database integration, observability and evaluation. 

Streamlit is not the ideal choice for a large-scale enterprise frontend. A production application would likely use a dedicated frontend framework such as React or Next.js to provide stronger control over routing, state management, accessibility, testing and UI composition.



### 2. Latency vs Security

During early testing, the predefined ReAct agent produced responses in approximately three to four seconds. This was faster and simpler, but it provided less explicit control over input validation, routing and safety checks before tool execution. The implementation was therefore moved to a custom graph-based workflow with guardrails, even though this introduced additional latency.

This trade-off was intentional because the application operates in an enterprise context where users interact with customer, issue, and operational data. In this type of system, predictable and controlled execution is more important than achieving the lowest possible response time. The additional latency is the cost of applying input guardrails, clearer execution routing, and safer separation between reasoning and business operations.

In a production implementation, latency would be optimised without removing the security controls. Possible improvements include streaming responses, caching safe intermediate results, using faster models for guardrail, parallelising independent operations and measuring each graph node separately to identify bottlenecks.



### 3. Multi-Stage Docker Builds vs Delivery Time

The MCP server container uses a multi-stage Docker build because this is a standard containerisation practice for reducing unnecessary runtime dependencies. It helps produce a cleaner image by keeping build-time dependencies out of the final runtime container. This proven technique improves maintainability, reduces deployment cost and reduces build times.

However, the same optimisation was not applied to every service, including the backend and frontend containers. The available time was prioritised toward the parts of the system that proved the enterprise AI capability end to end such as Keycloak authentication, RBAC, PostgreSQL integration, Redis state, MCP tool execution, observability, and evaluation. Fully optimising every Docker image would have improved container quality, but it would not have added as much value as it adds in the
production systems.

In a production implementation, all containers would be converted to multi-stage builds and hardened consistently which ultimately leads to reduce cost in the deployed application. 



### 4. Small Dataset vs Large Dataset Testing

The application uses a small representative dataset instead of a large production-sized dataset. This was done to prioritise proving the agent’s core capabilities of reliable secured infrastructure, guardrails and observability. A larger dataset would have required more time for data modelling, seeding, validation, and evaluation.

The trade-off is that the current dataset demonstrates functional correctness but does not fully test large-scale retrieval, edge cases, performance under higher data volume, or complex customer histories. However, the implementation still follows an important production practice by limiting how much data is passed into the agent. This prevents the model context window from being flooded with records and keeps the agent focused on relevant information.

In a production system, the dataset would be expanded and tested against more realistic customer scenarios. The application would also need stronger filtering, pagination, ranking and retrieval evaluation to ensure the agent receives the right amount of context without sacrificing quality or performance.


### 5. Automated Tests vs Functional Proof of Concept

In a normal production project, automated tests would be written and included in the CI/CD pipeline. These would cover unit tests, integration tests, API tests and regression evaluation. Due to the assessment timeframe and managing my current workloads, a complete automated test suite was not implemented.

The trade-off was made to prioritise a fully functional end-to-end proof of concept and prioritised in testing the agentic ai capability. This resulted in regorously testing and logging the ai agent by asking multiple question to create hypothetical 
situations. As a result, the time was well spent on agentic ai handling the uncertanity really well. These areas were considered more critical to the success of the prototype than broad automated test coverage.

However, the implementation was still validated incrementally during development by breaking work into smaller parts and testing each part before moving to the next. In production, this would not be sufficient as automated test coverage would be required before deployment.



## Future Implementations for Production Ready Solution


- Replace the Streamlit prototype frontend with a production web application using React or Next.js.

- Add a complete automated test suite covering unit, integration, API, RBAC, MCP tool, and agent regression tests.

- Integrate all tests into a CI/CD pipeline with linting, type checks, security scans, and deployment gates.

- Add streaming responses to improve perceived latency during longer agent executions.

- Expand the router to support more intent categories and route users to smaller, more relevant tool groups.

- Convert all application Docker images to multi-stage builds with minimal runtime dependencies.

- Replace local Docker Compose deployment with Kubernetes manifests.

- Move secrets and environment variables into a managed secrets service.

- Integrate Keycloak with an enterprise identity provider such as Azure AD. 

- Build a larger evaluation benchmark with normal, edge-case, adversarial, and role-specific test scenarios.

- Run continuous agent evaluation as part of CI/CD to detect regressions in tool selection and response quality.

- Add output validation to ensure responses are grounded, policy-compliant, and safe to show users.

- Define Redis cache invalidation rules, TTL policies, and monitoring for memory usage and cache hit rates.

- Add human approval workflows for sensitive actions such as executive escalations or high-impact data updates.

- Improve domain error handling with clearer user-facing messages and structured backend error responses.

- Add environment-specific configuration for local, staging, and production deployments.

- Introduce blue-green or canary deployment strategies for safer production releases.