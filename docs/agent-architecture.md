# Agent architecture

The agent is built as a custom LangGraph `StateGraph` rather than using the prebuilt `create_react_agent`.

## Why custom StateGraph

The prebuilt `create_react_agent` handles the basic ReAct loop but doesn't support:
- Routing to skill nodes based on intent classification
- Input guardrails as graph nodes
- Per-request evaluation hooks
- Configurable safety limits

A custom StateGraph gives explicit control over every edge and condition.


## Agent workflow diagram

<img width="657" height="512" alt="agent-workflow" src="https://github.com/user-attachments/assets/10026c90-9e25-425a-a0a3-8474e585c753" />


The diagram shows the runtime flow of a user request through the custom LangGraph agent. Every request starts with the input guardrail, where unsafe or policy-violating prompts are blocked before they can reach the reasoning layer.

If the input is safe, the router classifies the request and decides whether it should follow the general ReAct agent path or the specialised escalation summary skill path. General operational questions are handled by the agent node, which can call MCP tools through the tool node in a controlled loop.

The tool loop continues only while tool calls are required and remains bounded by the configured safety limit of 15 tool calls per request. Escalation summary requests bypass the general ReAct loop and follow a dedicated multi-step skill workflow, which gives more predictable output for executive escalation scenarios.

This design separates safety checks, routing, general reasoning, tool execution, and specialised skills into explicit graph nodes, making the agent easier to control, evaluate, and extend.


### Nodes

#### Input guardrail
Two-layer detection:
- **Layer 1**: 20+ regex patterns for prompt injection, persona hijacking, system prompt extraction, delimiter escapes, role elevation, and known jailbreaks
- **Layer 2**: LLM classifier (SAFE / BLOCKED)

If either layer flags the input, the request is blocked before reaching the router.


#### Router
LLM-based intent classifier. Returns a route string:
- `general` → Agent node (ReAct loop)
- `escalation_summary` → Skill node



#### Agent node (ReAct)
Receives the system prompt (templated with username and role), trimmed conversation history (last 10 turns), and 11 MCP tools. The LLM decides which tools to call. The loop continues until:
- The LLM produces a response without tool calls, OR
- The safety limit of 15 tool calls is reached



#### Tool node
Wraps LangGraph's prebuilt `ToolNode` with a call counter. Each tool execution increments the counter.



#### Escalation summary skill
A deterministic multi-step workflow:
1. Extract customer name (LLM)
2. Fetch customer profile (MCP)
3. Fetch open issues (MCP)
4. For each issue: fetch updates + next actions (MCP)
5. Synthesise executive summary (LLM)

Enforces its own limits: max 5 issues, max 5 updates per issue, max 20 MCP calls total.



#### State

The agent state stores the information required to move a request through the graph. It keeps the conversation messages, selected route, tool call count, and any skill-specific context needed during execution. This makes the workflow explicit and allows each node to read or update only the parts of state it needs.

```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    route: str
    tool_call_count: int
    skill_context: str
```



#### Safety limits

Safety limits are used to keep the agent execution bounded and predictable. The tool call limit prevents infinite tool loops, the conversation window limit controls how much history is passed to the model and the skill limits prevent the escalation workflow from processing too much data in a single request. These limits help reduce latency, control cost, and avoid overloading the LLM context window.

| Limit | Value | Enforced by |
|-------|-------|-------------|
| Max tool calls per request | 15 | `conditions.py` → `should_continue()` |
| Conversation window | 10 turns | `memory.py` → `trim_to_turns()` |
| Skill MCP calls | 20 | `EscalationSummarySkill._guarded_mcp_call()` |
| Skill issues processed | 5 | `SkillLimits.max_issues` |
