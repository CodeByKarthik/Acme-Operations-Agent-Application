# src/acme_ops_agent/observability.py

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from langsmith import traceable


_RBAC_ERROR_MARKERS = [
    "does not have the required role",
    "permission denied",
    "not permitted",
    "forbidden",
    "unauthorized",
    "rbac",
]


def classify_error_text(text: str) -> str:
    lowered = text.lower()

    if any(marker in lowered for marker in _RBAC_ERROR_MARKERS):
        return "rbac_denial"

    if "schema" in lowered or "validation" in lowered:
        return "tool_schema_failure"

    if "connection" in lowered or "connect" in lowered or "refused" in lowered:
        return "mcp_connection_failure"

    if "openai" in lowered or "llm" in lowered or "model" in lowered:
        return "llm_failure"

    return "tool_runtime_failure"


def is_rbac_denial_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _RBAC_ERROR_MARKERS)


@traceable(name="mcp_tool_call", run_type="tool")
async def trace_mcp_tool_call(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    call_fn: Callable[[], Awaitable[str]],
) -> dict[str, Any]:
    """
    Creates a LangSmith child run for each MCP tool invocation.

    This gives you:
    - tool name
    - success/error
    - latency
    - empty result
    - RBAC denial detection
    """
    started = time.perf_counter()

    try:
        result = await call_fn()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)

        empty_result = result.strip() == "" or result == "No output returned"
        rbac_denied = is_rbac_denial_text(result)
        success = not result.startswith("Error:") and not rbac_denied

        return {
            "success": success,
            "tool_name": tool_name,
            "latency_ms": latency_ms,
            "empty_result": empty_result,
            "rbac_denied": rbac_denied,
            "error_type": classify_error_text(result) if not success else None,
            "result": result,
        }

    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)

        return {
            "success": False,
            "tool_name": tool_name,
            "latency_ms": latency_ms,
            "empty_result": False,
            "rbac_denied": is_rbac_denial_text(str(exc)),
            "error_type": classify_error_text(str(exc)),
            "error": str(exc),
        }


@traceable(name="agent_final_response_check", run_type="chain")
def trace_final_response_check(
    *,
    has_final_response: bool,
    tools_called: list[str],
    rbac_denied: bool,
) -> dict[str, Any]:
    """
    Creates a post-agent child run summarizing agent outcome.
    """
    return {
        "has_final_response": has_final_response,
        "tools_called": tools_called,
        "tools_called_count": len(tools_called),
        "rbac_denied": rbac_denied,
    }