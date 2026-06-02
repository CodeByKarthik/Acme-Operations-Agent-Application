## Overview

AI tools were used during development to accelerate implementation and support debugging. They were treated as engineering assistants and never acted as autonomous decision-makers. 

All architectural decisions, security choices, role-based access rules, and final implementation reviews were performed manually to ensure the solution remained aligned with best practices and enterprise security expectations.


#### How AI Tools Were Used

AI tools were primarily delegated repetitive, time-consuming, or iteration-friendly tasks. These included code generation, code reviews, type safety fixes, and debugging assistance. They were especially helpful for quickly producing boilerplate code, reviewing ideas, and expanding on implementation thoughts.

- AI was also valuable for seeding data and writing seeding scripts when the database schema was provided.

- In the context of Agentic AI implementation, AI proved particularly useful when developing iterative prompts. Starting with a base version, coding assistance helped enhance prompt quality and tool definitions in a very short time.

- AI was used to interpret error logs and stack traces, quickly suggesting possible root causes and relevant fixes. This reduced the time spent tracing issues through unfamiliar parts of the codebase. During debugging sessions, AI helped generate targeted test cases and edge condition inputs, making it easier to reproduce intermittent issues and validate fixes before committing changes.

For higher-risk areas such as authentication, RBAC, MCP tool execution, database writes, and guardrail behavior, AI-generated suggestions were never accepted directly. These areas were manually reviewed and tested because errors could affect application security and correctness.

When using AI for code generation, requirements were broken into small pieces and solved sequentially. This approach provided enough time to spot errors, adjust formatting, restructure, suggest different methods, and critique my own code snippets.


#### How AI Output Was Reviewed

AI-generated code and documentation were reviewed before being added to the project. Each piece was checked for correctness, consistency with the existing architecture, type safety, validation behavior, security implications, and alignment with actual project requirements. Where AI-generated code was incomplete, too generic, or misaligned with the project structure, it was rewritten with specific instructions or sometimes adapted manually.

Some AI-generated suggestions were too broad, assumed unsupported components, or introduced patterns that did not match the project scope. These were corrected by comparing the suggestions against the actual repository and implementation constraints.

The implementation was validated incrementally during development. Each component was tested after implementation, including authentication, backend API flow, MCP tool execution, PostgreSQL access, Redis-backed conversation state, role-based permissions, and agent behavior. Prioritizing infrastructure implementation made comfortable to run end-to-end tests—any problems in generated code would cause the full implementation to fail.



