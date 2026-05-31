"""
Route definitions for the agent graph.

All valid routes and their mappings are defined here.
To add a new skill route, add it to SKILL_ROUTES and
update the ROUTER_PROMPT with examples.
"""

SKILL_ROUTES: dict[str, str] = {
    "escalation_summary": "escalation_summary",
    # "next_skill": "next_skill_node_name",   ← add new skills here
}

DEFAULT_ROUTE = "general"

VALID_ROUTES = set(SKILL_ROUTES.keys()) | {DEFAULT_ROUTE}
