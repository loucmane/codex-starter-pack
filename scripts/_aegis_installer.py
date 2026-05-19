"""Aegis Foundation installer core.

This module is intentionally independent of argparse so the future MCP wrapper can call
the same deterministic planning, install, and verify behavior as the CLI.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

_REPO_ROOT = Path(__file__).resolve().parents[1]
if _REPO_ROOT.as_posix() not in sys.path:
    sys.path.insert(0, _REPO_ROOT.as_posix())

from aegis_foundation.version import (
    FOUNDATION_NAME,
    FOUNDATION_VERSION,
    INSTALLER_VERSION,
    SCHEMA_VERSION,
)

PROFILE_GENERIC = "generic"
PRIMARY_AGENT_CHOICES = {"claude", "codex", "gemini", "multi", "none"}
AGENT_CHOICES = {"claude", "codex", "gemini"}
AEGIS_MANIFEST_REL = ".aegis/foundation-manifest.json"
AEGIS_CONTRACT_REL = ".aegis/contract.md"
AEGIS_REPORTS_REL = ".aegis/reports"
AEGIS_STATE_REL = ".aegis/state"
AEGIS_LOCAL_BIN_REL = ".aegis/bin/aegis"
AEGIS_CURRENT_WORK_REL = ".aegis/state/current-work.json"
AEGIS_PENDING_TRACKING_REL = ".aegis/state/pending-tracking.json"
AEGIS_PLAN_REPORT_REL = ".aegis/reports/install-plan.json"
AEGIS_INSTALL_REPORT_REL = ".aegis/reports/install-report.json"
AEGIS_VERIFY_REPORT_REL = ".aegis/reports/verification-report.json"
AEGIS_KICKOFF_REPORT_REL = ".aegis/reports/kickoff-report.json"
AEGIS_WORKFLOW_TEMPLATE_SOURCE_ROOT = "templates/aegis/workflow"
AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT = ".aegis/templates/workflow"
AEGIS_WORKFLOW_TEMPLATE_NAMES = (
    "session.md",
    "plan.md",
    "tracker.md",
    "findings.md",
    "decisions.md",
    "handoff.md",
    "implementation.md",
    "changelog.md",
)
AEGIS_LOG_SURFACES = {
    "implementation": "IMPLEMENTATION.md",
    "changelog": "CHANGELOG.md",
    "handoff": "HANDOFF.md",
    "findings": "FINDINGS.md",
    "decisions": "DECISIONS.md",
}
AEGIS_DEFAULT_LOG_SURFACES = ("implementation", "changelog", "handoff")
AEGIS_PLAN_STATUS_CHOICES = {"pending", "in-progress", "completed", "done", "n/a"}

CLAUDE_PRETOOLUSE_MATCHER = "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$"
CLAUDE_PRETOOLUSE_COMMAND = "bash $CLAUDE_PROJECT_DIR/.claude/scripts/pretooluse-gate.sh"
CLAUDE_POSTTOOLUSE_COMMAND = "bash $CLAUDE_PROJECT_DIR/.claude/scripts/posttooluse-tracking.sh"
CLAUDE_STOP_TRACKING_COMMAND = "bash $CLAUDE_PROJECT_DIR/.claude/scripts/tracking-stop-gate.sh"
CLAUDE_REQUIRED_FILES = (
    "CLAUDE.md",
    ".claude/settings.json",
    ".claude/scripts/readiness.sh",
    ".claude/scripts/pretooluse-gate.sh",
    ".claude/scripts/posttooluse-tracking.sh",
    ".claude/scripts/tracking-stop-gate.sh",
    ".claude/scripts/bash-command-guard.sh",
    ".claude/scripts/codex-path-guard.sh",
)
CLAUDE_SUPPORT_FILES = (
    ".claude/scripts/gate_lib.py",
)
CLAUDE_GATE_IDS = (
    "claude.readiness",
    "claude.pretooluse",
    "claude.posttooluse_tracking",
    "claude.stop_tracking",
    "claude.bash_command",
    "claude.protected_path",
)
CODEX_REQUIRED_FILES = (
    "CODEX.md",
    "scripts/_aegis_installer.py",
    "scripts/codex-task",
    "scripts/codex-guard",
    "scripts/_repo_structure.py",
    "scripts/template_registry.py",
    "scripts/template_governance.py",
    "scripts/template_versioning.py",
)
CODEX_GATE_IDS = (
    "codex.guard",
    "codex.work_tracking_audit",
)
SHARED_SCHEMA_FILES = (
    "schemas/aegis/foundation-manifest.schema.json",
    "schemas/aegis/profile.schema.json",
    "schemas/aegis/install-plan.schema.json",
)


class AegisError(ValueError):
    """Raised for predictable Aegis installer failures."""


@dataclass(frozen=True)
class Asset:
    """Single target file that Aegis can manage."""

    path: str
    content: bytes
    executable: bool = False
    kind: str = "managed"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_target_root(target_dir: str | Path) -> Path:
    path = Path(target_dir).expanduser()
    return path.resolve()


def _repo_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_bytes(source_root: Path, rel_path: str) -> bytes:
    path = source_root / rel_path
    if not path.exists():
        raise AegisError(f"Required source asset is missing: {rel_path}")
    return path.read_bytes()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _dump_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _load_schema(source_root: Path, name: str) -> dict[str, Any]:
    path = source_root / "schemas" / "aegis" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_with_schema(source_root: Path, schema_name: str, payload: Mapping[str, Any]) -> None:
    schema = _load_schema(source_root, schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(payload)


def _enabled_agents(primary_agent: str, agents: Sequence[str] | None) -> tuple[str, ...]:
    if primary_agent not in PRIMARY_AGENT_CHOICES:
        raise AegisError(f"Unsupported primary agent: {primary_agent}")
    requested = tuple(dict.fromkeys(agents or ()))
    unknown = sorted(set(requested) - AGENT_CHOICES)
    if unknown:
        raise AegisError(f"Unsupported enabled agent(s): {', '.join(unknown)}")
    if primary_agent == "none":
        if requested:
            raise AegisError("primary_agent=none cannot be combined with enabled agents")
        return ()
    if not requested:
        raise AegisError("Aegis install requires at least one explicit --agent value")
    if primary_agent == "multi" and len(requested) < 2:
        raise AegisError("primary_agent=multi requires at least two enabled agents")
    if primary_agent in AGENT_CHOICES and primary_agent not in requested:
        raise AegisError(f"primary_agent={primary_agent} must also be listed with --agent {primary_agent}")
    return requested


def profile_payload() -> dict[str, Any]:
    """Return the built-in generic profile contract."""

    return {
        "schema_version": SCHEMA_VERSION,
        "name": PROFILE_GENERIC,
        "description": "Generic Aegis install profile for unknown repositories.",
        "default_primary_agent": "claude",
        "supported_agents": ["claude", "codex"],
        "agent_selection_required": True,
        "paths": {
            "manifest": AEGIS_MANIFEST_REL,
            "reports": AEGIS_REPORTS_REL,
            "state": AEGIS_STATE_REL,
            "local_cli": AEGIS_LOCAL_BIN_REL,
        },
        "adapter_requirements": {
            "claude": {
                "entrypoint": "CLAUDE.md",
                "required_files": list(CLAUDE_REQUIRED_FILES),
                "required_hook_registrations": [
                    {
                        "settings_path": ".claude/settings.json",
                        "event": "PreToolUse",
                        "matcher": CLAUDE_PRETOOLUSE_MATCHER,
                        "command": CLAUDE_PRETOOLUSE_COMMAND,
                    },
                    {
                        "settings_path": ".claude/settings.json",
                        "event": "PostToolUse",
                        "matcher": CLAUDE_PRETOOLUSE_MATCHER,
                        "command": CLAUDE_POSTTOOLUSE_COMMAND,
                    },
                    {
                        "settings_path": ".claude/settings.json",
                        "event": "Stop",
                        "command": CLAUDE_STOP_TRACKING_COMMAND,
                    }
                ],
            },
            "codex": {
                "entrypoint": "CODEX.md",
                "required_files": list(CODEX_REQUIRED_FILES),
                "required_hook_registrations": [],
            },
        },
        "conditional_gates": {
            "agents.claude.enabled": list(CLAUDE_GATE_IDS),
            "agents.codex.enabled": list(CODEX_GATE_IDS),
        },
        "verification": {
            "required_commands": ["aegis verify"],
            "optional_smoke_tests": [
                "cold-session mutation blocked",
                "Aegis-native kickoff reaches READY without Taskmaster or Serena",
                "READY evidence write allowed",
                "aegis log updates session, tracker, plan, implementation, changelog, and handoff surfaces",
            ],
        },
    }


def _render_agents_doc(primary_agent: str, enabled_agents: Sequence[str]) -> bytes:
    agents = ", ".join(enabled_agents) if enabled_agents else "none"
    text = "\n".join(
        [
            "# Agents",
            "",
            "This project is managed by Aegis Foundation.",
            "",
            f"- Primary agent: `{primary_agent}`",
            f"- Enabled adapters: `{agents}`",
            "- Shared contract: `.aegis/contract.md`",
            "- Agents may read `.aegis/` directly.",
            "- Agents must not write `.aegis/` directly; use the Aegis CLI or future MCP tools.",
            "",
        ]
    )
    return text.encode("utf-8")


def _render_contract(primary_agent: str, enabled_agents: Sequence[str]) -> bytes:
    agents = ", ".join(enabled_agents) if enabled_agents else "none"
    text = "\n".join(
        [
            "# Aegis Foundation Contract",
            "",
            "Aegis Foundation is the shared portable runtime for this repository.",
            "",
            "## Agent Setup",
            "",
            f"- Primary agent: `{primary_agent}`",
            f"- Enabled adapters: `{agents}`",
            "",
            "## Access Policy",
            "",
            "- `.aegis/` is readable shared foundation state.",
            "- Direct writes to `.aegis/` are not allowed.",
            "- Mutating foundation operations go through `aegis ...`, the project-local `./.aegis/bin/aegis ...` CLI shim, or `aegis.*` MCP tools.",
            "- Taskmaster and Serena are optional integrations. Aegis-native state is sufficient for READY when they are absent.",
            "",
            "## Verification",
            "",
            "- Required gates must pass `aegis verify`.",
            "- Missing, non-executable, unconfigured, or failing required gates make verification fail.",
            "- Policy-only gates are documented limitations, not proof of enforcement.",
            "",
            "## Work Kickoff",
            "",
            "- Start work with `aegis kickoff --task <id> --slug <slug> --title \"<title>\"` or `./.aegis/bin/aegis kickoff ...` when the global command is unavailable.",
            "- Kickoff creates Aegis-native current work state, session, plan, and work-tracking files.",
            "- `.aegis/state/current-work.json` is the portable authority for READY.",
            "- Taskmaster is validated only when no Aegis current-work state exists or when current work explicitly marks Taskmaster required.",
            "- After every meaningful mutation, run `aegis log --handler <handler> --evidence <path> --note \"<past-tense note>\"` to write S:W:H:E entries to the active session, tracker, implementation log, changelog, handoff, and current plan evidence.",
            "- Use `--surface findings` or `--surface decisions` when the mutation also records a finding or decision. Use `--plan-step` and `--plan-status` for explicit scope/verify transitions.",
            "",
        ]
    )
    return text.encode("utf-8")


def _render_claude_entrypoint() -> bytes:
    text = "\n".join(
        [
            "# Claude Runtime Entry",
            "",
            "This project uses Aegis Foundation with Claude as an adapter.",
            "",
            "Before persistent mutation, Claude must be in a READY state:",
            "",
            "```bash",
            "bash .claude/scripts/readiness.sh --quick",
            "```",
            "",
            "If readiness is BLOCKED because no current work exists, start tracked work with:",
            "",
            "```bash",
            "aegis kickoff --task <id> --slug <slug> --title \"<title>\"",
            "```",
            "",
            "If `aegis` is not on PATH, use the installed project-local shim:",
            "",
            "```bash",
            "./.aegis/bin/aegis kickoff --task <id> --slug <slug> --title \"<title>\"",
            "```",
            "",
            "Project hooks route mutation tools through `.claude/scripts/pretooluse-gate.sh`.",
            "After a mutation, use `aegis log --handler <handler> --evidence <path> --note \"<past-tense note>\"` before attempting the next mutation. The command updates the session, tracker, implementation log, changelog, handoff, and plan evidence.",
            "Read `.aegis/contract.md` for the shared contract and access policy.",
            "",
        ]
    )
    return text.encode("utf-8")


def _render_claude_settings() -> bytes:
    payload = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {
            "allow": [
                "Bash(bash .claude/scripts/readiness.sh:*)",
                "Bash(bash .claude/scripts/pretooluse-gate.sh:*)",
                "Bash(bash .claude/scripts/posttooluse-tracking.sh:*)",
                "Bash(bash .claude/scripts/tracking-stop-gate.sh:*)",
                "Bash(bash .claude/scripts/codex-path-guard.sh:*)",
                "Bash(bash .claude/scripts/bash-command-guard.sh:*)",
                "Bash(aegis inspect:*)",
                "Bash(aegis status:*)",
                "Bash(aegis kickoff:*)",
                "Bash(aegis log:*)",
                "Bash(aegis verify:*)",
                "Bash(./.aegis/bin/aegis inspect:*)",
                "Bash(./.aegis/bin/aegis status:*)",
                "Bash(./.aegis/bin/aegis kickoff:*)",
                "Bash(./.aegis/bin/aegis log:*)",
                "Bash(./.aegis/bin/aegis verify:*)",
                "Bash(git status:*)",
                "Bash(git diff:*)",
                "Bash(date:*)",
                "Bash(ls:*)",
                "Bash(cat:*)",
                "Bash(rg:*)",
            ],
            "deny": [
                "Bash(rm -rf:*)",
                "Bash(git push --force:*)",
                "Bash(git push -f:*)",
                "Bash(git reset --hard:*)",
            ],
        },
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": CLAUDE_PRETOOLUSE_MATCHER,
                    "hooks": [
                        {
                            "type": "command",
                            "command": CLAUDE_PRETOOLUSE_COMMAND,
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": CLAUDE_PRETOOLUSE_MATCHER,
                    "hooks": [
                        {
                            "type": "command",
                            "command": CLAUDE_POSTTOOLUSE_COMMAND,
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": CLAUDE_STOP_TRACKING_COMMAND,
                        }
                    ],
                }
            ]
        },
    }
    return _dump_json(payload).encode("utf-8")


def _render_local_cli_shim(source_root: Path) -> bytes:
    source = source_root.resolve().as_posix()
    text = "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "SELF=\"$0\"",
            "SELF_RESOLVED=\"$(cd \"$(dirname \"$SELF\")\" && pwd -P)/$(basename \"$SELF\")\"",
            "if command -v aegis >/dev/null 2>&1; then",
            "  RESOLVED=\"$(command -v aegis)\"",
            "  RESOLVED_ABS=\"$(cd \"$(dirname \"$RESOLVED\")\" && pwd -P)/$(basename \"$RESOLVED\")\"",
            "  if [ \"$RESOLVED_ABS\" != \"$SELF_RESOLVED\" ]; then",
            "    exec \"$RESOLVED\" \"$@\"",
            "  fi",
            "fi",
            "",
            "if python3 -c 'import aegis_foundation.cli' >/dev/null 2>&1; then",
            "  exec python3 -m aegis_foundation.cli \"$@\"",
            "fi",
            "",
            f"AEGIS_SOURCE_FALLBACK=\"{source}\"",
            "if [ -n \"${AEGIS_SOURCE_ROOT:-}\" ]; then",
            "  AEGIS_SOURCE_FALLBACK=\"$AEGIS_SOURCE_ROOT\"",
            "fi",
            "if [ -d \"$AEGIS_SOURCE_FALLBACK\" ]; then",
            "  export PYTHONPATH=\"$AEGIS_SOURCE_FALLBACK${PYTHONPATH:+:$PYTHONPATH}\"",
            "  exec python3 -m aegis_foundation.cli --source-root \"$AEGIS_SOURCE_FALLBACK\" \"$@\"",
            "fi",
            "",
            "echo \"Aegis CLI is unavailable. Install aegis-foundation, add aegis to PATH, or set AEGIS_SOURCE_ROOT.\" >&2",
            "exit 127",
            "",
        ]
    )
    return text.encode("utf-8")


def _asset_from_source(source_root: Path, rel_path: str, *, kind: str = "managed") -> Asset:
    path = source_root / rel_path
    return Asset(path=rel_path, content=_read_bytes(source_root, rel_path), executable=os.access(path, os.X_OK), kind=kind)


def _asset_from_source_as(source_root: Path, source_rel_path: str, target_rel_path: str, *, kind: str = "managed") -> Asset:
    path = source_root / source_rel_path
    return Asset(path=target_rel_path, content=_read_bytes(source_root, source_rel_path), executable=os.access(path, os.X_OK), kind=kind)


def _base_assets(source_root: Path, primary_agent: str, enabled_agents: Sequence[str]) -> list[Asset]:
    assets = [
        Asset("AGENTS.md", _render_agents_doc(primary_agent, enabled_agents)),
        Asset(AEGIS_CONTRACT_REL, _render_contract(primary_agent, enabled_agents)),
        Asset(AEGIS_LOCAL_BIN_REL, _render_local_cli_shim(source_root), executable=True),
    ]
    for rel_path in SHARED_SCHEMA_FILES:
        assets.append(_asset_from_source(source_root, rel_path))
    for template_name in AEGIS_WORKFLOW_TEMPLATE_NAMES:
        assets.append(
            _asset_from_source_as(
                source_root,
                f"{AEGIS_WORKFLOW_TEMPLATE_SOURCE_ROOT}/{template_name}",
                f"{AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT}/{template_name}",
            )
        )
    return assets


def _adapter_assets(source_root: Path, primary_agent: str, enabled_agents: Sequence[str]) -> list[Asset]:
    assets: list[Asset] = []
    if "claude" in enabled_agents:
        assets.extend(
            [
                Asset("CLAUDE.md", _render_claude_entrypoint(), kind="adapter"),
                Asset(".claude/settings.json", _render_claude_settings(), kind="adapter"),
            ]
        )
        for rel_path in CLAUDE_REQUIRED_FILES:
            if rel_path in {"CLAUDE.md", ".claude/settings.json"}:
                continue
            assets.append(_asset_from_source(source_root, rel_path, kind="adapter"))
        for rel_path in CLAUDE_SUPPORT_FILES:
            assets.append(_asset_from_source(source_root, rel_path, kind="adapter"))
    if "codex" in enabled_agents:
        for rel_path in CODEX_REQUIRED_FILES:
            assets.append(_asset_from_source(source_root, rel_path, kind="adapter"))
    return assets


def _managed_assets(source_root: Path, primary_agent: str, enabled_agents: Sequence[str]) -> list[Asset]:
    return _base_assets(source_root, primary_agent, enabled_agents) + _adapter_assets(source_root, primary_agent, enabled_agents)


def _agent_records(enabled_agents: Sequence[str], managed_assets: Sequence[Asset]) -> dict[str, dict[str, Any]]:
    managed_by_agent: dict[str, list[str]] = {
        "claude": [asset.path for asset in managed_assets if asset.path == "CLAUDE.md" or asset.path.startswith(".claude/")],
        "codex": [asset.path for asset in managed_assets if asset.path == "CODEX.md" or asset.path.startswith("scripts/")],
        "gemini": [],
    }
    return {
        "claude": {
            "enabled": "claude" in enabled_agents,
            "available": True,
            "entrypoint": "CLAUDE.md",
            "managed_files": managed_by_agent["claude"],
            "gate_ids": list(CLAUDE_GATE_IDS) if "claude" in enabled_agents else [],
        },
        "codex": {
            "enabled": "codex" in enabled_agents,
            "available": True,
            "entrypoint": "CODEX.md",
            "managed_files": managed_by_agent["codex"],
            "gate_ids": list(CODEX_GATE_IDS) if "codex" in enabled_agents else list(CODEX_GATE_IDS),
        },
        "gemini": {
            "enabled": "gemini" in enabled_agents,
            "available": False,
            "entrypoint": None,
            "managed_files": [],
            "gate_ids": [],
        },
    }


def _gate(
    gate_id: str,
    *,
    required: bool,
    enforcement: str,
    scope: str,
    adapter: str | None = None,
    path: str | None = None,
    command: str | None = None,
    settings_path: str | None = None,
    hook_event: str | None = None,
    hook_matcher: str | None = None,
    unsupported_reason: str | None = None,
    method: str,
    failure_mode: str,
    expected: str | bool | None = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": gate_id,
        "required": required,
        "enforcement": enforcement,
        "scope": scope,
        "verification": {
            "method": method,
            "failure_mode": failure_mode,
            "expected": expected,
        },
    }
    for key, value in {
        "adapter": adapter,
        "path": path,
        "command": command,
        "settings_path": settings_path,
        "hook_event": hook_event,
        "hook_matcher": hook_matcher,
        "unsupported_reason": unsupported_reason,
    }.items():
        if value is not None:
            payload[key] = value
    return payload


def _gates(enabled_agents: Sequence[str]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    if "claude" in enabled_agents:
        gates.extend(
            [
                _gate(
                    "claude.readiness",
                    required=True,
                    enforcement="mechanical",
                    scope="adapter",
                    adapter="claude",
                    path=".claude/scripts/readiness.sh",
                    method="executable",
                    failure_mode="fail",
                ),
                _gate(
                    "claude.pretooluse",
                    required=True,
                    enforcement="mechanical",
                    scope="adapter",
                    adapter="claude",
                    path=".claude/scripts/pretooluse-gate.sh",
                    settings_path=".claude/settings.json",
                    hook_event="PreToolUse",
                    hook_matcher=CLAUDE_PRETOOLUSE_MATCHER,
                    method="settings_hook",
                    failure_mode="fail",
                    expected=CLAUDE_PRETOOLUSE_COMMAND,
                ),
                _gate(
                    "claude.posttooluse_tracking",
                    required=True,
                    enforcement="mechanical",
                    scope="adapter",
                    adapter="claude",
                    path=".claude/scripts/posttooluse-tracking.sh",
                    settings_path=".claude/settings.json",
                    hook_event="PostToolUse",
                    hook_matcher=CLAUDE_PRETOOLUSE_MATCHER,
                    method="settings_hook",
                    failure_mode="fail",
                    expected=CLAUDE_POSTTOOLUSE_COMMAND,
                ),
                _gate(
                    "claude.stop_tracking",
                    required=True,
                    enforcement="mechanical",
                    scope="adapter",
                    adapter="claude",
                    path=".claude/scripts/tracking-stop-gate.sh",
                    settings_path=".claude/settings.json",
                    hook_event="Stop",
                    method="settings_hook",
                    failure_mode="fail",
                    expected=CLAUDE_STOP_TRACKING_COMMAND,
                ),
                _gate(
                    "claude.bash_command",
                    required=True,
                    enforcement="mechanical",
                    scope="adapter",
                    adapter="claude",
                    path=".claude/scripts/bash-command-guard.sh",
                    method="executable",
                    failure_mode="fail",
                ),
                _gate(
                    "claude.protected_path",
                    required=True,
                    enforcement="mechanical",
                    scope="adapter",
                    adapter="claude",
                    path=".claude/scripts/codex-path-guard.sh",
                    method="executable",
                    failure_mode="fail",
                ),
            ]
        )
    if "codex" in enabled_agents:
        gates.extend(
            [
                _gate(
                    "codex.guard",
                    required=True,
                    enforcement="verification",
                    scope="adapter",
                    adapter="codex",
                    path="scripts/codex-guard",
                    method="executable",
                    failure_mode="fail",
                ),
                _gate(
                    "codex.work_tracking_audit",
                    required=True,
                    enforcement="verification",
                    scope="adapter",
                    adapter="codex",
                    path="scripts/codex-task",
                    method="executable",
                    failure_mode="fail",
                ),
            ]
        )
    gates.append(
        _gate(
            "mcp.memory_write",
            required=False,
            enforcement="policy",
            scope="shared",
            unsupported_reason="MCP memory writes are not mechanically hookable in every client.",
            method="manual",
            failure_mode="unsupported",
            expected=None,
        )
    )
    return gates


def _manifest_payload(
    source_root: Path,
    target_root: Path,
    primary_agent: str,
    enabled_agents: Sequence[str],
    *,
    installed_at: str,
) -> dict[str, Any]:
    assets = _managed_assets(source_root, primary_agent, enabled_agents)
    existing = _read_json(target_root / AEGIS_MANIFEST_REL)
    verification = (
        existing.get("verification")
        if existing and isinstance(existing.get("verification"), Mapping)
        else {
            "status": "never",
            "last_verified_at": None,
            "reports": [],
        }
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "foundation_name": FOUNDATION_NAME,
        "foundation_version": FOUNDATION_VERSION,
        "installer_version": INSTALLER_VERSION,
        "installed_at": installed_at,
        "profile": PROFILE_GENERIC,
        "primary_agent": primary_agent,
        "entrypoints": {
            "shared": "AGENTS.md",
            "contract": AEGIS_CONTRACT_REL,
            "codex": "CODEX.md",
            "claude": "CLAUDE.md",
            "gemini": None,
        },
        "interfaces": {
            "cli": {
                "command": "aegis",
            },
            "mcp": {
                "namespace": "aegis",
                "available": False,
                "endpoint": None,
            },
        },
        "access_policy": {
            "read_interface": "direct_read_or_aegis_cli",
            "write_interface": "aegis_cli_or_mcp",
            "direct_aegis_writes": False,
        },
        "agents": _agent_records(enabled_agents, assets),
        "capabilities": {
            "taskmaster": (target_root / ".taskmaster").exists(),
            "work_tracking": (target_root / "docs" / "ai" / "work-tracking").exists(),
            "ci": (target_root / ".github" / "workflows").exists(),
            "mcp_contract": True,
        },
        "gates": _gates(enabled_agents),
        "managed_files": [
            {"path": AEGIS_MANIFEST_REL, "kind": "managed"},
            *({"path": asset.path, "kind": asset.kind} for asset in assets),
        ],
        "customized_files": [],
        "verification": verification,
    }
    _validate_with_schema(source_root, "foundation-manifest.schema.json", payload)
    return payload


def _installed_at_for_plan(target_root: Path) -> str:
    existing = _read_json(target_root / AEGIS_MANIFEST_REL)
    if existing and isinstance(existing.get("installed_at"), str):
        return str(existing["installed_at"])
    return _iso_now()


def _plan_operations(target_root: Path, assets: Sequence[Asset], manifest_bytes: bytes) -> list[dict[str, Any]]:
    all_assets = [*assets, Asset(AEGIS_MANIFEST_REL, manifest_bytes)]
    operations: list[dict[str, Any]] = []
    for asset in all_assets:
        target = target_root / asset.path
        if not target.exists():
            operations.append(
                {
                    "action": "create",
                    "path": asset.path,
                    "classification": "create",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": "Target file is missing.",
                }
            )
            continue
        if target.is_dir():
            operations.append(
                {
                    "action": "conflict",
                    "path": asset.path,
                    "classification": "conflict",
                    "safe_to_apply": False,
                    "managed": False,
                    "reason": "Target path is a directory.",
                }
            )
            continue
        if target.read_bytes() == asset.content:
            operations.append(
                {
                    "action": "skip",
                    "path": asset.path,
                    "classification": "skip",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": "Target file already matches expected content.",
                }
            )
            continue
        operations.append(
            {
                "action": "manual-review",
                "path": asset.path,
                "classification": "manual-review",
                "safe_to_apply": False,
                "managed": False,
                "reason": "Existing file differs and Aegis V1 refuses unsafe overwrites.",
            }
        )
    return operations


def _summary(operations: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {key: 0 for key in ("creates", "modifies", "skips", "conflicts", "manual_reviews")}
    for operation in operations:
        classification = operation.get("classification")
        if classification == "create":
            counts["creates"] += 1
        elif classification == "modify":
            counts["modifies"] += 1
        elif classification == "skip":
            counts["skips"] += 1
        elif classification == "conflict":
            counts["conflicts"] += 1
        elif classification == "manual-review":
            counts["manual_reviews"] += 1
    return counts


def _expected_manifest_summary(primary_agent: str, enabled_agents: Sequence[str]) -> dict[str, Any]:
    return {
        "path": AEGIS_MANIFEST_REL,
        "profile": PROFILE_GENERIC,
        "primary_agent": primary_agent,
        "agents": {
            agent: {
                "enabled": agent in enabled_agents,
                "gate_ids": list(CLAUDE_GATE_IDS if agent == "claude" else CODEX_GATE_IDS if agent == "codex" else ()),
            }
            for agent in ("claude", "codex", "gemini")
        },
        "gates": [gate["id"] for gate in _gates(enabled_agents)],
    }


def _verification_requirements(enabled_agents: Sequence[str]) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": gate["id"],
            "required": bool(gate["required"]),
            "enforcement": str(gate["enforcement"]),
            "failure_mode": str(gate["verification"]["failure_mode"]),
        }
        for gate in _gates(enabled_agents)
    ]


def inspect_project(target_dir: str | Path, *, profile: str = PROFILE_GENERIC) -> dict[str, Any]:
    if profile != PROFILE_GENERIC:
        raise AegisError(f"Unsupported Aegis profile in V1: {profile}")
    target_root = _resolve_target_root(target_dir)
    manifest = _read_json(target_root / AEGIS_MANIFEST_REL)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_root": str(target_root),
        "profile": profile,
        "exists": target_root.exists(),
        "aegis": {
            "installed": manifest is not None,
            "manifest_path": AEGIS_MANIFEST_REL,
            "foundation_version": manifest.get("foundation_version") if manifest else None,
            "primary_agent": manifest.get("primary_agent") if manifest else None,
        },
        "detected_agents": {
            "claude": (target_root / "CLAUDE.md").exists() or (target_root / ".claude").exists(),
            "codex": (target_root / "CODEX.md").exists() or (target_root / ".codex").exists(),
            "gemini": (target_root / "GEMINI.md").exists() or (target_root / ".gemini").exists(),
        },
        "paths": {
            "manifest": str(target_root / AEGIS_MANIFEST_REL),
            "reports": str(target_root / AEGIS_REPORTS_REL),
            "state": str(target_root / AEGIS_STATE_REL),
        },
    }


def status(target_dir: str | Path, *, source_root: str | Path) -> dict[str, Any]:
    """Report installed Aegis release state without mutating the target."""

    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest_exists = manifest_path.exists()
    manifest = _read_json(manifest_path)
    current_versions = {
        "foundation_version": FOUNDATION_VERSION,
        "installer_version": INSTALLER_VERSION,
        "schema_version": SCHEMA_VERSION,
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "target_root": str(target_root),
        "manifest_path": AEGIS_MANIFEST_REL,
        "read_only": True,
        "installed": manifest is not None,
        "current": current_versions,
        "installed_versions": None,
        "migration_required": False,
        "status": "not_installed",
        "checks": [],
        "recommended_actions": [
            "Run aegis plan-install before applying Aegis to this target.",
        ],
    }
    if manifest is None:
        if manifest_exists:
            payload["status"] = "invalid_manifest"
            payload["recommended_actions"] = [
                "Repair or restore .aegis/foundation-manifest.json before upgrading.",
                "Use git history or recorded backups for rollback.",
            ]
        return payload

    installed_versions = {
        "foundation_version": manifest.get("foundation_version"),
        "installer_version": manifest.get("installer_version"),
        "schema_version": manifest.get("schema_version"),
    }
    checks: list[dict[str, Any]] = []
    try:
        _validate_with_schema(source, "foundation-manifest.schema.json", manifest)
        checks.append(
            {
                "id": "manifest_schema",
                "status": "pass",
                "message": "manifest schema valid",
            }
        )
    except ValidationError as exc:
        checks.append(
            {
                "id": "manifest_schema",
                "status": "fail",
                "message": exc.message,
            }
        )

    for key, current_value in current_versions.items():
        installed_value = installed_versions.get(key)
        checks.append(
            {
                "id": key,
                "status": "pass" if installed_value == current_value else "fail",
                "installed": installed_value,
                "current": current_value,
            }
        )

    failed = [check for check in checks if check.get("status") == "fail"]
    payload.update(
        {
            "installed": True,
            "installed_versions": installed_versions,
            "migration_required": bool(failed),
            "status": "migration_required" if failed else "current",
            "checks": checks,
            "recommended_actions": (
                [
                    "Run aegis plan-install and review managed-file changes before upgrading.",
                    "Run aegis install --apply only after reviewing the plan.",
                    "Run aegis verify after upgrading and keep .aegis/reports/ as evidence.",
                ]
                if failed
                else [
                    "No Aegis package migration is required.",
                    "Run aegis verify after local environment or hook changes.",
                ]
            ),
        }
    )
    return payload


def plan_install(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    profile: str = PROFILE_GENERIC,
    primary_agent: str,
    agents: Sequence[str] | None,
    mode: str = "dry_run",
    apply_confirmed: bool = False,
) -> dict[str, Any]:
    if profile != PROFILE_GENERIC:
        raise AegisError(f"Unsupported Aegis profile in V1: {profile}")
    if mode not in {"dry_run", "apply"}:
        raise AegisError(f"Unsupported install mode: {mode}")
    enabled_agents = _enabled_agents(primary_agent, agents)
    source = Path(source_root).resolve()
    target_root = _resolve_target_root(target_dir)
    installed_at = _installed_at_for_plan(target_root)
    assets = _managed_assets(source, primary_agent, enabled_agents)
    manifest = _manifest_payload(source, target_root, primary_agent, enabled_agents, installed_at=installed_at)
    manifest_bytes = _dump_json(manifest).encode("utf-8")
    operations = _plan_operations(target_root, assets, manifest_bytes)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": f"aegis-{profile}-{_utc_now().strftime('%Y%m%d%H%M%S')}",
        "generated_at": _iso_now(),
        "target_root": ".",
        "profile": profile,
        "mode": mode,
        "apply_confirmed": apply_confirmed,
        "agent_selection": {
            "source": "non_interactive",
            "primary_agent": primary_agent,
            "enabled_agents": list(enabled_agents),
            "explicit_flags_required": True,
        },
        "operations": operations,
        "expected_manifest": _expected_manifest_summary(primary_agent, enabled_agents),
        "verification_requirements": _verification_requirements(enabled_agents),
        "reports": {
            "plan_json": AEGIS_PLAN_REPORT_REL,
            "install_json": AEGIS_INSTALL_REPORT_REL if mode == "apply" else None,
            "verification_json": AEGIS_VERIFY_REPORT_REL if mode == "apply" else None,
            "markdown": ".aegis/reports/install-plan.md",
        },
        "summary": _summary(operations),
    }
    _validate_with_schema(source, "install-plan.schema.json", payload)
    return payload


def _unsafe_operations(plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [operation for operation in plan.get("operations", []) if not operation.get("safe_to_apply")]


def _write_asset(target_root: Path, asset: Asset) -> None:
    target = target_root / asset.path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(asset.content)
    if asset.executable:
        current_mode = target.stat().st_mode
        target.chmod(current_mode | 0o111)


def _cleanup_created_paths(target_root: Path, rel_paths: Iterable[str]) -> dict[str, Any]:
    removed: list[str] = []
    errors: list[dict[str, str]] = []
    targets = sorted(
        {target_root / rel_path for rel_path in rel_paths},
        key=lambda path: len(path.parts),
        reverse=True,
    )
    parent_candidates: set[Path] = set()
    for target in targets:
        parent_candidates.add(target.parent)
        try:
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            elif target.exists() or target.is_symlink():
                target.unlink()
            else:
                continue
            removed.append(_repo_path(target, target_root))
        except OSError as exc:
            errors.append({"path": _repo_path(target, target_root), "error": str(exc)})

    for parent in sorted(parent_candidates, key=lambda path: len(path.parts), reverse=True):
        current = parent
        while current != target_root and target_root in current.parents:
            try:
                current.rmdir()
                removed.append(_repo_path(current, target_root))
            except OSError:
                break
            current = current.parent

    return {
        "status": "partial" if errors else "completed",
        "removed_paths": sorted(set(removed)),
        "errors": errors,
    }


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise AegisError("slug must contain at least one alphanumeric character")
    return slug


def _normalize_task_id(task_id: str | int) -> str:
    value = str(task_id).strip()
    if not re.fullmatch(r"\d+", value):
        raise AegisError("Aegis kickoff currently requires a numeric task id")
    return value


def _run_target_git(target_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _current_branch(target_root: Path) -> str:
    result = _run_target_git(target_root, "branch", "--show-current")
    if result.returncode != 0 or not result.stdout.strip():
        detail = (result.stderr or result.stdout or "empty branch").strip()
        raise AegisError(f"could not determine current git branch: {detail}")
    return result.stdout.strip()


def _ensure_git_work_tree(target_root: Path) -> None:
    result = _run_target_git(target_root, "rev-parse", "--is-inside-work-tree")
    if result.returncode != 0 or result.stdout.strip() != "true":
        detail = (result.stderr or result.stdout or "not a git work tree").strip()
        raise AegisError(f"Aegis kickoff requires a git work tree: {detail}")


def _branch_task_id(branch: str) -> str | None:
    match = re.search(r"(?:^|[-_/])task-?(\d+)(?:[-_/]|$)", branch)
    return match.group(1) if match else None


def _ensure_task_branch(target_root: Path, task_id: str, slug: str, *, create_branch: bool) -> dict[str, Any]:
    before = _current_branch(target_root)
    if _branch_task_id(before) == task_id:
        return {
            "before": before,
            "current": before,
            "action": "already_on_task_branch",
            "created": False,
        }
    if not create_branch:
        raise AegisError(
            f"current branch '{before}' does not contain task id {task_id}; rerun with branch creation enabled"
        )

    branch_name = f"feat/task-{task_id}-{slug}"
    exists = _run_target_git(target_root, "rev-parse", "--verify", "--quiet", branch_name)
    if exists.returncode == 0:
        switch = _run_target_git(target_root, "switch", branch_name)
        action = "switched_existing_branch"
        created = False
    else:
        switch = _run_target_git(target_root, "switch", "-c", branch_name)
        action = "created_branch"
        created = True
    if switch.returncode != 0:
        detail = (switch.stderr or switch.stdout or "git switch failed").strip()
        raise AegisError(f"could not switch to task branch '{branch_name}': {detail}")
    return {
        "before": before,
        "current": _current_branch(target_root),
        "action": action,
        "created": created,
    }


def _replace_symlink(link: Path, target: str) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.exists() or link.is_symlink():
        if not link.is_symlink():
            raise AegisError(f"cannot replace non-symlink current pointer: {link}")
        link.unlink()
    link.symlink_to(target)


def _next_session_rel(target_root: Path, task_id: str, slug: str, now: datetime) -> str:
    date_text = now.strftime("%Y-%m-%d")
    month_rel = Path("sessions") / now.strftime("%Y") / now.strftime("%m")
    for index in range(1, 1000):
        candidate = month_rel / f"{date_text}-{index:03d}-task{task_id}-{slug}.md"
        if not (target_root / candidate).exists():
            return candidate.as_posix()
    raise AegisError("could not allocate session file name")


def _plan_rel(task_id: str, slug: str, now: datetime) -> str:
    return f"plans/{now.strftime('%Y-%m-%d')}-task{task_id}-{slug}.md"


def _work_tracking_rel(task_id: str, slug: str, now: datetime) -> str:
    return f"docs/ai/work-tracking/active/{now.strftime('%Y%m%d')}-task{task_id}-{slug}-ACTIVE"


def _default_goals() -> list[str]:
    return [
        "Define scope and constraints before implementation",
        "Implement only task-scoped changes",
        "Verify behavior with captured evidence before completion",
    ]


def _read_workflow_template(target_root: Path, source_root: Path | None, template_name: str) -> str:
    candidates: list[Path] = []
    if source_root is not None:
        candidates.append(source_root / AEGIS_WORKFLOW_TEMPLATE_SOURCE_ROOT / template_name)
    candidates.append(target_root / AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT / template_name)
    candidates.append(_REPO_ROOT / AEGIS_WORKFLOW_TEMPLATE_SOURCE_ROOT / template_name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise AegisError(f"Required workflow template is missing: {template_name}")


def _render_workflow_template(
    target_root: Path,
    source_root: Path | None,
    template_name: str,
    context: Mapping[str, str],
) -> str:
    rendered = _read_workflow_template(target_root, source_root, template_name)
    for key, value in sorted(context.items(), key=lambda item: len(item[0]), reverse=True):
        rendered = rendered.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"{{\s*([a-zA-Z0-9_]+)\s*}}", rendered)))
    if unresolved:
        raise AegisError(f"Workflow template {template_name} has unresolved variable(s): {', '.join(unresolved)}")
    return rendered.rstrip() + "\n"


def _workflow_template_context(
    *,
    task_id: str,
    title: str,
    slug: str,
    goals: Sequence[str],
    now: datetime,
    branch_current: str,
    session_rel: str,
    plan_rel: str,
    work_rel: str,
    reports_rel: str,
) -> dict[str, str]:
    selected_goals = list(goals or _default_goals())
    session_id = Path(session_rel).stem
    work_context = f"task{task_id}-{slug}"
    tracker_rel = f"{work_rel}/TRACKER.md"
    return {
        "task_id": task_id,
        "title": title,
        "slug": slug,
        "session_id": session_id,
        "session_value": now.strftime("%Y%m%d"),
        "work_context": work_context,
        "date": now.strftime("%Y-%m-%d"),
        "time_label": now.strftime("%H:%M %Z").strip(),
        "time_hm": now.strftime("%H:%M"),
        "timestamp_full": now.strftime("%Y-%m-%d %H:%M:%S %Z %z").strip(),
        "timestamp_tracker": now.strftime("%Y-%m-%d %H:%M %Z").strip(),
        "created_at": now.isoformat(),
        "branch_current": branch_current,
        "current_work_rel": AEGIS_CURRENT_WORK_REL,
        "session_rel": session_rel,
        "plan_rel": plan_rel,
        "work_rel": work_rel,
        "tracker_rel": tracker_rel,
        "reports_rel": reports_rel,
        "goals_checklist": "\n".join(f"- [ ] {goal}" for goal in selected_goals),
        "goals_bullets": "\n".join(f"- {goal}" for goal in selected_goals),
    }


def _write_text(target_root: Path, rel_path: str, content: str) -> None:
    path = target_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _update_manifest_after_kickoff(target_root: Path) -> None:
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest = _read_json(manifest_path)
    if manifest is None:
        return
    capabilities = manifest.get("capabilities")
    if isinstance(capabilities, dict):
        capabilities["work_tracking"] = True
    manifest_path.write_text(_dump_json(manifest), encoding="utf-8")


def kickoff(
    target_dir: str | Path,
    *,
    task_id: str | int,
    slug: str,
    title: str,
    goals: Sequence[str] | None = None,
    create_branch: bool = True,
    source_root: str | Path | None = None,
) -> dict[str, Any]:
    """Create Aegis-native current work state for an installed target project."""

    target_root = _resolve_target_root(target_dir)
    resolved_source = Path(source_root).resolve() if source_root is not None else None
    if not (target_root / AEGIS_MANIFEST_REL).is_file():
        raise AegisError("Aegis kickoff requires an installed .aegis/foundation-manifest.json")
    _ensure_git_work_tree(target_root)

    normalized_task_id = _normalize_task_id(task_id)
    normalized_slug = _slugify(slug)
    clean_title = title.strip()
    if not clean_title:
        raise AegisError("title is required")

    now = datetime.now().astimezone().replace(microsecond=0)
    selected_goals = list(goals or _default_goals())
    branch = _ensure_task_branch(target_root, normalized_task_id, normalized_slug, create_branch=create_branch)

    session_rel = _next_session_rel(target_root, normalized_task_id, normalized_slug, now)
    plan_rel = _plan_rel(normalized_task_id, normalized_slug, now)
    work_rel = _work_tracking_rel(normalized_task_id, normalized_slug, now)
    reports_rel = f"{work_rel}/reports/{normalized_slug}"
    template_context = _workflow_template_context(
        task_id=normalized_task_id,
        title=clean_title,
        slug=normalized_slug,
        goals=selected_goals,
        now=now,
        branch_current=str(branch["current"]),
        session_rel=session_rel,
        plan_rel=plan_rel,
        work_rel=work_rel,
        reports_rel=reports_rel,
    )

    _write_text(target_root, session_rel, _render_workflow_template(target_root, resolved_source, "session.md", template_context))
    _replace_symlink(target_root / "sessions" / "current", str(Path(session_rel).relative_to("sessions")))
    state_payload = {
        "schema_version": SCHEMA_VERSION,
        "current": Path(session_rel).name,
        "current_path": session_rel,
        "task": {
            "id": normalized_task_id,
            "slug": normalized_slug,
            "title": clean_title,
            "status": "in-progress",
        },
        "updated_at": _iso_now(),
    }
    _write_text(target_root, "sessions/state.json", _dump_json(state_payload))

    _write_text(target_root, plan_rel, _render_workflow_template(target_root, resolved_source, "plan.md", template_context))
    _replace_symlink(target_root / "plans" / "current", Path(plan_rel).name)

    work_files = {
        f"{work_rel}/TRACKER.md": _render_workflow_template(target_root, resolved_source, "tracker.md", template_context),
        f"{work_rel}/FINDINGS.md": _render_workflow_template(target_root, resolved_source, "findings.md", template_context),
        f"{work_rel}/DECISIONS.md": _render_workflow_template(target_root, resolved_source, "decisions.md", template_context),
        f"{work_rel}/HANDOFF.md": _render_workflow_template(target_root, resolved_source, "handoff.md", template_context),
        f"{work_rel}/IMPLEMENTATION.md": _render_workflow_template(target_root, resolved_source, "implementation.md", template_context),
        f"{work_rel}/CHANGELOG.md": _render_workflow_template(target_root, resolved_source, "changelog.md", template_context),
    }
    for rel_path, content in work_files.items():
        _write_text(target_root, rel_path, content)
    (target_root / work_rel / "designs").mkdir(parents=True, exist_ok=True)
    (target_root / reports_rel).mkdir(parents=True, exist_ok=True)

    current_work = {
        "schema_version": SCHEMA_VERSION,
        "status": "in-progress",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "updated_at": _iso_now(),
        "task": {
            "id": normalized_task_id,
            "slug": normalized_slug,
            "title": clean_title,
            "status": "in-progress",
        },
        "branch": branch,
        "paths": {
            "session": session_rel,
            "session_current": "sessions/current",
            "plan": plan_rel,
            "plan_current": "plans/current",
            "work_tracking": work_rel,
            "reports": reports_rel,
            "workflow_templates": AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT,
        },
        "integrations": {
            "taskmaster": {
                "required": False,
                "detected": (target_root / ".taskmaster").exists(),
            },
            "serena": {
                "required": False,
                "detected": (target_root / ".serena").exists(),
            },
        },
    }
    _write_text(target_root, AEGIS_CURRENT_WORK_REL, _dump_json(current_work))
    _update_manifest_after_kickoff(target_root)

    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "started",
        "started_at": _iso_now(),
        "target_root": str(target_root),
        "task": current_work["task"],
        "branch": branch,
        "paths": current_work["paths"],
        "integrations": current_work["integrations"],
        "workflow_templates": AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT,
    }
    _write_text(target_root, AEGIS_KICKOFF_REPORT_REL, _dump_json(report))
    return report


def _current_work_payload(target_root: Path) -> dict[str, Any]:
    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if current_work is None:
        raise AegisError("Aegis log requires .aegis/state/current-work.json; run aegis kickoff first")
    return current_work


def _normalize_evidence(target_root: Path, evidence: str) -> str:
    if not evidence.strip():
        raise AegisError("evidence is required")
    path = Path(evidence).expanduser()
    if path.is_absolute():
        try:
            return path.resolve().relative_to(target_root).as_posix()
        except ValueError:
            return path.as_posix()
    return evidence.strip().lstrip("./")


def _append_progress_entry(path: Path, heading: str, line: str) -> None:
    if not path.is_file():
        raise AegisError(f"required workflow file missing: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        heading_index = next(index for index, value in enumerate(lines) if value.strip() == heading)
    except StopIteration:
        lines.extend(["", heading, line])
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return

    insert_at = len(lines)
    for index in range(heading_index + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("#") and stripped != heading:
            insert_at = index
            break
    while insert_at > heading_index + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, line)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _normalize_log_surfaces(surfaces: Sequence[str] | None) -> tuple[str, ...]:
    selected = tuple(surfaces or AEGIS_DEFAULT_LOG_SURFACES)
    if not selected:
        return ()
    normalized: list[str] = []
    unknown: list[str] = []
    for value in selected:
        key = value.strip().lower()
        if not key:
            continue
        if key not in AEGIS_LOG_SURFACES:
            unknown.append(value)
            continue
        if key not in normalized:
            normalized.append(key)
    if unknown:
        choices = ", ".join(sorted(AEGIS_LOG_SURFACES))
        raise AegisError(f"unknown log surface(s): {', '.join(unknown)}; expected one of: {choices}")
    return tuple(normalized)


def _normalize_plan_status(status: str | None) -> str:
    clean = (status or "in-progress").strip().lower()
    if clean not in AEGIS_PLAN_STATUS_CHOICES:
        choices = ", ".join(sorted(AEGIS_PLAN_STATUS_CHOICES))
        raise AegisError(f"unknown plan status: {status}; expected one of: {choices}")
    return "completed" if clean == "done" else clean


def _update_tracker_timestamp(tracker_path: Path, timestamp: str) -> None:
    lines = tracker_path.read_text(encoding="utf-8").splitlines()
    changed = False
    for index, line in enumerate(lines):
        if line.startswith("**Last Updated**:"):
            lines[index] = f"**Last Updated**: {timestamp}"
            changed = True
            break
    if changed:
        tracker_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _update_tracker_plan_step(tracker_path: Path, plan_step: str, plan_status: str) -> None:
    if plan_status != "completed":
        return
    lines = tracker_path.read_text(encoding="utf-8").splitlines()
    changed = False
    for index, line in enumerate(lines):
        if line.startswith("- [ ] ") and plan_step in line:
            lines[index] = line.replace("- [ ] ", "- [x] ", 1)
            changed = True
    if changed:
        tracker_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _update_plan_table(
    plan_path: Path,
    *,
    plan_step: str,
    plan_status: str,
    evidence_rel: str,
    timestamp: str,
) -> bool:
    if not plan_path.is_file():
        raise AegisError(f"required workflow file missing: {plan_path}")
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    changed = False
    for index, line in enumerate(lines):
        if not line.startswith(f"| {plan_step} |"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) != 4:
            raise AegisError(f"plan row for {plan_step} is malformed")
        evidence = columns[2]
        if evidence_rel not in evidence:
            evidence = f"{evidence}; {evidence_rel}" if evidence else evidence_rel
        current_status = columns[3]
        next_status = current_status
        if current_status not in {"completed", "n/a"} or plan_status == "completed":
            next_status = plan_status
        lines[index] = f"| {columns[0]} | {columns[1]} | {evidence} | {next_status} |"
        changed = True
        break
    if not changed:
        raise AegisError(f"plan step not found in current plan: {plan_step}")
    amendment = f"- {timestamp} - `aegis log` updated `{plan_step}` to `{plan_status}` with evidence `{evidence_rel}`."
    if amendment not in lines:
        try:
            heading_index = next(index for index, value in enumerate(lines) if value.strip() == "## Amendments & Versioning")
        except StopIteration:
            lines.extend(["", "## Amendments & Versioning", amendment])
        else:
            insert_at = len(lines)
            for index in range(heading_index + 1, len(lines)):
                stripped = lines[index].strip()
                if stripped.startswith("#") and stripped != "## Amendments & Versioning":
                    insert_at = index
                    break
            while insert_at > heading_index + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            lines.insert(insert_at, amendment)
    plan_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def _pending_tracking_events(target_root: Path) -> list[dict[str, Any]]:
    payload = _read_json(target_root / AEGIS_PENDING_TRACKING_REL)
    if not payload:
        return []
    events = payload.get("events")
    return [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []


def _write_pending_tracking_events(target_root: Path, events: list[dict[str, Any]]) -> None:
    path = target_root / AEGIS_PENDING_TRACKING_REL
    if not events:
        if path.exists():
            path.unlink()
        return
    _write_text(
        target_root,
        AEGIS_PENDING_TRACKING_REL,
        _dump_json(
            {
                "schema_version": SCHEMA_VERSION,
                "updated_at": _iso_now(),
                "events": events,
            }
        ),
    )


def _format_pending_tracking_for_error(events: Sequence[Mapping[str, Any]]) -> str:
    lines = []
    for event in events:
        lines.append(
            f"- {event.get('id', 'unknown')}: "
            f"H={event.get('handler', 'unknown')} "
            f"E={event.get('evidence', 'unknown')}"
        )
    return "\n".join(lines)


def log_work(
    target_dir: str | Path,
    *,
    handler: str,
    evidence: str,
    note: str,
    surfaces: Sequence[str] | None = None,
    plan_step: str | None = "plan-step-implement",
    plan_status: str | None = "in-progress",
) -> dict[str, Any]:
    """Append S:W:H:E progress entries, update workflow surfaces, and clear pending tracking."""

    target_root = _resolve_target_root(target_dir)
    current_work = _current_work_payload(target_root)
    task = current_work.get("task") if isinstance(current_work.get("task"), dict) else {}
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), dict) else {}
    task_id = str(task.get("id") or "").strip()
    slug = str(task.get("slug") or "").strip()
    if not task_id or not slug:
        raise AegisError("current work task id and slug are required before logging")
    clean_handler = handler.strip()
    clean_note = note.strip()
    if not clean_handler:
        raise AegisError("handler is required")
    if not clean_note:
        raise AegisError("note is required")

    session_rel = str(paths.get("session") or "")
    plan_rel = str(paths.get("plan") or "")
    work_rel = str(paths.get("work_tracking") or "")
    if not session_rel or not plan_rel or not work_rel:
        raise AegisError("current work paths are incomplete; rerun aegis kickoff")
    session_path = target_root / session_rel
    plan_path = target_root / plan_rel
    tracker_path = target_root / work_rel / "TRACKER.md"
    evidence_rel = _normalize_evidence(target_root, evidence)
    log_surfaces = _normalize_log_surfaces(surfaces)
    normalized_plan_step = plan_step.strip() if plan_step else ""
    normalized_plan_status = _normalize_plan_status(plan_status) if normalized_plan_step else ""

    now = datetime.now().astimezone().replace(microsecond=0)
    session_value = now.strftime("%Y%m%d")
    date_value = now.strftime("%Y-%m-%d")
    work_context = f"task{task_id}-{slug}"
    swhe = f"[S:{session_value}|W:{work_context}|H:{clean_handler}|E:{evidence_rel}]"
    session_line = f"- **[{now.strftime('%H:%M')}]** - {swhe} {clean_note}"
    tracker_line = f"- **{now.strftime('%Y-%m-%d %H:%M %Z').strip()}** - {swhe} {clean_note}"

    pending_before = _pending_tracking_events(target_root)
    cleared = [
        event
        for event in pending_before
        if str(event.get("evidence") or "") == evidence_rel
    ]
    if pending_before and not cleared:
        pending_summary = _format_pending_tracking_for_error(pending_before)
        raise AegisError(
            "aegis log evidence does not match any pending S:W:H:E tracking event. "
            "Log the pending evidence first or inspect .aegis/state/pending-tracking.json.\n"
            f"Pending tracking:\n{pending_summary}"
        )

    _append_progress_entry(session_path, "### Progress Log", session_line)
    _append_progress_entry(tracker_path, "## Progress Log", tracker_line)
    _update_tracker_timestamp(tracker_path, date_value)

    updated_surfaces: dict[str, str] = {}
    for surface in log_surfaces:
        rel_path = f"{work_rel}/{AEGIS_LOG_SURFACES[surface]}"
        _append_progress_entry(target_root / rel_path, "## Progress Log", tracker_line)
        updated_surfaces[surface] = rel_path

    plan_updated = False
    if normalized_plan_step:
        plan_updated = _update_plan_table(
            plan_path,
            plan_step=normalized_plan_step,
            plan_status=normalized_plan_status,
            evidence_rel=evidence_rel,
            timestamp=date_value,
        )
        _update_tracker_plan_step(tracker_path, normalized_plan_step, normalized_plan_status)

    remaining = [
        event
        for event in pending_before
        if str(event.get("evidence") or "") != evidence_rel
    ]
    _write_pending_tracking_events(target_root, remaining)

    current_work["updated_at"] = _iso_now()
    _write_text(target_root, AEGIS_CURRENT_WORK_REL, _dump_json(current_work))

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "logged",
        "logged_at": _iso_now(),
        "target_root": str(target_root),
        "entry": {
            "session": session_line,
            "tracker": tracker_line,
            "s": session_value,
            "w": work_context,
            "h": clean_handler,
            "e": evidence_rel,
            "note": clean_note,
        },
        "paths": {
            "session": session_rel,
            "plan": plan_rel,
            "tracker": f"{work_rel}/TRACKER.md",
            "surfaces": updated_surfaces,
            "pending_tracking": AEGIS_PENDING_TRACKING_REL,
        },
        "plan": {
            "updated": plan_updated,
            "step": normalized_plan_step or None,
            "status": normalized_plan_status or None,
            "evidence": evidence_rel,
        },
        "pending": {
            "cleared": len(cleared),
            "remaining": len(remaining),
            "cleared_events": cleared,
        },
    }


def install(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    profile: str = PROFILE_GENERIC,
    primary_agent: str,
    agents: Sequence[str] | None,
    apply: bool,
) -> dict[str, Any]:
    if not apply:
        return plan_install(
            target_dir,
            source_root=source_root,
            profile=profile,
            primary_agent=primary_agent,
            agents=agents,
            mode="dry_run",
            apply_confirmed=False,
        )
    target_root = _resolve_target_root(target_dir)
    target_root.mkdir(parents=True, exist_ok=True)
    enabled_agents = _enabled_agents(primary_agent, agents)
    source = Path(source_root).resolve()
    plan = plan_install(
        target_root,
        source_root=source,
        profile=profile,
        primary_agent=primary_agent,
        agents=enabled_agents,
        mode="apply",
        apply_confirmed=True,
    )
    unsafe = _unsafe_operations(plan)
    if unsafe:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "refused",
            "reason": "Unsafe overwrite or manual-review operation present.",
            "plan": plan,
            "unsafe_operations": list(unsafe),
        }

    installed_at = _installed_at_for_plan(target_root)
    assets = _managed_assets(source, primary_agent, enabled_agents)
    manifest = _manifest_payload(source, target_root, primary_agent, enabled_agents, installed_at=installed_at)
    manifest_asset = Asset(AEGIS_MANIFEST_REL, _dump_json(manifest).encode("utf-8"))
    created_plan_paths = [
        str(operation["path"])
        for operation in plan.get("operations", [])
        if operation.get("classification") == "create" and isinstance(operation.get("path"), str)
    ]
    runtime_report_paths = [
        rel_path
        for rel_path in (AEGIS_PLAN_REPORT_REL, AEGIS_INSTALL_REPORT_REL)
        if not (target_root / rel_path).exists()
    ]
    try:
        for asset in [*assets, manifest_asset]:
            target = target_root / asset.path
            if target.exists() and target.is_file() and target.read_bytes() == asset.content:
                continue
            _write_asset(target_root, asset)

        reports_dir = target_root / AEGIS_REPORTS_REL
        reports_dir.mkdir(parents=True, exist_ok=True)
        (target_root / AEGIS_PLAN_REPORT_REL).write_text(_dump_json(plan), encoding="utf-8")
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": "applied",
            "applied_at": _iso_now(),
            "target_root": str(target_root),
            "plan": plan,
            "manifest_path": AEGIS_MANIFEST_REL,
        }
        (target_root / AEGIS_INSTALL_REPORT_REL).write_text(_dump_json(report), encoding="utf-8")
        return report
    except Exception as exc:
        cleanup = _cleanup_created_paths(target_root, [*created_plan_paths, *runtime_report_paths])
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "failed",
            "reason": str(exc),
            "failed_at": _iso_now(),
            "target_root": str(target_root),
            "plan": plan,
            "cleanup": cleanup,
        }


def _check_settings_hook(target_root: Path, gate: Mapping[str, Any]) -> tuple[bool, str]:
    settings_path = target_root / str(gate.get("settings_path") or "")
    if not settings_path.exists():
        return False, f"settings file missing: {_repo_path(settings_path, target_root)}"
    settings = _read_json(settings_path)
    if not settings:
        return False, f"settings file is not valid JSON: {_repo_path(settings_path, target_root)}"
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False, "settings hooks object missing"
    event = str(gate.get("hook_event") or "")
    matcher = str(gate.get("hook_matcher") or "")
    expected = str(gate.get("verification", {}).get("expected") or "")
    entries = hooks.get(event)
    if not isinstance(entries, list):
        return False, f"settings hook event missing: {event}"
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if matcher and entry.get("matcher") != matcher:
            continue
        hook_items = entry.get("hooks")
        if not isinstance(hook_items, list):
            continue
        for hook in hook_items:
            if isinstance(hook, dict) and hook.get("command") == expected:
                return True, "hook registered"
    label = f"{event} / {matcher}" if matcher else event
    return False, f"hook registration missing for {label}"


def _verify_gate(target_root: Path, gate: Mapping[str, Any]) -> dict[str, Any]:
    verification = gate.get("verification") if isinstance(gate.get("verification"), Mapping) else {}
    method = verification.get("method")
    gate_id = str(gate.get("id"))
    path_value = gate.get("path")
    result: dict[str, Any] = {
        "gate_id": gate_id,
        "required": bool(gate.get("required")),
        "enforcement": gate.get("enforcement"),
        "method": method,
        "status": "pass",
        "message": "ok",
    }
    if method == "manual":
        result["status"] = "unsupported" if gate.get("enforcement") == "policy" else "warn"
        result["message"] = str(gate.get("unsupported_reason") or "manual verification required")
        return result
    if method in {"exists", "executable"}:
        target = target_root / str(path_value or "")
        if not target.exists():
            result["status"] = "fail"
            result["message"] = f"path missing: {_repo_path(target, target_root)}"
        elif method == "executable" and not os.access(target, os.X_OK):
            result["status"] = "fail"
            result["message"] = f"path not executable: {_repo_path(target, target_root)}"
        return result
    if method == "settings_hook":
        ok, message = _check_settings_hook(target_root, gate)
        result["status"] = "pass" if ok else "fail"
        result["message"] = message
        return result
    if method == "command":
        command = str(gate.get("command") or "")
        result["status"] = "warn"
        result["message"] = f"command gate not executed by V1 verifier: {command}"
        return result
    result["status"] = "warn"
    result["message"] = f"unsupported verification method: {method}"
    return result


def verify(target_dir: str | Path, *, source_root: str | Path) -> dict[str, Any]:
    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest = _read_json(manifest_path)
    checks: list[dict[str, Any]] = []
    if manifest is None:
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": "failed",
            "verified_at": _iso_now(),
            "target_root": str(target_root),
            "manifest_path": AEGIS_MANIFEST_REL,
            "checks": [
                {
                    "gate_id": "aegis.manifest",
                    "required": True,
                    "status": "fail",
                    "message": "Aegis manifest missing or invalid JSON.",
                }
            ],
        }
        _write_verify_report(target_root, report)
        return report

    try:
        _validate_with_schema(source, "foundation-manifest.schema.json", manifest)
        checks.append(
            {
                "gate_id": "aegis.manifest_schema",
                "required": True,
                "status": "pass",
                "message": "manifest schema valid",
            }
        )
    except ValidationError as exc:
        checks.append(
            {
                "gate_id": "aegis.manifest_schema",
                "required": True,
                "status": "fail",
                "message": exc.message,
            }
        )

    for gate in manifest.get("gates", []) if isinstance(manifest.get("gates"), list) else []:
        if isinstance(gate, Mapping):
            checks.append(_verify_gate(target_root, gate))

    failed_required = [check for check in checks if check.get("required") and check.get("status") == "fail"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "failed" if failed_required else "passed",
        "verified_at": _iso_now(),
        "target_root": str(target_root),
        "manifest_path": AEGIS_MANIFEST_REL,
        "summary": {
            "total": len(checks),
            "failed_required": len(failed_required),
            "warnings": sum(1 for check in checks if check.get("status") == "warn"),
            "unsupported": sum(1 for check in checks if check.get("status") == "unsupported"),
        },
        "checks": checks,
    }
    _write_verify_report(target_root, report)
    if report["status"] == "passed":
        manifest["verification"] = {
            "status": "passed",
            "last_verified_at": report["verified_at"],
            "reports": [AEGIS_VERIFY_REPORT_REL],
        }
        manifest_path.write_text(_dump_json(manifest), encoding="utf-8")
    return report


def _write_verify_report(target_root: Path, report: Mapping[str, Any]) -> None:
    reports_dir = target_root / AEGIS_REPORTS_REL
    reports_dir.mkdir(parents=True, exist_ok=True)
    (target_root / AEGIS_VERIFY_REPORT_REL).write_text(_dump_json(report), encoding="utf-8")


def list_profiles(*, source_root: str | Path) -> dict[str, Any]:
    source = Path(source_root).resolve()
    profile = profile_payload()
    _validate_with_schema(source, "profile.schema.json", profile)
    return {
        "schema_version": SCHEMA_VERSION,
        "profiles": [
            {
                "name": PROFILE_GENERIC,
                "default_primary_agent": "claude",
                "agent_selection_required": True,
                "supported_agents": ["claude", "codex"],
            }
        ],
    }


def explain_profile(profile: str, *, source_root: str | Path) -> dict[str, Any]:
    if profile != PROFILE_GENERIC:
        raise AegisError(f"Unsupported Aegis profile in V1: {profile}")
    payload = profile_payload()
    _validate_with_schema(Path(source_root).resolve(), "profile.schema.json", payload)
    return payload
