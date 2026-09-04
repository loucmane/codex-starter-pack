"""Non-overridable client-mode boundaries, independent of workflow readiness."""

from __future__ import annotations

from pathlib import Path

from .contracts import Payload
from .decisions import gate_hard_block
from .delegation import is_provider_native_delegation_tool
from .evidence import payload_is_read_only
from .payloads import is_hookable_tool, payload_required_field_issue


def deny_plan_mode_mutation(root: Path, payload: Payload) -> int | None:
    """Return an explicit refusal, or None to continue the ordinary gate.

    Withholding a native permission approval is not a denial: the client may
    still execute Bash. Apply this boundary before bootstrap/delegation/readiness
    exemptions and again before any degraded advisory allowance. Missing or
    unknown modes retain their existing behavior (including no native bootstrap
    approval); this rule adds no grant to any client or mode.
    """
    if payload.permission_mode != "plan":
        return None
    delegation = is_provider_native_delegation_tool(payload.tool_name)
    if not delegation and not is_hookable_tool(payload.tool_name):
        return None
    try:
        denied = (
            delegation
            or bool(payload_required_field_issue(payload))
            or not payload_is_read_only(payload)
        )
    except Exception:  # noqa: BLE001 - classifier uncertainty cannot authorize plan-mode work.
        denied = True
    if not denied:
        return None
    return gate_hard_block(
        root,
        payload,
        "BLOCKED by .claude/scripts/pretooluse-gate.sh\n\n"
        f"Tool: {payload.tool_name}\n"
        "Reason: plan mode permits inspection, not persistent mutations or delegation.\n\n"
        "Kickoff, plan-file writes, tracking updates, and workflow repair are mutations; "
        "bootstrap or advisory mode cannot exempt them. Continue read-only inspection, "
        "or run already-authorized work from a non-plan session without widening its scope.",
        reason="plan_mode_mutation",
    )
