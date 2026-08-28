"""Aegis hook gate: lifecycle."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .contracts import Payload
from .loaders import _load_brief_lib_module, _load_ledger_lib_module
from .decisions import advisory_enabled, advisory_message, append_gate_decision, block, project_root
from .payloads import safe_expanduser
from .runtime_state import clear_client_reload_marker, required_pending_tracking_events
from .evidence import format_pending_tracking
from .tracking import _hook_adapter, _hook_agent_identity, _record_branch


def session_start_hook() -> int:
    """Capsule PR-2b: stamp session_begin with the capsule on/off flag (falsifier
    instrumentation) and, when on, inject the computed capsule via stdout.

    SessionStart is synchronous on purpose — stdout enters model context. The stamp
    and the injection are independent best-effort paths; nothing here may fail the
    hook or block a session start.
    """

    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001
        raw = ""
    root = project_root()
    brief_lib = _load_brief_lib_module()
    try:
        data = json.loads(raw or "{}")
        if not isinstance(data, dict):
            data = {}
    except Exception:  # noqa: BLE001 - a malformed payload must not block a session.
        data = {}
    clear_client_reload_marker(root, agent=_hook_adapter(data))
    if brief_lib is not None and hasattr(brief_lib, "capsule_assignment"):
        assignment = brief_lib.capsule_assignment(root, session_id=data.get("session_id"))
    elif brief_lib is not None:
        assignment = {"injected": brief_lib.injection_enabled(root), "mode": "static-on"}
    else:
        assignment = {"injected": False, "mode": "no-brief-lib"}
    injected = bool(assignment.get("injected"))
    try:
        ledger_lib = _load_ledger_lib_module()
        if ledger_lib is not None:
            agent_id, agent_type, parent_agent_id, attribution_source = _hook_agent_identity(data)
            ledger = ledger_lib.open_ledger(cwd=root)
            try:
                ledger.append(
                    {
                        "session_id": data.get("session_id"),
                        "branch": _record_branch(str(root)),
                        "cwd": data.get("cwd"),
                        "event_type": "session_begin",
                        "handler": f"{_hook_adapter(data)}:sessionstart",
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "parent_agent_id": parent_agent_id,
                        "extra": {
                            "hook_event_name": "SessionStart",
                            "source": data.get("source"),
                            "turn_id": data.get("turn_id"),
                            "model": data.get("model"),
                            "adapter": _hook_adapter(data),
                            "agent_attribution_source": attribution_source,
                            "capsule_injected": injected,
                            "assignment": assignment.get("mode"),
                        },
                    }
                )
            finally:
                ledger.close()
    except Exception:  # noqa: BLE001 - the falsifier stamp is best-effort.
        pass
    if not injected or brief_lib is None:
        return 0
    try:
        source = str(data.get("source") or "")
        reason = "session-start" if source == "startup" else "session-resume"
        capsule = brief_lib.compile_capsule(root, reason=reason)
        text, _dropped = brief_lib.render_injection(capsule)
        brief_lib.write_capsule(root, capsule, brief_lib.render_markdown(capsule))
        print(text)
    except Exception:  # noqa: BLE001 - injection must never block a session start.
        return 0
    return 0


def stop_gate() -> int:
    root = project_root()
    pending_events = required_pending_tracking_events(root)
    if not pending_events:
        if advisory_enabled(root):
            append_gate_decision(
                root,
                hook="stop",
                payload=Payload("Stop", {}),
                verdict="allow",
                reason="no_pending_tracking",
            )
        return 0
    message = (
        "BLOCKED by .claude/scripts/tracking-stop-gate.sh\n\n"
        "Reason: pending S:W:H:E tracking remains before session stop.\n\n"
        f"Pending tracking:\n{format_pending_tracking(pending_events)}\n\n"
        "Run the pending-id repair command above, or use the explicit fallback "
        '`aegis log --handler <handler> --evidence <path-or-command> --note "<past-tense note>"`, '
        "before ending the session."
    )
    if advisory_enabled(root):
        append_gate_decision(
            root,
            hook="stop",
            payload=Payload("Stop", {}),
            verdict="would_block",
            reason="pending_tracking",
        )
        advisory_message("stop", "pending_tracking")
        return 0
    return block(message)


def settings_has_required_hooks(settings_path: Path) -> tuple[bool, list[str]]:
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced in hook feedback.
        return False, [f"could not parse {settings_path}: {exc}"]
    if not isinstance(data, dict):
        return False, [f"{settings_path} is not a JSON object"]

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False, ["settings missing hooks object"]

    issues: list[str] = []
    pretool = hooks.get("PreToolUse")
    if not isinstance(pretool, list) or not any(
        isinstance(group, dict)
        and str(group.get("matcher") or "") == "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$"
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command") == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/pretooluse-gate.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in pretool
    ):
        issues.append("required PreToolUse dispatcher hook missing or changed")

    posttool = hooks.get("PostToolUse")
    if not isinstance(posttool, list) or not any(
        isinstance(group, dict)
        and str(group.get("matcher") or "") == "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$"
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command")
            == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/posttooluse-tracking.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in posttool
    ):
        issues.append("required PostToolUse S:W:H:E tracking hook missing or changed")

    stop = hooks.get("Stop")
    if not isinstance(stop, list) or not any(
        isinstance(group, dict)
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command") == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/handoff-nudge.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in stop
    ):
        issues.append("required Stop handoff hook missing or changed")

    if not isinstance(stop, list) or not any(
        isinstance(group, dict)
        and any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and hook.get("command")
            == "bash $CLAUDE_PROJECT_DIR/.claude/scripts/tracking-stop-gate.sh"
            for hook in group.get("hooks", [])
            if isinstance(group.get("hooks"), list)
        )
        for group in stop
    ):
        issues.append("required Stop S:W:H:E tracking gate missing or changed")

    return not issues, issues


def config_change_guard() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return 0
    if not isinstance(data, dict):
        return 0

    source = str(data.get("source") or "")
    if source == "policy_settings":
        return 0

    file_path = data.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0

    root = project_root()
    path = safe_expanduser(file_path)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    project_settings = (root / ".claude" / "settings.json").resolve()
    if path != project_settings:
        return 0

    ok, issues = settings_has_required_hooks(path)
    if ok:
        return 0
    details = "\n".join(f"  - {issue}" for issue in issues)
    return block(
        "BLOCKED by .claude/scripts/config-change-guard.sh\n\n"
        f"Settings file: {path}\n"
        f"Violation(s):\n{details}\n\n"
        "Project settings must keep the Claude runtime gate registered. Restore the PreToolUse dispatcher and Stop handoff hook before continuing."
    )
