from __future__ import annotations

from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from acme_ops_agent.agent.mcp_client import MCPConnection, safe_json_parse
from acme_ops_agent.agent.prompts.skills import (
    CUSTOMER_NAME_EXTRACTION_PROMPT,
    ESCALATION_SUMMARY_PROMPT,
)
from acme_ops_agent.utils.logger import get_logger

logger = get_logger(__name__)

MessageContent = str | list[str | dict[str, object]]
IssueRecord = dict[str, object]


def _content_to_text(content: MessageContent) -> str:
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        else:
            text_value = item.get("text")
            if isinstance(text_value, str):
                parts.append(text_value)
            else:
                parts.append(repr(item))
    return " ".join(parts)


def _parse_issue_list(raw: object) -> list[IssueRecord]:
    if not isinstance(raw, list):
        return []

    raw_items = cast(list[object], raw)
    issues: list[IssueRecord] = []
    for item in raw_items:
        if isinstance(item, dict):
            issues.append(cast(IssueRecord, item))
    return issues


class EscalationSummarySkill:
    """
    Orchestrates a full customer escalation summary.

    Input:  User message containing a customer name.
    Output: Structured executive summary with risk level,
            recommendations, and identified gaps.
    """

    def __init__(
        self,
        connection: MCPConnection,
        llm: ChatOpenAI,
    ) -> None:
        self._connection = connection
        self._llm = llm

    async def execute(self, user_message: str) -> str:
        """
        Run the full escalation summary workflow.

        Steps:
        1. Extract customer name from the user message (LLM)
        2. Fetch customer profile (MCP)
        3. Fetch open issues (MCP)
        4. For each issue, fetch updates and next actions (MCP)
        5. Synthesise executive summary (LLM)
        """
        logger.info("Escalation Summary Skill started")

        # --- Step 1: Extract customer name ---
        customer_name = await self._extract_customer_name(user_message)
        if customer_name == "UNKNOWN":
            return (
                "I could not identify a customer name in your request. "
                "Please specify which customer you need an escalation summary for."
            )
        logger.info("Extracted customer name: %s", customer_name)

        # --- Step 2: Fetch customer profile ---
        customer_raw = await self._connection.call_tool(
            "get_customer_by_name", {"name": customer_name}
        )

        if customer_raw.startswith("Error:") or customer_raw in ("null", "None", ""):
            return f"Customer '{customer_name}' was not found in the system."

        customer = safe_json_parse(customer_raw)
        if customer is None:
            return f"Customer '{customer_name}' returned unreadable data."

        customer_id = customer.get("id")
        if not customer_id:
            return f"Customer '{customer_name}' is missing an ID in the database."

        logger.info("Fetched customer profile: %s (id=%s)", customer_name, customer_id)

        # --- Step 3: Fetch open issues ---
        issues_raw = await self._connection.call_tool(
            "list_open_issues", {"customer_id": customer_id}
        )
        issues = _parse_issue_list(safe_json_parse(issues_raw))
        logger.info("Fetched %d open issues", len(issues))

        # --- Step 4: Fetch updates and actions per issue ---
        updates_sections: list[str] = []
        actions_sections: list[str] = []

        for issue in issues:
            issue_id = issue.get("id")
            ref = issue.get("external_ref", "???")

            if not issue_id:
                continue

            updates_raw = await self._connection.call_tool(
                "list_issue_updates", {"issue_id": issue_id}
            )
            actions_raw = await self._connection.call_tool(
                "list_next_actions", {"issue_id": issue_id}
            )

            updates_sections.append(f"### {ref}\n{updates_raw}")
            actions_sections.append(f"### {ref}\n{actions_raw}")

        logger.info(
            "Fetched updates for %d issues, actions for %d issues",
            len(updates_sections),
            len(actions_sections),
        )

        # --- Step 5: Synthesise executive summary ---
        summary = await self._synthesise(
            customer_data=customer_raw,
            issues_data=issues_raw,
            issue_count=len(issues),
            updates_data="\n\n".join(updates_sections) or "No updates found.",
            actions_data="\n\n".join(actions_sections) or "No pending actions.",
        )

        logger.info("Escalation Summary Skill completed")
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _extract_customer_name(self, message: str) -> str:
        """Use the LLM to pull the customer name from free text."""
        prompt = CUSTOMER_NAME_EXTRACTION_PROMPT.format(message=message)
        response = await self._llm.ainvoke([HumanMessage(content=prompt)])
        return _content_to_text(cast(MessageContent, getattr(response, "content"))).strip()

    async def _synthesise(
        self,
        customer_data: str,
        issues_data: str,
        issue_count: int,
        updates_data: str,
        actions_data: str,
    ) -> str:
        """Feed all gathered data into the synthesis prompt."""
        prompt = ESCALATION_SUMMARY_PROMPT.format(
            customer_data=customer_data,
            issues_data=issues_data,
            issue_count=issue_count,
            updates_data=updates_data,
            actions_data=actions_data,
        )
        response = await self._llm.ainvoke([SystemMessage(content=prompt)])
        return _content_to_text(cast(MessageContent, getattr(response, "content")))
