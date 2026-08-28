"""Aegis hook gate: runtime state."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

from aegis_foundation.gate.readiness import evaluate as evaluate_readiness
from aegis_foundation.gate.render import quick_text

from .contracts import (
    AEGIS_CLIENT_RELOAD_REL,
    AEGIS_CURRENT_WORK_REL,
    AEGIS_DEGRADED_EVENTS_REL,
    AEGIS_PENDING_TRACKING_REL,
    CODEX_APPLY_PATCH_TOOL,
    Payload,
)
from .decisions import _read_json_object
from .payloads import raw_payload_preview


def run_readiness(root: Path) -> subprocess.CompletedProcess[str]:
    task_id, checks, state = evaluate_readiness(root)
    return subprocess.CompletedProcess(
        ["aegis", "gate", "readiness", "--quick", "--target-dir", str(root)],
        2 if state == "BLOCKED" else 0,
        stdout=quick_text(state, task_id, checks) + "\n",
        stderr="",
    )


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def degraded_events_path(root: Path) -> Path:
    return root / AEGIS_DEGRADED_EVENTS_REL


def degraded_events(root: Path) -> list[dict[str, Any]]:
    payload = read_json(degraded_events_path(root))
    if not payload:
        return []
    events = payload.get("events")
    return (
        [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    )


def degraded_event_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def write_degraded_event(
    root: Path,
    payload: Payload,
    reason: str,
    raw_payload: str,
    *,
    mode: str = "degraded_allow",
    action_class: str = "non_destructive",
    trace: str = "",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    existing_events = degraded_events(root)
    previous_hash = str(existing_events[-1].get("event_hash") or "") if existing_events else ""
    event = {
        "id": sha1(
            f"{now}|{payload.tool_name}|{reason}|{raw_payload_preview(raw_payload)}".encode("utf-8")
        ).hexdigest()[:12],
        "created_at": now,
        "gate": "pretooluse",
        "mode": mode,
        "action_class": action_class,
        "tool": payload.tool_name,
        "reason": reason,
        "raw_preview": raw_payload_preview(raw_payload),
        "previous_event_hash": previous_hash,
    }
    if trace:
        event["traceback"] = trace
    event["event_hash"] = degraded_event_hash(event)
    existing_events.append(event)
    write_json(
        degraded_events_path(root),
        {
            "schema_version": "1.0.0",
            "updated_at": now,
            "events": existing_events,
        },
    )
    return event


def current_work(root: Path) -> dict[str, Any] | None:
    return read_json(root / AEGIS_CURRENT_WORK_REL)


def current_work_is_observation(root: Path) -> bool:
    work = current_work(root)
    return (
        isinstance(work, dict)
        and work.get("mode") == "observation"
        and work.get("status") == "in-progress"
    )


def current_work_closeout_completed(root: Path) -> dict[str, Any] | None:
    work = current_work(root)
    if not isinstance(work, dict):
        return None
    if work.get("status") == "completed" and work.get("closeout_passed_at"):
        return work
    return None


def current_git_branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "branch", "--show-current"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def current_work_branch_name(work: dict[str, Any]) -> str:
    branch = work.get("branch")
    if isinstance(branch, dict):
        return str(branch.get("current") or branch.get("name") or "").strip()
    if isinstance(branch, str):
        return branch.strip()
    return ""


def hook_invoking_agent(payload: Payload) -> str | None:
    explicit = str(os.environ.get("AEGIS_INVOKING_AGENT") or "").strip().lower()
    if explicit in {"claude", "codex", "gemini"}:
        return explicit
    if payload.tool_name == CODEX_APPLY_PATCH_TOOL:
        return "codex"
    if os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_CI") == "1":
        return "codex"
    return None


def clear_client_reload_marker(
    root: Path,
    invoking_agent: str | None = None,
    *,
    agent: str | None = None,
) -> None:
    marker = root / AEGIS_CLIENT_RELOAD_REL
    if not marker.exists():
        return
    state = _read_json_object(marker)
    normalized_agent = str(agent or invoking_agent or "").strip().lower()
    raw_agents = state.get("agents")
    pending_agents = (
        [
            str(value).strip().lower()
            for value in raw_agents
            if str(value).strip().lower() in {"claude", "codex", "gemini"}
        ]
        if isinstance(raw_agents, list)
        else []
    )
    legacy_agent = str(state.get("agent") or "").strip().lower()
    if legacy_agent in {"claude", "codex", "gemini"}:
        pending_agents.append(legacy_agent)
    pending_agents = list(dict.fromkeys(pending_agents))
    if not pending_agents:
        # Backward-compatible marker written before per-agent reload tracking.
        marker.unlink()
        return
    if normalized_agent not in pending_agents:
        return
    remaining = [value for value in pending_agents if value != normalized_agent]
    if not remaining:
        marker.unlink()
        return
    state["agents"] = remaining
    state["agent"] = remaining[0] if len(remaining) == 1 else "multi"
    changed_by_agent = state.get("changed_paths_by_agent")
    if isinstance(changed_by_agent, dict):
        changed_by_agent = {
            key: value for key, value in changed_by_agent.items() if key in remaining
        }
        state["changed_paths_by_agent"] = changed_by_agent
        state["changed_paths"] = sorted(
            {
                str(path)
                for paths in changed_by_agent.values()
                if isinstance(paths, list)
                for path in paths
                if isinstance(path, str) and path
            }
        )
    clearance_by_agent = state.get("clearance_by_agent")
    if isinstance(clearance_by_agent, dict):
        clearance_by_agent = {
            key: value for key, value in clearance_by_agent.items() if key in remaining
        }
        state["clearance_by_agent"] = clearance_by_agent
        state["clearance"] = clearance_by_agent.get(remaining[0], {})
    write_json(marker, state)


def pending_tracking_path(root: Path) -> Path:
    return root / AEGIS_PENDING_TRACKING_REL


def pending_tracking_events(root: Path) -> list[dict[str, Any]]:
    payload = read_json(pending_tracking_path(root))
    if not payload:
        return []
    events = payload.get("events")
    return (
        [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    )


def required_pending_tracking_events(root: Path) -> list[dict[str, Any]]:
    """Return events that still require strict-mode reconciliation.

    Advisory events are retained audit evidence. Missing or unknown provenance remains
    required so strict enforcement never infers that an untrusted event is safe.
    """

    return [
        event
        for event in pending_tracking_events(root)
        if str(event.get("mode") or "").strip().lower() != "advisory"
    ]
