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
import hashlib
import tarfile
import tempfile
import zipfile
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
AEGIS_CLOSEOUT_REPORT_REL = ".aegis/reports/closeout-report.json"
AEGIS_KICKOFF_REPORT_REL = ".aegis/reports/kickoff-report.json"
AEGIS_RELEASE_CERT_REPORT_REL = "reports/aegis-release-certification/certification-report.json"
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
            "required_commands": ["aegis verify --strict", "aegis closeout"],
            "optional_smoke_tests": [
                "cold-session mutation blocked",
                "Aegis-native kickoff reaches READY without Taskmaster or Serena",
                "READY evidence write allowed",
                "aegis log updates session, tracker, implementation, changelog, handoff, and explicit plan surfaces",
                "aegis closeout blocks completion until strict verification, plan evidence, and semantic handoff pass",
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
            "- Agents must not write `.aegis/` directly; use Aegis MCP tools or the project-local Aegis CLI.",
            "- Aegis MCP/CLI is the workflow control plane. Use native agent tools for normal source edits, test runs, and git inspection.",
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
            "## Control Plane vs Implementation Tools",
            "",
            "- Use Aegis MCP tools, or the project-local Aegis CLI, for Aegis workflow state: inspect, plan-install, install, kickoff, log, verify, closeout, status, and future reconciliation.",
            "- Use native agent tools for normal project implementation: reading files, editing source files, running project tests, and inspecting git status or diffs.",
            "- The installed Aegis runtime, not the MCP session, is responsible for enforcement.",
            "- Installed hooks govern persistent mutations regardless of whether the attempted mutation comes from MCP, Bash, Edit, Write, or another supported tool surface.",
            "- MCP is the bootstrap and control-plane interface. It is not a replacement for the agent's editor, shell, test runner, or normal implementation workflow.",
            "",
            "## Verification",
            "",
            "- Required gates must pass `aegis verify --strict` before work is declared complete.",
            "- `aegis closeout` is the final completion gate. Do not report task completion until it writes a passing closeout report.",
            "- Missing, non-executable, unconfigured, or failing required gates make verification fail.",
            "- Policy-only gates are documented limitations, not proof of enforcement.",
            "",
            "## Work Kickoff",
            "",
            "- Start work with `aegis kickoff --task <id> --slug <slug> --title \"<title>\"` or `./.aegis/bin/aegis kickoff ...` when the global command is unavailable.",
            "- Kickoff creates Aegis-native current work state, session, plan, and work-tracking files.",
            "- `.aegis/state/current-work.json` is the portable authority for READY.",
            "- Taskmaster is validated only when no Aegis current-work state exists or when current work explicitly marks Taskmaster required.",
            "- Normal feature work is: confirm readiness, mark `plan-step-scope` complete with `aegis log`, make the task-scoped code change, let PostToolUse create pending tracking, run `aegis log` for the changed source file with `--plan-step plan-step-implement`, run task-specific verification with `--plan-step plan-step-verify`, run `aegis verify --strict`, log the strict verification report with `--plan-step plan-step-verify`, then run `aegis closeout` before declaring the work complete.",
            "- After every meaningful mutation, run `aegis log --handler <handler> --evidence <path> --note \"<past-tense note>\"` to write S:W:H:E entries to the active session, tracker, implementation log, changelog, and handoff.",
            "- `aegis log` updates plan state only when `--plan-step` is supplied. This prevents generic evidence logs from accidentally changing an unrelated plan step.",
            "- The next persistent mutation is blocked until pending S:W:H:E tracking is logged; this is what makes the workflow mechanical rather than advisory.",
            "- Use `--surface findings` or `--surface decisions` when the mutation also records a finding or decision. Use `--plan-step` and `--plan-status` for explicit scope/implement/verify transitions.",
            "- `aegis closeout --update-handoff` may refresh Aegis-owned semantic handoff sections before validation. It preserves the Progress Log.",
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
            "",
            "Tool routing:",
            "",
            "- Use Aegis MCP tools for Aegis workflow state when they are available: inspect, plan_install, install, kickoff, log, verify, closeout, status, and future reconciliation.",
            "- Use `aegis ...` or `./.aegis/bin/aegis ...` for the same workflow operations when MCP is unavailable.",
            "- Use native Claude tools for normal implementation work: reading files, editing source, running tests, and inspecting git status or diffs.",
            "- Do not use MCP as a replacement for normal source editing. The installed hooks enforce the workflow around native tool use.",
            "",
            "Normal feature-work loop:",
            "",
            "1. Confirm readiness is READY.",
            "2. Record scope with `aegis log --handler claude:scope --evidence <scope-doc-or-file> --note \"Confirmed task scope\" --surface findings --surface decisions --plan-step plan-step-scope --plan-status completed`.",
            "3. Make the task-scoped source change requested by the user with native Edit/Write tools.",
            "4. After the hook records pending tracking, run `aegis log --handler <handler> --evidence <changed-file> --note \"<past-tense note>\" --plan-step plan-step-implement --plan-status completed`.",
            "5. Run task-specific verification and log it with `--plan-step plan-step-verify --plan-status completed`.",
            "6. Run `aegis verify --strict` or `./.aegis/bin/aegis verify --strict`, then log `.aegis/reports/verification-report.json` with `aegis log --handler aegis:verify --evidence .aegis/reports/verification-report.json --note \"Recorded strict verification evidence\" --plan-step plan-step-verify --plan-status completed`.",
            "7. Run `aegis closeout --update-handoff` or `./.aegis/bin/aegis closeout --update-handoff`; do not report the task complete until closeout passes.",
            "",
            "After any mutation, use `aegis log --handler <handler> --evidence <path> --note \"<past-tense note>\"` before attempting the next mutation. The command updates the session, tracker, implementation log, changelog, and handoff. It updates plan evidence only when `--plan-step` is supplied.",
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
                "Bash(aegis closeout:*)",
                "Bash(./.aegis/bin/aegis inspect:*)",
                "Bash(./.aegis/bin/aegis status:*)",
                "Bash(./.aegis/bin/aegis kickoff:*)",
                "Bash(./.aegis/bin/aegis log:*)",
                "Bash(./.aegis/bin/aegis verify:*)",
                "Bash(./.aegis/bin/aegis closeout:*)",
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
            "  for AEGIS_PYTHONPATH_CANDIDATE in \"$AEGIS_SOURCE_FALLBACK\" \"$AEGIS_SOURCE_FALLBACK/..\" \"$AEGIS_SOURCE_FALLBACK/../..\"; do",
            "    if PYTHONPATH=\"$AEGIS_PYTHONPATH_CANDIDATE${PYTHONPATH:+:$PYTHONPATH}\" python3 -c 'import aegis_foundation.cli' >/dev/null 2>&1; then",
            "      export PYTHONPATH=\"$AEGIS_PYTHONPATH_CANDIDATE${PYTHONPATH:+:$PYTHONPATH}\"",
            "      exec python3 -m aegis_foundation.cli --source-root \"$AEGIS_SOURCE_FALLBACK\" \"$@\"",
            "    fi",
            "  done",
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
    clean = evidence.strip()
    return clean[2:] if clean.startswith("./") else clean


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
    plan_step: str | None = None,
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


def _strict_check(
    check_id: str,
    *,
    category: str,
    required: bool,
    passed: bool,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "gate_id": check_id,
        "id": check_id,
        "category": category,
        "required": required,
        "enforcement": "strict",
        "method": "strict",
        "status": "pass" if passed else "fail",
        "message": message,
    }
    if details is not None:
        result["details"] = dict(details)
    return result


def _strict_path_check(
    target_root: Path,
    check_id: str,
    *,
    category: str,
    rel_path: str,
    required: bool = True,
    directory: bool = False,
    executable: bool = False,
) -> dict[str, Any]:
    target = target_root / rel_path
    exists = target.exists()
    kind_ok = target.is_dir() if directory else target.is_file()
    executable_ok = not executable or os.access(target, os.X_OK)
    passed = exists and kind_ok and executable_ok
    if not exists:
        message = f"path missing: {rel_path}"
    elif not kind_ok:
        expected = "directory" if directory else "file"
        message = f"path is not a {expected}: {rel_path}"
    elif not executable_ok:
        message = f"path not executable: {rel_path}"
    else:
        message = "ok"
    return _strict_check(
        check_id,
        category=category,
        required=required,
        passed=passed,
        message=message,
        details={
            "path": rel_path,
            "directory": directory,
            "executable": executable,
        },
    )


def _agent_enabled(manifest: Mapping[str, Any], agent: str) -> bool:
    agents = manifest.get("agents")
    if not isinstance(agents, Mapping):
        return False
    agent_payload = agents.get(agent)
    return isinstance(agent_payload, Mapping) and agent_payload.get("enabled") is True


def _strict_managed_files_check(target_root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    managed_files = manifest.get("managed_files")
    if not isinstance(managed_files, list):
        return _strict_check(
            "manifest.managed_files",
            category="manifest",
            required=True,
            passed=False,
            message="managed_files is missing or not a list",
        )
    missing: list[str] = []
    directories: list[str] = []
    checked: list[str] = []
    for item in managed_files:
        if not isinstance(item, Mapping):
            continue
        rel_path = str(item.get("path") or "").strip()
        if not rel_path:
            continue
        checked.append(rel_path)
        target = target_root / rel_path
        if not target.exists():
            missing.append(rel_path)
        elif target.is_dir():
            directories.append(rel_path)
    passed = not missing and not directories
    message = "all manifest managed files exist" if passed else "manifest managed files missing or invalid"
    return _strict_check(
        "manifest.managed_files",
        category="manifest",
        required=True,
        passed=passed,
        message=message,
        details={
            "checked": len(checked),
            "missing": missing,
            "directories": directories,
        },
    )


def _strict_workflow_template_check(target_root: Path) -> dict[str, Any]:
    missing = [
        template_name
        for template_name in AEGIS_WORKFLOW_TEMPLATE_NAMES
        if not (target_root / AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT / template_name).is_file()
    ]
    return _strict_check(
        "runtime.workflow_templates",
        category="runtime",
        required=True,
        passed=not missing,
        message="all workflow templates installed" if not missing else "workflow templates missing",
        details={
            "template_root": AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT,
            "missing": missing,
        },
    )


def _strict_current_work_checks(target_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    current_work_path = target_root / AEGIS_CURRENT_WORK_REL
    current_work = _read_json(current_work_path)
    if current_work is None:
        return [
            _strict_check(
                "workflow.current_work",
                category="workflow",
                required=True,
                passed=False,
                message=f"{AEGIS_CURRENT_WORK_REL} missing or invalid JSON",
            )
        ], None

    task = current_work.get("task") if isinstance(current_work.get("task"), Mapping) else {}
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    task_id = str(task.get("id") or "").strip()
    task_slug = str(task.get("slug") or "").strip()
    missing_path_keys = [
        key
        for key in (
            "session",
            "session_current",
            "plan",
            "plan_current",
            "work_tracking",
            "reports",
            "workflow_templates",
        )
        if not str(paths.get(key) or "").strip()
    ]
    valid_payload = (
        current_work.get("status") == "in-progress"
        and bool(task_id)
        and bool(task_slug)
        and not missing_path_keys
    )
    checks = [
        _strict_check(
            "workflow.current_work",
            category="workflow",
            required=True,
            passed=valid_payload,
            message="current work payload is active and complete" if valid_payload else "current work payload is incomplete",
            details={
                "task": task,
                "missing_path_keys": missing_path_keys,
            },
        )
    ]

    if task_id:
        try:
            branch = _current_branch(target_root)
            branch_task = _branch_task_id(branch)
            branch_matches = branch_task == task_id
            checks.append(
                _strict_check(
                    "workflow.branch_task_alignment",
                    category="workflow",
                    required=True,
                    passed=branch_matches,
                    message="branch task id matches current work" if branch_matches else "branch task id does not match current work",
                    details={
                        "branch": branch,
                        "branch_task_id": branch_task,
                        "current_work_task_id": task_id,
                    },
                )
            )
        except AegisError as exc:
            checks.append(
                _strict_check(
                    "workflow.branch_task_alignment",
                    category="workflow",
                    required=True,
                    passed=False,
                    message=str(exc),
                )
            )

    for key, check_id, directory in (
        ("session", "workflow.session_file", False),
        ("session_current", "workflow.session_current", False),
        ("plan", "workflow.plan_file", False),
        ("plan_current", "workflow.plan_current", False),
        ("work_tracking", "workflow.work_tracking", True),
        ("reports", "workflow.reports", True),
        ("workflow_templates", "workflow.workflow_templates_path", True),
    ):
        rel_path = str(paths.get(key) or "").strip()
        if rel_path:
            checks.append(
                _strict_path_check(
                    target_root,
                    check_id,
                    category="workflow",
                    rel_path=rel_path,
                    directory=directory,
                )
            )

    work_rel = str(paths.get("work_tracking") or "").strip()
    if work_rel:
        missing_surfaces = [
            name
            for name in (
                "TRACKER.md",
                "FINDINGS.md",
                "DECISIONS.md",
                "IMPLEMENTATION.md",
                "CHANGELOG.md",
                "HANDOFF.md",
            )
            if not (target_root / work_rel / name).is_file()
        ]
        checks.append(
            _strict_check(
                "workflow.tracking_surfaces",
                category="workflow",
                required=True,
                passed=not missing_surfaces,
                message="all work-tracking surfaces exist" if not missing_surfaces else "work-tracking surfaces missing",
                details={
                    "work_tracking": work_rel,
                    "missing": missing_surfaces,
                },
            )
        )
    return checks, current_work


def _strict_pending_tracking_check(target_root: Path) -> dict[str, Any]:
    pending_path = target_root / AEGIS_PENDING_TRACKING_REL
    if not pending_path.exists():
        return _strict_check(
            "mutation.pending_tracking_empty",
            category="mutation",
            required=True,
            passed=True,
            message="pending tracking queue absent",
            details={"path": AEGIS_PENDING_TRACKING_REL, "events": 0},
        )
    payload = _read_json(pending_path)
    if payload is None:
        return _strict_check(
            "mutation.pending_tracking_empty",
            category="mutation",
            required=True,
            passed=False,
            message="pending tracking queue is invalid JSON",
            details={"path": AEGIS_PENDING_TRACKING_REL},
        )
    events = payload.get("events")
    event_count = len(events) if isinstance(events, list) else 0
    return _strict_check(
        "mutation.pending_tracking_empty",
        category="mutation",
        required=True,
        passed=event_count == 0,
        message="pending tracking queue empty" if event_count == 0 else "pending tracking queue has unlogged mutation events",
        details={"path": AEGIS_PENDING_TRACKING_REL, "events": event_count},
    )


def _strict_claude_checks(target_root: Path, manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    required = _agent_enabled(manifest, "claude")
    if not required:
        return [
            _strict_check(
                "claude.adapter_enabled",
                category="claude",
                required=False,
                passed=True,
                message="Claude adapter is not enabled for this install",
            )
        ]

    missing_required_files = [
        rel_path
        for rel_path in CLAUDE_REQUIRED_FILES
        if not (target_root / rel_path).is_file()
    ]
    checks = [
        _strict_check(
            "claude.required_files",
            category="claude",
            required=True,
            passed=not missing_required_files,
            message="all Claude required files exist" if not missing_required_files else "Claude required files missing",
            details={"missing": missing_required_files},
        )
    ]

    hook_gate_ids = {
        "claude.pretooluse",
        "claude.posttooluse_tracking",
        "claude.stop_tracking",
    }
    hook_results = [
        _verify_gate(target_root, gate)
        for gate in manifest.get("gates", [])
        if isinstance(gate, Mapping) and gate.get("id") in hook_gate_ids
    ]
    failed_hooks = [
        str(result.get("gate_id"))
        for result in hook_results
        if result.get("status") != "pass"
    ]
    checks.append(
        _strict_check(
            "claude.hooks_registered",
            category="claude",
            required=True,
            passed=len(hook_results) == len(hook_gate_ids) and not failed_hooks,
            message="Claude hook registrations are present" if not failed_hooks and len(hook_results) == len(hook_gate_ids) else "Claude hook registrations are missing or invalid",
            details={
                "expected": sorted(hook_gate_ids),
                "observed": [str(result.get("gate_id")) for result in hook_results],
                "failed": failed_hooks,
            },
        )
    )
    checks.append(
        _strict_check(
            "protection.codex_owned_paths",
            category="protection",
            required=True,
            passed=(target_root / ".claude/scripts/codex-path-guard.sh").is_file()
            and os.access(target_root / ".claude/scripts/codex-path-guard.sh", os.X_OK)
            and (target_root / ".claude/scripts/bash-command-guard.sh").is_file()
            and os.access(target_root / ".claude/scripts/bash-command-guard.sh", os.X_OK),
            message="Codex-owned path guard scripts are installed and executable",
            details={
                "file_tool_guard": ".claude/scripts/codex-path-guard.sh",
                "bash_guard": ".claude/scripts/bash-command-guard.sh",
            },
        )
    )
    return checks


def _strict_integration_checks(target_root: Path, current_work: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    integrations = current_work.get("integrations") if isinstance(current_work, Mapping) and isinstance(current_work.get("integrations"), Mapping) else {}
    checks: list[dict[str, Any]] = []
    for name, rel_path in (("taskmaster", ".taskmaster"), ("serena", ".serena")):
        integration = integrations.get(name) if isinstance(integrations, Mapping) else {}
        required = isinstance(integration, Mapping) and integration.get("required") is True
        detected = (target_root / rel_path).exists()
        checks.append(
            _strict_check(
                f"integrations.{name}_optional",
                category="integrations",
                required=required,
                passed=(detected or not required),
                message=(
                    f"{name} integration present"
                    if detected
                    else f"{name} integration is optional and absent"
                    if not required
                    else f"{name} integration is required but absent"
                ),
                details={
                    "path": rel_path,
                    "required": required,
                    "detected": detected,
                },
            )
        )
    return checks


def _strict_verification_checks(target_root: Path, manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = [
        _strict_managed_files_check(target_root, manifest),
        _strict_path_check(
            target_root,
            "runtime.local_cli_shim",
            category="runtime",
            rel_path=AEGIS_LOCAL_BIN_REL,
            executable=True,
        ),
        _strict_workflow_template_check(target_root),
    ]
    workflow_checks, current_work = _strict_current_work_checks(target_root)
    checks.extend(workflow_checks)
    checks.append(_strict_pending_tracking_check(target_root))
    checks.extend(_strict_claude_checks(target_root, manifest))
    checks.extend(_strict_integration_checks(target_root, current_work))
    return checks


def verify(target_dir: str | Path, *, source_root: str | Path, strict: bool = False) -> dict[str, Any]:
    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest = _read_json(manifest_path)
    mode = "strict" if strict else "standard"
    checks: list[dict[str, Any]] = []
    if manifest is None:
        report = {
            "schema_version": SCHEMA_VERSION,
            "mode": mode,
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
            "summary": {
                "total": 1,
                "failed_required": 1,
                "warnings": 0,
                "unsupported": 0,
            },
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

    if strict:
        checks.extend(_strict_verification_checks(target_root, manifest))

    failed_required = [check for check in checks if check.get("required") and check.get("status") == "fail"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
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


def _closeout_check(
    check_id: str,
    *,
    passed: bool,
    message: str,
    category: str = "closeout",
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _strict_check(
        check_id,
        category=category,
        required=True,
        passed=passed,
        message=message,
        details=details,
    )


def _read_text_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _parse_plan_rows(plan_path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for index, line in enumerate(_read_text_or_empty(plan_path).splitlines()):
        if not line.startswith("| plan-step-"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) != 4:
            rows[columns[0] if columns else f"malformed-{index}"] = {
                "id": columns[0] if columns else "",
                "description": "",
                "evidence": "",
                "status": "malformed",
                "index": index,
                "malformed": True,
            }
            continue
        rows[columns[0]] = {
            "id": columns[0],
            "description": columns[1],
            "evidence": columns[2],
            "status": columns[3].lower(),
            "index": index,
            "malformed": False,
        }
    return rows


def _parse_tracker_plan_steps(tracker_path: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    pattern = re.compile(r"^-\s+\[(?P<mark>[ xX])\]\s+`?(?P<step>plan-step-[A-Za-z0-9_-]+)`?")
    for line in _read_text_or_empty(tracker_path).splitlines():
        match = pattern.match(line.strip())
        if match:
            statuses[match.group("step")] = "completed" if match.group("mark").lower() == "x" else "pending"
    return statuses


def _split_evidence_tokens(raw_evidence: str) -> list[str]:
    tokens: list[str] = []
    for token in raw_evidence.split(";"):
        clean = token.strip().strip("`")
        if clean and clean != "_TBD_":
            tokens.append(clean)
    return tokens


def _is_closeout_required_evidence(token: str) -> bool:
    if token == "changed files":
        return False
    if token.endswith("/"):
        return False
    if Path(token).name in {
        "TRACKER.md",
        "FINDINGS.md",
        "DECISIONS.md",
        "IMPLEMENTATION.md",
        "CHANGELOG.md",
        "HANDOFF.md",
    }:
        return False
    return True


def _markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## ") and lines[index].strip() != heading:
            end = index
            break
    return "\n".join(lines[start + 1 : end]).strip()


def _markdown_before_heading(text: str, heading: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == heading:
            return "\n".join(lines[:index]).strip()
    return text


def _replace_markdown_section(text: str, heading: str, body_lines: Sequence[str]) -> str:
    lines = text.splitlines()
    replacement = [heading, *body_lines]
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        insert_at = len(lines)
        while insert_at > 0 and not lines[insert_at - 1].strip():
            insert_at -= 1
        next_lines = lines[:insert_at] + ["", *replacement] + lines[insert_at:]
        return "\n".join(next_lines).rstrip() + "\n"

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## ") and lines[index].strip() != heading:
            end = index
            break
    next_lines = lines[:start] + replacement + lines[end:]
    return "\n".join(next_lines).rstrip() + "\n"


def _closeout_readiness(target_root: Path) -> dict[str, Any]:
    readiness_script = target_root / ".claude" / "scripts" / "readiness.sh"
    if readiness_script.is_file():
        result = subprocess.run(
            ["bash", str(readiness_script), "--quick", "--root", str(target_root)],
            cwd=target_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        passed = result.returncode == 0 and result.stdout.strip().startswith("READY")
        return {
            "status": "passed" if passed else "failed",
            "command": f"bash {readiness_script.relative_to(target_root).as_posix()} --quick --root {target_root}",
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    workflow_checks, _current_work = _strict_current_work_checks(target_root)
    failed = [check for check in workflow_checks if check.get("required") and check.get("status") == "fail"]
    return {
        "status": "passed" if not failed else "failed",
        "command": None,
        "returncode": 0 if not failed else 2,
        "stdout": "READY from strict current-work checks" if not failed else "BLOCKED by strict current-work checks",
        "stderr": "",
        "checks": workflow_checks,
    }


def _update_handoff_for_closeout(
    target_root: Path,
    *,
    handoff_path: Path,
    current_work: Mapping[str, Any],
    evidence_tokens: Sequence[str],
    strict_verify_rel: str,
) -> None:
    task = current_work.get("task") if isinstance(current_work.get("task"), Mapping) else {}
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    task_id = str(task.get("id") or "")
    slug = str(task.get("slug") or "")
    title = str(task.get("title") or f"Task {task_id}")
    branch = _current_branch(target_root)
    evidence_lines = [f"- `{token}`" for token in evidence_tokens]
    if not evidence_lines:
        evidence_lines = ["- No plan evidence tokens were available."]

    text = _read_text_or_empty(handoff_path)
    text = _replace_markdown_section(
        text,
        "## Current State",
        [
            f"- Task {task_id} `{slug}` is ready for closeout validation.",
            f"- Title: {title}.",
            f"- Branch: `{branch}`.",
            f"- Strict verification report: `{strict_verify_rel}`.",
            f"- Closeout report: `{AEGIS_CLOSEOUT_REPORT_REL}`.",
        ],
    )
    text = _replace_markdown_section(
        text,
        "## What Was Done",
        [
            "- Completed scope, implementation, and verification plan steps through Aegis logging.",
            "- Required evidence recorded:",
            *evidence_lines,
        ],
    )
    text = _replace_markdown_section(
        text,
        "## Current Issues/Blockers",
        [
            "- None known at closeout.",
        ],
    )
    text = _replace_markdown_section(
        text,
        "## Next Steps",
        [
            f"1. Review `{AEGIS_CLOSEOUT_REPORT_REL}`.",
            "2. Commit and open a pull request with normal git/GitHub commands when delegated.",
            "3. Archive or continue the active work-tracking folder according to the project lifecycle.",
        ],
    )
    text = _replace_markdown_section(
        text,
        "## Important Context",
        [
            f"- Current work authority remains `{AEGIS_CURRENT_WORK_REL}` with status `in-progress` until archive or lifecycle tooling changes it.",
            f"- Session: `{paths.get('session', 'unknown')}`.",
            f"- Plan: `{paths.get('plan', 'unknown')}`.",
            f"- Active work-tracking: `{paths.get('work_tracking', 'unknown')}`.",
            "- Taskmaster and Serena are optional unless current work marks them required.",
            "- Use normal git and GitHub commands by default. `gac` is legacy/manual only.",
        ],
    )
    handoff_path.write_text(text, encoding="utf-8")


def _closeout_handoff_checks(
    handoff_text: str,
    *,
    implementation_tokens: Sequence[str],
    verification_tokens: Sequence[str],
    strict_verify_rel: str,
) -> list[dict[str, Any]]:
    current_state = _markdown_section(handoff_text, "## Current State")
    next_steps = _markdown_section(handoff_text, "## Next Steps")
    semantic_text = _markdown_before_heading(handoff_text, "## Progress Log")
    kickoff_only_phrases = (
        "has been kicked off through Aegis",
        "Confirm scope before implementation",
        "Capture verification evidence",
        "_Pending_",
    )
    current_state_ok = bool(current_state.strip()) and not (
        "has been kicked off through Aegis" in current_state
        and "ready for closeout validation" not in current_state
    )
    next_steps_ok = bool(next_steps.strip()) and not any(phrase in next_steps for phrase in kickoff_only_phrases)

    checks = [
        _closeout_check(
            "closeout.handoff.current_state",
            passed=current_state_ok,
            message="handoff current state is semantic" if current_state_ok else "handoff current state is still placeholder/kickoff-oriented",
        ),
        _closeout_check(
            "closeout.handoff.next_steps",
            passed=next_steps_ok,
            message="handoff next steps are semantic" if next_steps_ok else "handoff next steps are still placeholder/kickoff-oriented",
        ),
    ]

    for check_id, tokens, label in (
        ("closeout.handoff.implementation_evidence", implementation_tokens, "implementation"),
        ("closeout.handoff.verification_evidence", verification_tokens, "verification"),
        ("closeout.handoff.strict_verify_evidence", [strict_verify_rel], "strict verification"),
    ):
        missing = [token for token in tokens if token not in semantic_text]
        checks.append(
            _closeout_check(
                check_id,
                passed=not missing,
                message=f"handoff semantic sections reference {label} evidence" if not missing else f"handoff semantic sections missing {label} evidence",
                details={"missing": missing},
            )
        )
    return checks


def _closeout_git_report(target_root: Path, *, require_clean_git: bool, include_guidance: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    status_result = _run_target_git(target_root, "status", "--short")
    status_short = status_result.stdout.strip().splitlines() if status_result.returncode == 0 else []
    if require_clean_git:
        checks.append(
            _closeout_check(
                "closeout.git.clean",
                passed=status_result.returncode == 0 and not status_short,
                message="git worktree is clean" if status_result.returncode == 0 and not status_short else "git worktree has uncommitted changes",
                category="git",
                details={"status_short": status_short, "stderr": status_result.stderr.strip()},
            )
        )
    guidance = []
    if include_guidance:
        guidance = [
            "git status --short",
            "git add <paths>",
            "git commit -m \"<type(scope): summary>\"",
            "git push",
            "gh pr create",
        ]
    return {
        "require_clean_git": require_clean_git,
        "status_available": status_result.returncode == 0,
        "status_short": status_short,
        "guidance": guidance,
        "legacy_manual_only": ["gac"],
    }, checks


def closeout(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    update_handoff: bool = False,
    require_clean_git: bool = False,
    include_git_guidance: bool = True,
) -> dict[str, Any]:
    """Validate that Aegis workflow state is complete enough to report task completion."""

    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    checked_at = _iso_now()
    checks: list[dict[str, Any]] = []

    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    current_work_ok = isinstance(current_work, dict) and current_work.get("status") == "in-progress"
    checks.append(
        _closeout_check(
            "closeout.current_work",
            passed=current_work_ok,
            message="current work payload is active" if current_work_ok else f"{AEGIS_CURRENT_WORK_REL} missing, invalid, or not in-progress",
            details={"path": AEGIS_CURRENT_WORK_REL},
        )
    )
    if not isinstance(current_work, dict):
        current_work = {}

    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    session_rel = str(paths.get("session") or "")
    plan_rel = str(paths.get("plan") or "")
    work_rel = str(paths.get("work_tracking") or "")
    session_path = target_root / session_rel if session_rel else target_root / "sessions" / "current"
    plan_path = target_root / plan_rel if plan_rel else target_root / "plans" / "current"
    work_path = target_root / work_rel if work_rel else target_root / "docs" / "ai" / "work-tracking" / "active"
    tracker_path = work_path / "TRACKER.md"
    implementation_path = work_path / "IMPLEMENTATION.md"
    changelog_path = work_path / "CHANGELOG.md"
    handoff_path = work_path / "HANDOFF.md"

    readiness = _closeout_readiness(target_root)
    checks.append(
        _closeout_check(
            "closeout.readiness",
            passed=readiness.get("status") == "passed",
            message="readiness is READY" if readiness.get("status") == "passed" else "readiness is not READY",
            details=readiness,
        )
    )

    pending_events = _pending_tracking_events(target_root)
    checks.append(
        _closeout_check(
            "closeout.pending_tracking",
            passed=not pending_events,
            message="pending tracking queue is empty" if not pending_events else "pending tracking queue has unlogged mutation events",
            details={"path": AEGIS_PENDING_TRACKING_REL, "events": pending_events},
        )
    )

    strict_verify = verify(target_root, source_root=source, strict=True)
    checks.append(
        _closeout_check(
            "closeout.strict_verify",
            passed=strict_verify.get("status") == "passed",
            message="strict verification passed" if strict_verify.get("status") == "passed" else "strict verification failed",
            details={
                "report": AEGIS_VERIFY_REPORT_REL,
                "summary": strict_verify.get("summary", {}),
            },
        )
    )

    plan_rows = _parse_plan_rows(plan_path)
    tracker_steps = _parse_tracker_plan_steps(tracker_path)
    required_steps = ("plan-step-scope", "plan-step-implement", "plan-step-verify")
    for step in required_steps:
        row = plan_rows.get(step)
        plan_completed = isinstance(row, Mapping) and row.get("status") in {"completed", "done"}
        checks.append(
            _closeout_check(
                f"closeout.plan.{step.removeprefix('plan-step-')}",
                passed=plan_completed,
                message=f"{step} completed in current plan" if plan_completed else f"{step} missing or not completed in current plan",
                category="plan",
                details={"row": row},
            )
        )
        tracker_completed = tracker_steps.get(step) == "completed"
        checks.append(
            _closeout_check(
                f"closeout.tracker.{step.removeprefix('plan-step-')}",
                passed=tracker_completed,
                message=f"{step} completed in tracker" if tracker_completed else f"{step} missing or unchecked in tracker",
                category="tracker",
                details={"tracker_status": tracker_steps.get(step)},
            )
        )

    ordered = all(step in plan_rows for step in required_steps) and [
        int(plan_rows[step]["index"])
        for step in required_steps
    ] == sorted(int(plan_rows[step]["index"]) for step in required_steps)
    checks.append(
        _closeout_check(
            "closeout.plan.order",
            passed=ordered,
            message="required plan steps are in scope -> implement -> verify order" if ordered else "required plan steps are missing or out of order",
            category="plan",
            details={"order": [step for step in plan_rows if step in required_steps]},
        )
    )

    implementation_tokens = [
        token
        for token in _split_evidence_tokens(str(plan_rows.get("plan-step-implement", {}).get("evidence") or ""))
        if _is_closeout_required_evidence(token)
    ]
    verification_tokens = [
        token
        for token in _split_evidence_tokens(str(plan_rows.get("plan-step-verify", {}).get("evidence") or ""))
        if _is_closeout_required_evidence(token)
    ]
    strict_verify_rel = _normalize_evidence(target_root, AEGIS_VERIFY_REPORT_REL)
    required_evidence = tuple(dict.fromkeys([*implementation_tokens, *verification_tokens, strict_verify_rel]))

    surface_texts = {
        "session": _read_text_or_empty(session_path),
        "tracker": _read_text_or_empty(tracker_path),
        "implementation": _read_text_or_empty(implementation_path),
        "changelog": _read_text_or_empty(changelog_path),
        "handoff": _read_text_or_empty(handoff_path),
        "plan": _read_text_or_empty(plan_path),
    }
    evidence_matrix = {
        token: {
            surface: token in text
            for surface, text in surface_texts.items()
        }
        for token in required_evidence
    }
    for surface, text in surface_texts.items():
        missing = [token for token in required_evidence if token not in text]
        checks.append(
            _closeout_check(
                f"closeout.evidence.{surface}",
                passed=not missing,
                message=f"{surface} references all required evidence" if not missing else f"{surface} is missing required evidence",
                category="evidence",
                details={"missing": missing},
            )
        )

    if update_handoff and handoff_path.is_file():
        _update_handoff_for_closeout(
            target_root,
            handoff_path=handoff_path,
            current_work=current_work,
            evidence_tokens=required_evidence,
            strict_verify_rel=strict_verify_rel,
        )
        surface_texts["handoff"] = _read_text_or_empty(handoff_path)
        evidence_matrix = {
            token: {
                surface: (token in surface_texts[surface])
                for surface in surface_texts
            }
            for token in required_evidence
        }
        checks = [
            check
            for check in checks
            if check.get("gate_id") != "closeout.evidence.handoff"
        ]
        missing = [token for token in required_evidence if token not in surface_texts["handoff"]]
        checks.append(
            _closeout_check(
                "closeout.evidence.handoff",
                passed=not missing,
                message="handoff references all required evidence" if not missing else "handoff is missing required evidence",
                category="evidence",
                details={"missing": missing, "updated": True},
            )
        )

    checks.extend(
        _closeout_handoff_checks(
            surface_texts["handoff"],
            implementation_tokens=implementation_tokens,
            verification_tokens=verification_tokens,
            strict_verify_rel=strict_verify_rel,
        )
    )

    integrations = current_work.get("integrations") if isinstance(current_work.get("integrations"), Mapping) else {}
    integration_report: dict[str, Any] = {}
    for name, rel_path in (("taskmaster", ".taskmaster"), ("serena", ".serena")):
        integration = integrations.get(name) if isinstance(integrations, Mapping) else {}
        required = isinstance(integration, Mapping) and integration.get("required") is True
        detected = (target_root / rel_path).exists()
        integration_report[name] = {
            "detected": detected,
            "required": required,
            "status": "present" if detected else "optional_absent" if not required else "required_missing",
        }

    git_report, git_checks = _closeout_git_report(
        target_root,
        require_clean_git=require_clean_git,
        include_guidance=include_git_guidance,
    )
    checks.extend(git_checks)

    failed_required = [check for check in checks if check.get("required") and check.get("status") == "fail"]
    status_value = "failed" if failed_required else "passed"
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status_value,
        "checked_at": checked_at,
        "target_root": str(target_root),
        "current_work": current_work,
        "readiness": readiness,
        "strict_verify": {
            "status": strict_verify.get("status"),
            "report": AEGIS_VERIFY_REPORT_REL,
            "summary": strict_verify.get("summary", {}),
        },
        "plan": {
            "path": _repo_path(plan_path, target_root),
            "required_steps": {step: plan_rows.get(step) for step in required_steps},
            "tracker_steps": {step: tracker_steps.get(step) for step in required_steps},
        },
        "pending_tracking": {
            "path": AEGIS_PENDING_TRACKING_REL,
            "events": pending_events,
        },
        "evidence_matrix": evidence_matrix,
        "handoff": {
            "path": _repo_path(handoff_path, target_root),
            "updated": update_handoff,
        },
        "integrations": integration_report,
        "git": git_report,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "failed_required": len(failed_required),
            "warnings": 0,
        },
    }
    if status_value == "passed":
        report["closed_at"] = _iso_now()

    reports_dir = target_root / AEGIS_REPORTS_REL
    reports_dir.mkdir(parents=True, exist_ok=True)
    (target_root / AEGIS_CLOSEOUT_REPORT_REL).write_text(_dump_json(report), encoding="utf-8")

    if status_value == "passed" and current_work:
        current_work["updated_at"] = _iso_now()
        current_work["closeout_passed_at"] = report["closed_at"]
        current_work["closeout_report"] = AEGIS_CLOSEOUT_REPORT_REL
        _write_text(target_root, AEGIS_CURRENT_WORK_REL, _dump_json(current_work))

    return report


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_cert_command(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    input_text: str | None = None,
    expected_returncodes: Sequence[int] = (0,),
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    output = result.stdout + result.stderr
    payload = {
        "command": list(command),
        "cwd": cwd.as_posix(),
        "returncode": result.returncode,
        "status": "passed" if result.returncode in expected_returncodes else "failed",
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "output_tail": output[-4000:],
        "expected_returncodes": list(expected_returncodes),
    }
    return result, payload


def _git_provenance(source_root: Path) -> dict[str, Any]:
    def run_git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", source_root.as_posix(), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    commit = run_git("rev-parse", "HEAD")
    status = run_git("status", "--short")
    branch = run_git("branch", "--show-current")
    return {
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        "status_short": status.stdout.splitlines() if status.returncode == 0 else [],
        "available": commit.returncode == 0,
    }


def _artifact_kind(path: Path) -> str:
    name = path.name
    if name.endswith(".whl"):
        return "wheel"
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return "sdist"
    return "unknown"


def _artifact_members(path: Path) -> list[str]:
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            return sorted(archive.namelist())
    if path.name.endswith(".tar.gz") or path.name.endswith(".tgz"):
        with tarfile.open(path, "r:gz") as archive:
            return sorted(member.name for member in archive.getmembers())
    return []


def _required_artifact_suffixes(kind: str) -> tuple[str, ...]:
    shared = (
        "aegis_foundation/cli.py",
        "aegis_mcp/server.py",
        "aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh",
        "aegis_foundation/assets/.claude/scripts/posttooluse-tracking.sh",
        "aegis_foundation/assets/.claude/scripts/tracking-stop-gate.sh",
        "aegis_foundation/assets/scripts/_aegis_installer.py",
        "aegis_foundation/assets/scripts/codex-task",
        "aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json",
        "aegis_foundation/assets/templates/aegis/workflow/session.md",
        "aegis_foundation/assets/templates/aegis/workflow/tracker.md",
    )
    if kind == "wheel":
        return (*shared, "entry_points.txt")
    if kind == "sdist":
        return (*shared, "pyproject.toml")
    return shared


def _inspect_release_artifact(path: Path) -> dict[str, Any]:
    kind = _artifact_kind(path)
    members = _artifact_members(path)
    required = _required_artifact_suffixes(kind)
    missing = [
        suffix
        for suffix in required
        if not any(member.endswith(suffix) for member in members)
    ]
    return {
        "path": path.as_posix(),
        "name": path.name,
        "kind": kind,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "member_count": len(members),
        "required_suffixes": list(required),
        "missing_required_suffixes": missing,
        "status": "passed" if kind != "unknown" and not missing else "failed",
    }


def _certify_clean_cli_smoke(wheel: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aegis-release-cert-") as tmp:
        tmp_root = Path(tmp)
        venv_dir = tmp_root / "venv"
        target = tmp_root / "target"
        target.mkdir()
        steps: list[dict[str, Any]] = []

        venv_result, step = _run_cert_command(
            [sys.executable, "-m", "venv", venv_dir.as_posix()],
            cwd=tmp_root,
        )
        step["name"] = "create_venv"
        steps.append(step)
        if venv_result.returncode != 0:
            return {"status": "failed", "steps": steps}

        python = venv_dir / "bin" / "python"
        install_result, step = _run_cert_command(
            [python.as_posix(), "-m", "pip", "install", wheel.as_posix()],
            cwd=tmp_root,
        )
        step["name"] = "install_wheel"
        steps.append(step)
        if install_result.returncode != 0:
            return {"status": "failed", "steps": steps}

        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("AEGIS_SOURCE_ROOT", None)
        aegis_bin = venv_dir / "bin" / "aegis"

        command_steps: list[tuple[str, list[str], Path, Sequence[int], str | None, Mapping[str, str] | None]] = [
            ("aegis_version", [aegis_bin.as_posix(), "--version"], target, (0,), None, env),
            ("git_init", ["git", "init", "-b", "main"], target, (0,), None, env),
            ("aegis_inspect", [aegis_bin.as_posix(), "inspect", "--target-dir", "."], target, (0,), None, env),
            (
                "aegis_plan_install",
                [aegis_bin.as_posix(), "plan-install", "--target-dir", ".", "--primary-agent", "claude", "--agent", "claude"],
                target,
                (0,),
                None,
                env,
            ),
            (
                "aegis_install",
                [aegis_bin.as_posix(), "install", "--target-dir", ".", "--primary-agent", "claude", "--agent", "claude", "--apply"],
                target,
                (0,),
                None,
                env,
            ),
            ("aegis_status", [aegis_bin.as_posix(), "status", "--target-dir", "."], target, (0,), None, env),
            (
                "aegis_kickoff",
                [aegis_bin.as_posix(), "kickoff", "--target-dir", ".", "--task", "42", "--slug", "release-cert", "--title", "Release Certification"],
                target,
                (0,),
                None,
                env,
            ),
            (
                "readiness_quick",
                ["bash", ".claude/scripts/readiness.sh", "--quick"],
                target,
                (0,),
                None,
                env,
            ),
        ]
        for name, command, cwd, expected, input_text, command_env in command_steps:
            result, step = _run_cert_command(
                command,
                cwd=cwd,
                env=command_env,
                input_text=input_text,
                expected_returncodes=expected,
            )
            step["name"] = name
            steps.append(step)
            if result.returncode not in expected:
                return {"status": "failed", "steps": steps}

        current_work = _read_json(target / AEGIS_CURRENT_WORK_REL)
        if current_work is None:
            steps.append(
                {
                    "name": "read_current_work",
                    "status": "failed",
                    "message": f"{AEGIS_CURRENT_WORK_REL} missing after kickoff",
                }
            )
            return {"status": "failed", "steps": steps}
        paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
        reports_rel = str(paths.get("reports") or "").strip()
        if not reports_rel:
            steps.append(
                {
                    "name": "read_current_work_reports",
                    "status": "failed",
                    "message": "current work reports path missing",
                }
            )
            return {"status": "failed", "steps": steps}
        evidence_rel = f"{reports_rel}/release-certification-evidence.txt"
        claude_env = {**env, "CLAUDE_PROJECT_DIR": target.as_posix()}
        tracking_steps: list[tuple[str, list[str], Sequence[int], str | None, Mapping[str, str]]] = [
            (
                "pretooluse_allowed_evidence_write",
                ["bash", ".claude/scripts/pretooluse-gate.sh"],
                (0,),
                json.dumps({"tool_name": "Write", "tool_input": {"file_path": evidence_rel}}),
                claude_env,
            ),
            (
                "posttooluse_pending_tracking",
                ["bash", ".claude/scripts/posttooluse-tracking.sh"],
                (0,),
                json.dumps({"tool_name": "Write", "tool_input": {"file_path": evidence_rel}}),
                claude_env,
            ),
            (
                "pretooluse_blocks_before_log",
                ["bash", ".claude/scripts/pretooluse-gate.sh"],
                (2,),
                json.dumps({"tool_name": "Write", "tool_input": {"file_path": f"{reports_rel}/blocked-before-log.txt"}}),
                claude_env,
            ),
            (
                "aegis_log_tracking",
                [
                    aegis_bin.as_posix(),
                    "log",
                    "--target-dir",
                    ".",
                    "--handler",
                    "certification:write",
                    "--evidence",
                    evidence_rel,
                    "--note",
                    "Recorded release certification smoke evidence",
                ],
                (0,),
                None,
                env,
            ),
            (
                "aegis_verify_strict",
                [aegis_bin.as_posix(), "verify", "--target-dir", ".", "--strict"],
                (0,),
                None,
                env,
            ),
            (
                "protected_path_refusal",
                ["bash", ".claude/scripts/pretooluse-gate.sh"],
                (2,),
                json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {
                            "command": "printf blocked > templates/should-not-land.md",
                        },
                    }
                ),
                claude_env,
            ),
        ]
        evidence_path = target / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        for name, command, expected, input_text, command_env in tracking_steps:
            if name == "posttooluse_pending_tracking":
                evidence_path.write_text("release certification smoke evidence\n", encoding="utf-8")
                steps.append(
                    {
                        "name": "write_evidence_file",
                        "status": "passed",
                        "path": evidence_rel,
                    }
                )
            result, step = _run_cert_command(
                command,
                cwd=target,
                env=command_env,
                input_text=input_text,
                expected_returncodes=expected,
            )
            step["name"] = name
            steps.append(step)
            if result.returncode not in expected:
                return {"status": "failed", "steps": steps}

        verification_report = target / AEGIS_VERIFY_REPORT_REL
        return {
            "status": "passed",
            "steps": steps,
            "strict_verification_report": (
                verification_report.read_text(encoding="utf-8")
                if verification_report.is_file()
                else None
            ),
        }


def _certify_mcp_server_config_smoke(wheel: Path) -> dict[str, Any]:
    uvx = shutil.which("uvx")
    if uvx is None:
        return {
            "status": "skipped",
            "reason": "uvx is not available for local wheel MCP server config smoke",
        }
    with tempfile.TemporaryDirectory(prefix="aegis-release-mcp-") as tmp:
        tmp_root = Path(tmp)
        target = tmp_root / "target"
        target.mkdir()
        result, step = _run_cert_command(
            [
                uvx,
                "--from",
                wheel.as_posix(),
                "aegis-mcp-server",
                "--default-target-dir",
                target.as_posix(),
                "--describe-config",
            ],
            cwd=target,
        )
        step["name"] = "mcp_describe_config_from_local_wheel"
        if result.returncode != 0:
            return {"status": "failed", "steps": [step]}
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "status": "failed",
                "steps": [step],
                "reason": "aegis-mcp-server --describe-config did not return JSON",
            }
        checks = [
            {
                "id": "asset_origin_package",
                "status": "pass" if payload.get("asset_origin") == "package" else "fail",
                "observed": payload.get("asset_origin"),
            },
            {
                "id": "distribution_name",
                "status": "pass" if payload.get("distribution_name") == "aegis-foundation" else "fail",
                "observed": payload.get("distribution_name"),
            },
            {
                "id": "default_target_dir",
                "status": "pass" if payload.get("default_target_dir") == target.as_posix() else "fail",
                "observed": payload.get("default_target_dir"),
            },
        ]
        failed = [check for check in checks if check["status"] != "pass"]
        return {
            "status": "failed" if failed else "passed",
            "steps": [step],
            "checks": checks,
            "failed_required": len(failed),
            "config": payload,
        }


def certify_release_candidate(
    source_dir: str | Path,
    *,
    dist_dir: str | Path,
    report_file: str | Path | None = None,
    build: bool = True,
    run_smoke: bool = True,
) -> dict[str, Any]:
    source_root = _resolve_target_root(source_dir)
    dist_path = Path(dist_dir).expanduser()
    if not dist_path.is_absolute():
        dist_path = source_root / dist_path
    dist_path.mkdir(parents=True, exist_ok=True)
    report_path = Path(report_file or AEGIS_RELEASE_CERT_REPORT_REL).expanduser()
    if not report_path.is_absolute():
        report_path = source_root / report_path

    build_payload: dict[str, Any]
    if build:
        uv = shutil.which("uv")
        command = (
            [uv, "build", "--sdist", "--wheel", "--out-dir", dist_path.as_posix()]
            if uv
            else [sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", dist_path.as_posix()]
        )
        build_result, build_payload = _run_cert_command(command, cwd=source_root)
    else:
        build_payload = {
            "status": "skipped",
            "command": None,
            "reason": "build disabled by caller",
        }

    artifact_paths = sorted(
        [
            *dist_path.glob("*.whl"),
            *dist_path.glob("*.tar.gz"),
            *dist_path.glob("*.tgz"),
        ]
    )
    artifacts = [_inspect_release_artifact(path) for path in artifact_paths]
    artifact_kinds = {artifact["kind"] for artifact in artifacts}
    missing_kinds = sorted({"wheel", "sdist"} - artifact_kinds)

    wheel_paths = [path for path in artifact_paths if _artifact_kind(path) == "wheel"]
    if run_smoke and wheel_paths:
        cli_smoke = _certify_clean_cli_smoke(wheel_paths[0])
        mcp_config_smoke = _certify_mcp_server_config_smoke(wheel_paths[0])
    elif run_smoke:
        cli_smoke = {"status": "failed", "reason": "no wheel artifact available for clean CLI smoke"}
        mcp_config_smoke = {"status": "failed", "reason": "no wheel artifact available for MCP server config smoke"}
    else:
        cli_smoke = {"status": "skipped", "reason": "clean CLI smoke disabled by caller"}
        mcp_config_smoke = {"status": "skipped", "reason": "MCP server config smoke disabled by caller"}

    failures: list[dict[str, Any]] = []
    if build_payload.get("status") == "failed":
        failures.append({"stage": "build", "message": "artifact build failed"})
    if missing_kinds:
        failures.append({"stage": "artifacts", "message": "required artifact kind missing", "missing": missing_kinds})
    for artifact in artifacts:
        if artifact.get("status") == "failed":
            failures.append(
                {
                    "stage": "artifact_inspection",
                    "artifact": artifact.get("name"),
                    "missing": artifact.get("missing_required_suffixes"),
                }
            )
    if cli_smoke.get("status") == "failed":
        failures.append({"stage": "clean_cli_smoke", "message": "clean CLI smoke failed"})
    if mcp_config_smoke.get("status") == "failed":
        failures.append({"stage": "mcp_server_config_smoke", "message": "MCP server config smoke failed"})

    status_value = "failed" if failures else "passed"
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": status_value,
        "generated_at": _iso_now(),
        "source_root": source_root.as_posix(),
        "dist_dir": dist_path.as_posix(),
        "report_file": report_path.as_posix(),
        "provenance": {
            "python": sys.version.split()[0],
            "git": _git_provenance(source_root),
            "foundation_version": FOUNDATION_VERSION,
            "installer_version": INSTALLER_VERSION,
            "schema_version": SCHEMA_VERSION,
        },
        "build": build_payload,
        "artifacts": artifacts,
        "smokes": {
            "clean_cli": cli_smoke,
            "mcp_server_config": mcp_config_smoke,
            "mcp_stdio": {
                "status": "covered_by_focused_pytest",
                "test": "tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py::test_local_wheel_mcp_real_target_project_smoke_when_enabled",
                "reason": "Full install/kickoff/log/verify/closeout MCP stdio artifact proof is intentionally exercised by the focused pytest target.",
            },
        },
        "failures": failures,
        "publishing_handoff": {
            "github_release_candidate_ready": status_value == "passed" and cli_smoke.get("status") == "passed",
            "pypi_ready": False,
            "notes": [
                "GitHub release-candidate artifacts remain the first recommended public channel.",
                "PyPI publication requires a separate explicit release task.",
            ],
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_dump_json(report), encoding="utf-8")
    return report


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
