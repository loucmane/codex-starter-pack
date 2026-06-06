"""Aegis Foundation installer core.

This module is intentionally independent of argparse so the future MCP wrapper can call
the same deterministic planning, install, and verify behavior as the CLI.
"""

from __future__ import annotations

import json
import os
import re
import shlex
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
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

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
AEGIS_CLIENT_RELOAD_REL = ".aegis/state/client-reload-required.json"
AEGIS_PENDING_TRACKING_REL = ".aegis/state/pending-tracking.json"
AEGIS_DEGRADED_EVENTS_REL = ".aegis/state/degraded-events.json"
AEGIS_LOCAL_TASKS_REL = ".aegis/state/local-tasks.json"
TASKMASTER_TASKS_REL = ".taskmaster/tasks/tasks.json"
AEGIS_PLAN_REPORT_REL = ".aegis/reports/install-plan.json"
AEGIS_INSTALL_REPORT_REL = ".aegis/reports/install-report.json"
AEGIS_VERIFY_REPORT_REL = ".aegis/reports/verification-report.json"
AEGIS_CLOSEOUT_REPORT_REL = ".aegis/reports/closeout-report.json"
AEGIS_REPAIR_REPORT_REL = ".aegis/reports/repair-report.json"
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
AEGIS_LOG_EVENT_CLASSES = ("scope", "implementation", "verification", "note")
AEGIS_EVENT_DEFAULT_LOG_SURFACES = {
    "scope": ("findings", "decisions", "handoff"),
    "implementation": ("implementation", "changelog", "handoff"),
    "verification": ("implementation", "changelog", "handoff"),
    "note": AEGIS_DEFAULT_LOG_SURFACES,
}
AEGIS_PENDING_EVENT_SENTINELS = {"current", "latest"}
AEGIS_PLAN_STATUS_CHOICES = {"pending", "in-progress", "completed", "done", "n/a"}
AEGIS_CLAUDE_BLOCK_BEGIN = "<!-- AEGIS:BEGIN claude-runtime -->"
AEGIS_CLAUDE_BLOCK_END = "<!-- AEGIS:END claude-runtime -->"
AEGIS_AGENTS_BLOCK_BEGIN = "<!-- AEGIS:BEGIN agents-runtime -->"
AEGIS_AGENTS_BLOCK_END = "<!-- AEGIS:END agents-runtime -->"

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
CLAUDE_SUPPORT_FILES = (".claude/scripts/gate_lib.py",)
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


@dataclass(frozen=True)
class TaskmasterState:
    """Taskmaster task authority state for a target repository."""

    state: str
    source: str
    reason: str = ""
    message: str = ""
    tasks: tuple[Mapping[str, Any], ...] = ()

    @property
    def present(self) -> bool:
        return self.state != "absent"

    @property
    def valid(self) -> bool:
        return self.state == "valid"

    def details(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "state": self.state,
            "present": self.present,
            "valid": self.valid,
            "task_count": len(self.tasks) if self.valid else 0,
        }
        if self.reason:
            payload["reason"] = self.reason
        if self.message:
            payload["message"] = self.message
        if self.state == "invalid":
            payload["repair_guidance"] = _taskmaster_repair_guidance()
        return payload


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
        raise AegisError(
            f"primary_agent={primary_agent} must also be listed with --agent {primary_agent}"
        )
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
                    },
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
                "aegis log updates session, tracker, event-aware canonical surfaces, and explicit plan evidence",
                "aegis closeout --dry-run reports closeout readiness without mutation",
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
            "- Use Aegis MCP tools, or the project-local Aegis CLI, for Aegis workflow state: init, inspect, plan-install, install, status, next, start, kickoff, log, verify, closeout dry-runs, closeout, and future reconciliation.",
            "- Use native agent tools for normal project implementation: reading files, editing source files, running project tests, and inspecting git status or diffs.",
            "- The installed Aegis runtime, not the MCP session, is responsible for enforcement.",
            "- Installed hooks govern persistent mutations regardless of whether the attempted mutation comes from MCP, Bash, Edit, Write, or another supported tool surface.",
            "- MCP is the bootstrap and control-plane interface. It is not a replacement for the agent's editor, shell, test runner, or normal implementation workflow.",
            "- Claude Code loads `.claude/settings.json` hooks at session start. If Aegis just created or changed Claude settings/hooks, restart Claude before source edits so enforcement is active.",
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
            '- Start local work with `aegis start "<task title>"` or `./.aegis/bin/aegis start ...` only when no external task id exists.',
            '- If `.taskmaster/tasks/tasks.json` contains available numeric work, run `task-master next` and `task-master show <id>` first, then use explicit `aegis kickoff --task <id> --slug <slug> --title "<title>"`.',
            "- Taskmaster done only after Aegis closeout and doctor pass. Do not run `task-master set-status --status=done` before `aegis closeout` and read-only `aegis doctor` are both healthy.",
            "- After Taskmaster status changes, refresh generated task files. Prefer the project's targeted helper when present (for example `python3 scripts/codex-task taskmaster generate-one --id <id>`); otherwise run `task-master generate` deliberately and report that broad generated-file refresh was used.",
            '- Use explicit `aegis kickoff --task <id> --slug <slug> --title "<title>"` when an external task id already exists.',
            "- Kickoff creates Aegis-native current work state, session, plan, and work-tracking files.",
            "- `.aegis/state/current-work.json` is the portable authority for READY.",
            "- Taskmaster is validated only when no Aegis current-work state exists or when current work explicitly marks Taskmaster required.",
            '- Normal feature work is: confirm readiness and `aegis next`; if no current work exists, use Taskmaster next/show plus `aegis kickoff` when Taskmaster provides a numeric task, otherwise infer a short title from the user\'s request and run `aegis start "<task title>"`; mark scope complete with `aegis log --plan-step auto`; make the task-scoped code change with native tools; let PostToolUse create pending tracking; run `aegis log --pending-id current --plan-step auto` for the changed source file; run task-specific verification and log it with `--plan-step auto`; run `aegis verify --strict`; log the strict verification report with `--pending-id current --plan-step auto`; run `aegis closeout --dry-run --update-handoff` for preflight; if handoff semantic gates fail, run `aegis handoff repair`; run `aegis closeout --update-handoff`; run read-only `aegis doctor`; only then mark Taskmaster done if Taskmaster is in use.',
            '- After every meaningful mutation, run `aegis log --pending-id <id> --note "<past-tense note>"` to write S:W:H:E entries to the active session, tracker, and event-aware canonical surfaces.',
            "- `aegis log` updates plan state only when `--plan-step` is supplied. This prevents generic evidence logs from accidentally changing an unrelated plan step.",
            "- The next persistent mutation is blocked until pending S:W:H:E tracking is logged; this is what makes the workflow mechanical rather than advisory.",
            "- Omit `--surface` for event-aware defaults. Scope logs update findings, decisions, and handoff; implementation and verification logs update implementation, changelog, and handoff. Use `--surface` only for targeted repairs.",
            "- `aegis closeout --dry-run --update-handoff` checks closeout gates without writing reports, handoff updates, or current-work state.",
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
            "If this project is not initialized yet, run:",
            "",
            "```bash",
            "aegis init",
            "```",
            "",
            "If this `aegis init` created or changed `.claude/settings.json` or `.claude/scripts/*`, stop before source edits and restart Claude Code in this project. Claude loads hooks at session start; after restart, run `aegis next` and continue.",
            "",
            "If readiness is BLOCKED because no current work exists and `.taskmaster/` is present, use Taskmaster as the task authority first:",
            "",
            "```bash",
            "task-master next",
            "task-master show <id>",
            'aegis kickoff --task <id> --slug <slug> --title "<title>"',
            "```",
            "",
            "Taskmaster done only after Aegis closeout and doctor pass.",
            "After marking Taskmaster done, refresh generated task files with the project helper when present; otherwise run `task-master generate` deliberately and mention that broad refresh in the final report.",
            "",
            "If no Taskmaster numeric task is available, infer a short task title from the user's request and start tracked local work with:",
            "",
            "```bash",
            'aegis start "<task title>"',
            "```",
            "",
            "If `aegis` is not on PATH, use the installed project-local shim: `./.aegis/bin/aegis ...`.",
            "",
            "Project hooks route mutation tools through `.claude/scripts/pretooluse-gate.sh`.",
            "",
            "Tool routing:",
            "",
            "- Use Aegis MCP tools for Aegis workflow state when they are available: inspect, status, next, plan_install, install, start, kickoff for explicit external numeric task ids, log, verify, closeout_ready, closeout, and future reconciliation.",
            "- If Taskmaster is installed and has available work, run `task-master next` and `task-master show <id>` or the Taskmaster MCP equivalent before `aegis kickoff`.",
            '- Use `aegis init` for first-time project setup and `aegis start "<task title>"` for local task kickoff only when no external task id exists.',
            "- Use `aegis ...` or `./.aegis/bin/aegis ...` for the same workflow operations when MCP is unavailable.",
            "- Use native Claude tools for normal implementation work: reading files, editing source, running tests, and inspecting git status or diffs.",
            "- Do not use MCP as a replacement for normal source editing. The installed hooks enforce the workflow around native tool use.",
            "- If `aegis.init` or `aegis.install` reports `client_reload.required=true`, restart Claude before any source edits; then run `aegis next` after the reload.",
            "",
            "Normal feature-work loop:",
            "",
            '1. Confirm readiness. If Aegis is missing, run `aegis init`. If no current work exists, run `aegis next` or `./.aegis/bin/aegis next`; use Taskmaster next/show plus `aegis kickoff` when Taskmaster provides a numeric task, otherwise infer a task title and run `aegis start "<task title>"`.',
            '2. Record scope with `aegis log --handler claude:scope --evidence <scope-doc-or-file> --note "Confirmed task scope" --plan-step auto --plan-status completed`.',
            "3. Make the task-scoped source change requested by the user with native Edit/Write tools.",
            '4. After the hook records pending tracking, run `aegis log --pending-id current --note "<past-tense note>" --plan-step auto --plan-status completed`.',
            "5. Run task-specific verification and log it with `--plan-step auto --plan-status completed`.",
            '6. Run `aegis verify --strict` or `./.aegis/bin/aegis verify --strict`, then log the strict verification pending event with `aegis log --pending-id current --note "Recorded strict verification evidence" --plan-step auto --plan-status completed`.',
            "7. Run `aegis closeout --dry-run --update-handoff` or call MCP `aegis.closeout_ready` before final closeout.",
            "8. If handoff semantic gates fail, run `aegis handoff repair` or call MCP `aegis.handoff_repair apply=true`, then re-run closeout readiness.",
            "9. Run `aegis closeout --update-handoff` or `./.aegis/bin/aegis closeout --update-handoff`; do not report the task complete until closeout passes.",
            "10. Run read-only `aegis doctor --target-dir .` or call MCP `aegis.doctor` once after closeout; include the health result in the final report.",
            "11. If Taskmaster is in use, run `task-master set-status --id=<id> --status=done` only after closeout and doctor pass. Then refresh generated task files with `python3 scripts/codex-task taskmaster generate-one --id <id>` when that project helper exists; otherwise run `task-master generate` deliberately and report the broad refresh.",
            "",
            'After any mutation, use `aegis log --pending-id <id> --note "<past-tense note>" --plan-step auto` before attempting the next mutation. Use explicit `--handler`, `--evidence`, and explicit plan step only when no pending event exists or auto inference reports ambiguity.',
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
                "Bash(aegis init:*)",
                "Bash(aegis status:*)",
                "Bash(aegis next:*)",
                "Bash(aegis start:*)",
                "Bash(aegis mcp register:*)",
                "Bash(aegis kickoff:*)",
                "Bash(aegis log:*)",
                "Bash(aegis verify:*)",
                "Bash(aegis closeout:*)",
                "Bash(task-master *)",
                "Bash(./.aegis/bin/aegis inspect:*)",
                "Bash(./.aegis/bin/aegis init:*)",
                "Bash(./.aegis/bin/aegis status:*)",
                "Bash(./.aegis/bin/aegis next:*)",
                "Bash(./.aegis/bin/aegis start:*)",
                "Bash(./.aegis/bin/aegis mcp register:*)",
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
            ],
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
            'SELF="$0"',
            'SELF_RESOLVED="$(cd "$(dirname "$SELF")" && pwd -P)/$(basename "$SELF")"',
            "if command -v aegis >/dev/null 2>&1; then",
            '  RESOLVED="$(command -v aegis)"',
            '  RESOLVED_ABS="$(cd "$(dirname "$RESOLVED")" && pwd -P)/$(basename "$RESOLVED")"',
            '  if [ "$RESOLVED_ABS" != "$SELF_RESOLVED" ]; then',
            '    exec "$RESOLVED" "$@"',
            "  fi",
            "fi",
            "",
            "if python3 -c 'import aegis_foundation.cli' >/dev/null 2>&1; then",
            '  exec python3 -m aegis_foundation.cli "$@"',
            "fi",
            "",
            f'AEGIS_SOURCE_FALLBACK="{source}"',
            'if [ -n "${AEGIS_SOURCE_ROOT:-}" ]; then',
            '  AEGIS_SOURCE_FALLBACK="$AEGIS_SOURCE_ROOT"',
            "fi",
            'if [ -d "$AEGIS_SOURCE_FALLBACK" ]; then',
            '  for AEGIS_PYTHONPATH_CANDIDATE in "$AEGIS_SOURCE_FALLBACK" "$AEGIS_SOURCE_FALLBACK/.." "$AEGIS_SOURCE_FALLBACK/../.."; do',
            "    if PYTHONPATH=\"$AEGIS_PYTHONPATH_CANDIDATE${PYTHONPATH:+:$PYTHONPATH}\" python3 -c 'import aegis_foundation.cli' >/dev/null 2>&1; then",
            '      export PYTHONPATH="$AEGIS_PYTHONPATH_CANDIDATE${PYTHONPATH:+:$PYTHONPATH}"',
            '      exec python3 -m aegis_foundation.cli --source-root "$AEGIS_SOURCE_FALLBACK" "$@"',
            "    fi",
            "  done",
            "fi",
            "",
            'echo "Aegis CLI is unavailable. Install aegis-foundation, add aegis to PATH, or set AEGIS_SOURCE_ROOT." >&2',
            "exit 127",
            "",
        ]
    )
    return text.encode("utf-8")


def _asset_from_source(source_root: Path, rel_path: str, *, kind: str = "managed") -> Asset:
    path = source_root / rel_path
    return Asset(
        path=rel_path,
        content=_read_bytes(source_root, rel_path),
        executable=os.access(path, os.X_OK),
        kind=kind,
    )


def _asset_from_source_as(
    source_root: Path, source_rel_path: str, target_rel_path: str, *, kind: str = "managed"
) -> Asset:
    path = source_root / source_rel_path
    return Asset(
        path=target_rel_path,
        content=_read_bytes(source_root, source_rel_path),
        executable=os.access(path, os.X_OK),
        kind=kind,
    )


def _base_assets(
    source_root: Path, primary_agent: str, enabled_agents: Sequence[str]
) -> list[Asset]:
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


def _adapter_assets(
    source_root: Path, primary_agent: str, enabled_agents: Sequence[str]
) -> list[Asset]:
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


def _managed_assets(
    source_root: Path, primary_agent: str, enabled_agents: Sequence[str]
) -> list[Asset]:
    return _base_assets(source_root, primary_agent, enabled_agents) + _adapter_assets(
        source_root, primary_agent, enabled_agents
    )


def _claude_runtime_block(aegis_entrypoint: bytes) -> str:
    entrypoint = aegis_entrypoint.decode("utf-8").strip()
    return "\n".join(
        [
            AEGIS_CLAUDE_BLOCK_BEGIN,
            entrypoint,
            AEGIS_CLAUDE_BLOCK_END,
            "",
        ]
    )


def _managed_runtime_block(
    *,
    begin_marker: str,
    end_marker: str,
    entrypoint: bytes,
) -> str:
    text = entrypoint.decode("utf-8").strip()
    return "\n".join([begin_marker, text, end_marker, ""])


def _merge_managed_entrypoint(
    existing: bytes,
    aegis_entrypoint: bytes,
    *,
    begin_marker: str,
    end_marker: str,
    existing_heading: str,
) -> bytes | None:
    if existing == aegis_entrypoint:
        return aegis_entrypoint
    try:
        existing_text = existing.decode("utf-8")
    except UnicodeDecodeError:
        return None
    block = _managed_runtime_block(
        begin_marker=begin_marker,
        end_marker=end_marker,
        entrypoint=aegis_entrypoint,
    )
    if begin_marker in existing_text and end_marker in existing_text:
        pattern = re.compile(
            rf"{re.escape(begin_marker)}.*?{re.escape(end_marker)}\n?",
            re.DOTALL,
        )
        return pattern.sub(block, existing_text, count=1).encode("utf-8")
    prefix = f"{block}\n---\n\n## {existing_heading}\n\n"
    return f"{prefix}{existing_text}".encode("utf-8")


def _merge_claude_entrypoint(existing: bytes, aegis_entrypoint: bytes) -> bytes | None:
    """Return CLAUDE.md with an Aegis-managed block while preserving project content."""

    return _merge_managed_entrypoint(
        existing,
        aegis_entrypoint,
        begin_marker=AEGIS_CLAUDE_BLOCK_BEGIN,
        end_marker=AEGIS_CLAUDE_BLOCK_END,
        existing_heading="Existing Project Instructions",
    )


def _merge_agents_entrypoint(existing: bytes, aegis_entrypoint: bytes) -> bytes | None:
    """Return AGENTS.md with an Aegis-managed block while preserving project content."""

    return _merge_managed_entrypoint(
        existing,
        aegis_entrypoint,
        begin_marker=AEGIS_AGENTS_BLOCK_BEGIN,
        end_marker=AEGIS_AGENTS_BLOCK_END,
        existing_heading="Existing Agent Instructions",
    )


def _assets_for_target(target_root: Path, assets: Sequence[Asset]) -> list[Asset]:
    """Materialize target-specific assets such as merged Claude entrypoints."""

    materialized: list[Asset] = []
    for asset in assets:
        if asset.path == "CLAUDE.md" and asset.kind == "adapter":
            target = target_root / asset.path
            if target.exists() and target.is_file():
                merged = _merge_claude_entrypoint(target.read_bytes(), asset.content)
                if merged is not None:
                    materialized.append(
                        Asset(
                            path=asset.path,
                            content=merged,
                            executable=asset.executable,
                            kind=asset.kind,
                        )
                    )
                    continue
        if asset.path == "AGENTS.md":
            target = target_root / asset.path
            if target.exists() and target.is_file():
                merged = _merge_agents_entrypoint(target.read_bytes(), asset.content)
                if merged is not None:
                    materialized.append(
                        Asset(
                            path=asset.path,
                            content=merged,
                            executable=asset.executable,
                            kind=asset.kind,
                        )
                    )
                    continue
        materialized.append(asset)
    return materialized


def _agent_records(
    enabled_agents: Sequence[str], managed_assets: Sequence[Asset]
) -> dict[str, dict[str, Any]]:
    managed_by_agent: dict[str, list[str]] = {
        "claude": [
            asset.path
            for asset in managed_assets
            if asset.path == "CLAUDE.md" or asset.path.startswith(".claude/")
        ],
        "codex": [
            asset.path
            for asset in managed_assets
            if asset.path == "CODEX.md" or asset.path.startswith("scripts/")
        ],
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


def _plan_operations(
    target_root: Path, assets: Sequence[Asset], manifest_bytes: bytes
) -> list[dict[str, Any]]:
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
        if asset.path == "CLAUDE.md" and asset.kind == "adapter":
            operations.append(
                {
                    "action": "modify",
                    "path": asset.path,
                    "classification": "modify",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": "Existing Claude instructions will be preserved below an Aegis-managed runtime block.",
                }
            )
            continue
        if asset.path == "AGENTS.md":
            operations.append(
                {
                    "action": "modify",
                    "path": asset.path,
                    "classification": "modify",
                    "safe_to_apply": True,
                    "managed": True,
                    "reason": "Existing agent instructions will be preserved below an Aegis-managed runtime block.",
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


def _client_reload_marker_path(target_root: Path) -> Path:
    return target_root / AEGIS_CLIENT_RELOAD_REL


def _client_reload_marker(target_root: Path) -> dict[str, Any] | None:
    payload = _read_json(_client_reload_marker_path(target_root))
    return payload if isinstance(payload, dict) else None


def _write_client_reload_marker(target_root: Path, report: Mapping[str, Any]) -> None:
    changed_paths = [
        str(path) for path in report.get("changed_paths", []) if isinstance(path, str) and path
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "required",
        "agent": report.get("agent") or "claude",
        "created_at": _iso_now(),
        "changed_paths": changed_paths,
        "reason": report.get("reason"),
        "instructions": report.get("instructions"),
        "clearance": {
            "method": "installed_claude_pretooluse_hook",
            "path": ".claude/scripts/pretooluse-gate.sh",
            "description": "A restarted Claude session proves hook activation when PreToolUse runs and clears this marker.",
        },
    }
    _write_text(target_root, AEGIS_CLIENT_RELOAD_REL, _dump_json(payload))


def _client_reload_report(
    target_root: Path, plan: Mapping[str, Any], enabled_agents: Sequence[str]
) -> dict[str, Any]:
    changed_paths: list[str] = []
    if "claude" in enabled_agents:
        for operation in plan.get("operations", []):
            if not isinstance(operation, Mapping):
                continue
            classification = str(operation.get("classification") or "")
            rel_path = str(operation.get("path") or "")
            if classification not in {"create", "modify"}:
                continue
            if rel_path == "CLAUDE.md" or rel_path.startswith(".claude/"):
                changed_paths.append(rel_path)

    unique_changed_paths = sorted(set(changed_paths))
    marker = _client_reload_marker(target_root)
    marker_paths = [
        str(path)
        for path in (marker or {}).get("changed_paths", [])
        if isinstance(path, str) and path
    ]
    effective_paths = unique_changed_paths or sorted(set(marker_paths))
    required = bool(unique_changed_paths) or marker is not None
    return {
        "required": required,
        "agent": "claude" if "claude" in enabled_agents else None,
        "severity": "hard_stop" if required else "none",
        "must_stop": required,
        "pending_marker": marker is not None,
        "marker_path": AEGIS_CLIENT_RELOAD_REL if required else None,
        "changed_paths": effective_paths,
        "reason": (
            "Claude Code loads project hook settings at session start; newly created or changed "
            ".claude/settings.json and .claude/scripts/* hooks are not guaranteed to govern this already-running session."
            if required
            else "No Claude adapter settings or hook scripts changed in this install."
        ),
        "instructions": (
            "HARD STOP: if this install ran inside Claude Code, do not edit source files, run project verification, "
            "mutate Taskmaster, or call aegis.start/aegis.kickoff in this same session. restart Claude in this "
            "project so newly installed hooks are active. After restart, run aegis.next and start or kickoff tracked "
            "work before mutating files."
            if required
            else "No Claude restart is required by this install."
        ),
        "forbidden_until_reload": (
            [
                "source edits",
                "project verification commands",
                "Taskmaster mutations",
                "aegis.start",
                "aegis.kickoff",
                "aegis.verify",
                "aegis.closeout",
            ]
            if required
            else []
        ),
        "allowed_until_reload": (
            [
                "read-only Aegis inspect/status/next/doctor",
                "tell the user to restart Claude in this project",
            ]
            if required
            else []
        ),
    }


def _expected_manifest_summary(primary_agent: str, enabled_agents: Sequence[str]) -> dict[str, Any]:
    return {
        "path": AEGIS_MANIFEST_REL,
        "profile": PROFILE_GENERIC,
        "primary_agent": primary_agent,
        "agents": {
            agent: {
                "enabled": agent in enabled_agents,
                "gate_ids": list(
                    CLAUDE_GATE_IDS
                    if agent == "claude"
                    else CODEX_GATE_IDS if agent == "codex" else ()
                ),
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


def inspect_project(
    target_dir: str | Path,
    *,
    profile: str = PROFILE_GENERIC,
    source_root: str | Path | None = None,
    default_primary_agent: str = "claude",
    default_agents: Sequence[str] | None = None,
) -> dict[str, Any]:
    if profile != PROFILE_GENERIC:
        raise AegisError(f"Unsupported Aegis profile in V1: {profile}")
    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve() if source_root else Path(__file__).resolve().parents[1]
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
        "workflow_guidance": next_action(
            target_root,
            source_root=source,
            default_primary_agent=default_primary_agent,
            default_agents=default_agents,
        ),
    }


def status(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    default_primary_agent: str = "claude",
    default_agents: Sequence[str] | None = None,
) -> dict[str, Any]:
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
        payload["workflow_guidance"] = next_action(
            target_root,
            source_root=source,
            default_primary_agent=default_primary_agent,
            default_agents=default_agents,
        )
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
    payload["workflow_guidance"] = next_action(
        target_root,
        source_root=source,
        default_primary_agent=default_primary_agent,
        default_agents=default_agents,
    )
    return payload


AEGIS_ARCHITECTURE_NOTES = (
    "Aegis CLI/MCP controls workflow state and evidence. Native agent tools perform "
    "source reads, edits, and project tests. Installed hooks and guards enforce tracking "
    "and protected-path behavior."
)


def _workflow_guidance_payload(
    *,
    phase: str,
    state: str,
    next_required_action: str,
    suggested_cli: str,
    suggested_mcp_tool: str | None = None,
    suggested_mcp_arguments: Mapping[str, Any] | None = None,
    missing_gates: Sequence[str] | None = None,
    copyable_repairs: Sequence[str] | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "phase": phase,
        "state": state,
        "next_required_action": next_required_action,
        "suggested_cli": suggested_cli,
        "suggested_mcp_call": (
            {
                "tool": suggested_mcp_tool,
                "arguments": dict(suggested_mcp_arguments or {}),
            }
            if suggested_mcp_tool
            else None
        ),
        "missing_gates": list(missing_gates or []),
        "copyable_repairs": list(copyable_repairs or []),
        "read_only": True,
        "architecture_notes": AEGIS_ARCHITECTURE_NOTES,
    }
    if details:
        payload["details"] = dict(details)
    return payload


def _plan_step_completed(plan_rows: Mapping[str, Mapping[str, Any]], step: str) -> bool:
    row = plan_rows.get(step)
    return isinstance(row, Mapping) and str(row.get("status") or "").lower() in {
        "completed",
        "done",
    }


def _strict_verify_passed(target_root: Path) -> bool:
    report = _read_json(target_root / AEGIS_VERIFY_REPORT_REL)
    if not isinstance(report, Mapping):
        return False
    return report.get("mode") == "strict" and report.get("status") == "passed"


def _closeout_passed(target_root: Path) -> bool:
    report = _read_json(target_root / AEGIS_CLOSEOUT_REPORT_REL)
    if isinstance(report, Mapping) and report.get("status") == "passed":
        return True
    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    return isinstance(current_work, Mapping) and bool(current_work.get("closeout_passed_at"))


def _numeric_task_id(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if re.fullmatch(r"\d+", text) else None


TASKMASTER_STATUS_CHOICES = {
    "pending",
    "in-progress",
    "done",
    "completed",
    "deferred",
    "cancelled",
    "blocked",
}


def _taskmaster_repair_guidance() -> list[str]:
    return [
        f"Inspect and repair {TASKMASTER_TASKS_REL}.",
        "Run task-master validate-dependencies after repairing Taskmaster state.",
        "Run python3 scripts/codex-task taskmaster health when the project helper exists.",
    ]


def _invalid_taskmaster_state(reason: str, message: str) -> TaskmasterState:
    return TaskmasterState(
        state="invalid",
        source=TASKMASTER_TASKS_REL,
        reason=reason,
        message=message,
    )


def _iter_taskmaster_tasks(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    task_lists: list[Any] = []
    root_tasks = payload.get("tasks")
    if isinstance(root_tasks, list):
        task_lists.append(root_tasks)
    for value in payload.values():
        if isinstance(value, Mapping) and isinstance(value.get("tasks"), list):
            task_lists.append(value["tasks"])

    tasks: list[Mapping[str, Any]] = []
    seen_ids: set[str] = set()
    for task_list in task_lists:
        for item in task_list:
            if not isinstance(item, Mapping):
                continue
            task_id = _numeric_task_id(item.get("id"))
            if task_id is None or task_id in seen_ids:
                continue
            seen_ids.add(task_id)
            tasks.append(item)
    return tasks


def _taskmaster_task_lists(payload: Mapping[str, Any]) -> tuple[list[Any], TaskmasterState | None]:
    task_lists: list[Any] = []
    if "tasks" in payload:
        root_tasks = payload.get("tasks")
        if not isinstance(root_tasks, list):
            return [], _invalid_taskmaster_state(
                "malformed_task_container",
                "root tasks field must be a list",
            )
        task_lists.append(root_tasks)
    for tag, value in payload.items():
        if not isinstance(value, Mapping) or "tasks" not in value:
            continue
        tagged_tasks = value.get("tasks")
        if not isinstance(tagged_tasks, list):
            return [], _invalid_taskmaster_state(
                "malformed_task_container",
                f"tag {tag!s} tasks field must be a list",
            )
        task_lists.append(tagged_tasks)
    if not task_lists:
        return [], _invalid_taskmaster_state(
            "missing_task_container",
            "Taskmaster payload must contain at least one tasks list",
        )
    return task_lists, None


def _validate_taskmaster_tasks(task_lists: Sequence[Sequence[Any]]) -> TaskmasterState | None:
    seen_ids: set[str] = set()
    for list_index, task_list in enumerate(task_lists):
        for item_index, item in enumerate(task_list):
            location = f"tasks list {list_index} item {item_index}"
            if not isinstance(item, Mapping):
                return _invalid_taskmaster_state(
                    "malformed_task",
                    f"{location} must be an object",
                )
            task_id = _numeric_task_id(item.get("id"))
            if task_id is None:
                return _invalid_taskmaster_state(
                    "invalid_task_id",
                    f"{location} must have a numeric id",
                )
            if task_id in seen_ids:
                return _invalid_taskmaster_state(
                    "duplicate_task_id",
                    f"Taskmaster task id {task_id} appears more than once",
                )
            seen_ids.add(task_id)
            raw_status = item.get("status")
            if not isinstance(raw_status, str) or not raw_status.strip():
                return _invalid_taskmaster_state(
                    "invalid_task_status",
                    f"task {task_id} must have a non-empty string status",
                )
            status = raw_status.strip().lower()
            if status not in TASKMASTER_STATUS_CHOICES:
                return _invalid_taskmaster_state(
                    "invalid_task_status",
                    f"task {task_id} has unsupported status {raw_status!r}",
                )
            raw_dependencies = item.get("dependencies")
            if raw_dependencies is None:
                continue
            if not isinstance(raw_dependencies, list):
                return _invalid_taskmaster_state(
                    "invalid_task_dependencies",
                    f"task {task_id} dependencies must be a list when present",
                )
            for dependency in raw_dependencies:
                if _numeric_task_id(dependency) is None:
                    return _invalid_taskmaster_state(
                        "invalid_task_dependency",
                        f"task {task_id} dependency {dependency!r} is not a numeric task id",
                    )
    if not seen_ids:
        return _invalid_taskmaster_state(
            "empty_taskmaster_tasks",
            "Taskmaster payload must contain at least one task",
        )
    return None


def _taskmaster_state(target_root: Path) -> TaskmasterState:
    path = target_root / TASKMASTER_TASKS_REL
    if not path.exists():
        return TaskmasterState(state="absent", source=TASKMASTER_TASKS_REL)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _invalid_taskmaster_state(
            "json_decode_error",
            f"{TASKMASTER_TASKS_REL} is not valid JSON: {exc.msg}",
        )
    except OSError as exc:
        return _invalid_taskmaster_state(
            "unreadable",
            f"{TASKMASTER_TASKS_REL} could not be read: {exc}",
        )
    if not isinstance(payload, Mapping):
        return _invalid_taskmaster_state(
            "non_object_payload",
            "Taskmaster payload root must be a JSON object",
        )
    task_lists, invalid = _taskmaster_task_lists(payload)
    if invalid is not None:
        return invalid
    invalid = _validate_taskmaster_tasks(task_lists)
    if invalid is not None:
        return invalid
    return TaskmasterState(
        state="valid",
        source=TASKMASTER_TASKS_REL,
        tasks=tuple(_iter_taskmaster_tasks(payload)),
    )


def _normalise_default_agent_selection(
    primary_agent: str = "claude",
    agents: Sequence[str] | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Return a valid default install agent selection for guidance payloads."""

    primary = primary_agent if primary_agent in PRIMARY_AGENT_CHOICES else "claude"
    requested = tuple(dict.fromkeys(agents or ()))
    if not requested and primary in AGENT_CHOICES:
        requested = (primary,)
    if not requested and primary == "none":
        requested = ()
    try:
        selected = _enabled_agents(primary, requested)
    except AegisError:
        primary = "claude"
        selected = ("claude",)
    return primary, selected


def _agent_selection_cli_args(primary_agent: str, agents: Sequence[str]) -> str:
    parts = [f"--primary-agent {primary_agent}"]
    parts.extend(f"--agent {agent}" for agent in agents)
    return " ".join(parts)


def _enabled_agents_from_manifest(manifest: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ()
    agents = manifest.get("agents")
    if not isinstance(agents, Mapping):
        return ()
    enabled: list[str] = []
    for name, payload in agents.items():
        if name not in AGENT_CHOICES or not isinstance(payload, Mapping):
            continue
        if bool(payload.get("enabled")):
            enabled.append(str(name))
    return tuple(enabled)


def _workflow_handler_prefix(target_root: Path) -> str:
    manifest = _read_json(target_root / AEGIS_MANIFEST_REL)
    primary = (
        str(manifest.get("primary_agent") or "").strip() if isinstance(manifest, Mapping) else ""
    )
    if primary in AGENT_CHOICES:
        return primary
    enabled = _enabled_agents_from_manifest(manifest)
    if len(enabled) == 1:
        return enabled[0]
    return "agent"


def _workflow_log_handler(target_root: Path, event_class: str) -> str:
    return f"{_workflow_handler_prefix(target_root)}:{event_class}"


def _expects_pending_tracking(target_root: Path) -> bool:
    """Return true when the installed primary workflow is expected to enqueue hook events."""

    manifest = _read_json(target_root / AEGIS_MANIFEST_REL)
    if not isinstance(manifest, Mapping):
        return True
    primary = str(manifest.get("primary_agent") or "").strip()
    return primary == "claude" and "claude" in _enabled_agents_from_manifest(manifest)


def next_action(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    default_primary_agent: str = "claude",
    default_agents: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Return read-only workflow guidance for the next Aegis action."""

    target_root = _resolve_target_root(target_dir)
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest_exists = manifest_path.exists()
    manifest = _read_json(manifest_path)
    guidance_primary_agent, guidance_agents = _normalise_default_agent_selection(
        default_primary_agent,
        default_agents,
    )
    public_init_cli = (
        "aegis init"
        if guidance_primary_agent == "claude" and guidance_agents == ("claude",)
        else f"aegis init {_agent_selection_cli_args(guidance_primary_agent, guidance_agents)}"
    )
    plan_install_cli = f"aegis plan-install --target-dir . {_agent_selection_cli_args(guidance_primary_agent, guidance_agents)}"
    install_cli = f"aegis install --target-dir . {_agent_selection_cli_args(guidance_primary_agent, guidance_agents)} --apply"
    if manifest is None:
        if manifest_exists:
            return _workflow_guidance_payload(
                phase="bootstrap",
                state="invalid_manifest",
                next_required_action="repair or restore .aegis/foundation-manifest.json before continuing",
                suggested_cli="./.aegis/bin/aegis status --target-dir .",
                suggested_mcp_tool="aegis.status",
                suggested_mcp_arguments={"target_dir": "."},
                missing_gates=["aegis.manifest_schema"],
                copyable_repairs=[
                    "Restore .aegis/foundation-manifest.json from git history or reinstall Aegis after reviewing plan-install output."
                ],
            )
        return _workflow_guidance_payload(
            phase="bootstrap",
            state="not_installed",
            next_required_action=(
                "HARD STOP before source edits: when Aegis MCP is available, call "
                "suggested_mcp_call (aegis.init) before starting work. Use suggested_cli "
                "only as a CLI fallback when `aegis` is already on PATH. Do not run "
                "project verification, Taskmaster mutation, or Aegis start/kickoff first."
            ),
            suggested_cli=public_init_cli,
            suggested_mcp_tool="aegis.init",
            suggested_mcp_arguments={
                "target_dir": ".",
                "profile": PROFILE_GENERIC,
                "primary_agent": guidance_primary_agent,
                "agents": list(guidance_agents),
                "apply": True,
                "verify_after_install": True,
            },
            missing_gates=["aegis.manifest"],
            copyable_repairs=[
                public_init_cli,
                plan_install_cli,
                install_cli,
            ],
            details={
                "default_primary_agent": guidance_primary_agent,
                "default_agents": list(guidance_agents),
                "preferred_invocation": "mcp",
                "mcp_preferred_when_available": True,
                "cli_requires_aegis_on_path": True,
                "must_initialize_before_source_edits": True,
                "forbidden_until_init": [
                    "source edits",
                    "project verification",
                    "Taskmaster mutations",
                    "aegis.start",
                    "aegis.kickoff",
                ],
                "allowed_until_init": [
                    "read-only project inspection",
                    "Taskmaster next/show discovery",
                    "aegis.inspect",
                    "aegis.status",
                    "aegis.next",
                    "aegis.init",
                ],
            },
        )

    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if not isinstance(current_work, Mapping):
        reload_marker = _client_reload_marker(target_root)
        if reload_marker is not None:
            return _workflow_guidance_payload(
                phase="bootstrap",
                state="client_reload_required",
                next_required_action=(
                    "restart Claude before start/kickoff or source edits so newly installed hooks are active"
                ),
                suggested_cli="Restart Claude Code in this project, then run ./.aegis/bin/aegis next --target-dir .",
                suggested_mcp_tool="aegis.next",
                suggested_mcp_arguments={"target_dir": "."},
                missing_gates=["claude.client_reload"],
                copyable_repairs=[
                    "Exit this Claude session.",
                    "Start Claude again in this same project directory.",
                    "./.aegis/bin/aegis next --target-dir .",
                ],
                details={
                    "client_reload_required": True,
                    "marker_path": AEGIS_CLIENT_RELOAD_REL,
                    "changed_paths": reload_marker.get("changed_paths", []),
                    "clearance": reload_marker.get("clearance", {}),
                },
            )
        taskmaster = _taskmaster_state(target_root)
        if taskmaster.state == "invalid":
            return _workflow_guidance_payload(
                phase="start",
                state="installed_taskmaster_invalid",
                next_required_action=(
                    "repair Taskmaster task state before Aegis can start or select work"
                ),
                suggested_cli="python3 scripts/codex-task taskmaster health",
                missing_gates=["aegis.current_work", "taskmaster.tasks_json_valid"],
                copyable_repairs=_taskmaster_repair_guidance(),
                details={
                    "taskmaster": {
                        **taskmaster.details(),
                        "task_selection_authority": "taskmaster",
                        "aegis_task_selection": "suppressed",
                        "local_fallback_allowed": False,
                    }
                },
            )
        if taskmaster.state == "valid":
            return _workflow_guidance_payload(
                phase="start",
                state="installed_taskmaster_present",
                next_required_action=(
                    "use Taskmaster next/show as task authority, then start Aegis with an explicit "
                    "Taskmaster numeric task id before mutating files"
                ),
                suggested_cli=(
                    "task-master next && task-master show <id> && "
                    "./.aegis/bin/aegis kickoff --target-dir . --task <id> --slug <slug> --title '<title>'"
                ),
                missing_gates=["aegis.current_work"],
                copyable_repairs=[
                    "task-master next",
                    "task-master show <id>",
                    "./.aegis/bin/aegis kickoff --target-dir . --task <id> --slug <slug> --title '<title>'",
                    (
                        "task-master set-status --id=<id> --status=done "
                        "only after aegis closeout and aegis doctor pass"
                    ),
                ],
                details={
                    "taskmaster": {
                        **taskmaster.details(),
                        "task_selection_authority": "taskmaster",
                        "aegis_task_selection": "suppressed",
                        "kickoff_requires_explicit_taskmaster_id": True,
                        "local_fallback_allowed": False,
                        "ordering": [
                            "task-master next/show",
                            "aegis.kickoff",
                            "native source edit",
                            "aegis.verify",
                            "aegis.closeout",
                            "aegis.doctor",
                            "task-master set-status --status=done",
                        ],
                    }
                },
            )
        return _workflow_guidance_payload(
            phase="start",
            state="installed_no_current_work",
            next_required_action="start task-scoped local work before mutating files",
            suggested_cli="./.aegis/bin/aegis start '<task title>'",
            suggested_mcp_tool="aegis.start",
            suggested_mcp_arguments={
                "target_dir": ".",
                "title": "<title>",
                "apply": True,
            },
            missing_gates=["aegis.current_work"],
            copyable_repairs=[
                "./.aegis/bin/aegis start '<task title>'",
                "./.aegis/bin/aegis kickoff --target-dir . --task <id> --slug <slug> --title '<title>'",
            ],
        )

    pending_events = _pending_tracking_events(target_root)
    if pending_events:
        ids = [str(event.get("id") or "unknown") for event in pending_events]
        return _workflow_guidance_payload(
            phase="track",
            state="pending_tracking",
            next_required_action="log the pending S:W:H:E event before any further mutation",
            suggested_cli="./.aegis/bin/aegis log --target-dir . --pending-id current --note '<past-tense note>' --plan-step auto --plan-status completed",
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments={
                "target_dir": ".",
                "pending_event_id": "current",
                "note": "<past-tense note>",
                "plan_step": "auto",
                "plan_status": "completed",
                "apply": True,
            },
            missing_gates=["mutation.pending_tracking_empty"],
            copyable_repairs=[
                "./.aegis/bin/aegis log --target-dir . --pending-id current --note '<past-tense note>' --plan-step auto --plan-status completed"
            ],
            details={"pending_event_ids": ids},
        )

    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    work_rel = str(paths.get("work_tracking") or "").strip()
    plan_rel = str(paths.get("plan") or "plans/current").strip()
    tracker_rel = (
        f"{work_rel}/TRACKER.md" if work_rel else "docs/ai/work-tracking/active/<folder>/TRACKER.md"
    )
    findings_rel = (
        f"{work_rel}/FINDINGS.md"
        if work_rel
        else "docs/ai/work-tracking/active/<folder>/FINDINGS.md"
    )
    reports_rel = str(paths.get("reports") or f"{work_rel}/reports/<slug>").strip()
    plan_path = target_root / plan_rel
    tracker_path = target_root / tracker_rel
    scope_handler = _workflow_log_handler(target_root, "scope")
    implementation_handler = _workflow_log_handler(target_root, "implementation")
    verification_handler = _workflow_log_handler(target_root, "verification")
    pending_tracking_expected = _expects_pending_tracking(target_root)
    if not plan_path.exists() or not tracker_path.exists():
        missing = []
        if not plan_path.exists():
            missing.append("workflow.plan")
        if not tracker_path.exists():
            missing.append("workflow.tracker")
        return _workflow_guidance_payload(
            phase="repair",
            state="workflow_scaffold_incomplete",
            next_required_action="repair current work, plan, and tracker pointers before continuing",
            suggested_cli="./.aegis/bin/aegis status --target-dir .",
            suggested_mcp_tool="aegis.status",
            suggested_mcp_arguments={"target_dir": "."},
            missing_gates=missing,
            copyable_repairs=[
                "Re-run kickoff only after preserving existing task evidence, or restore missing workflow files from git history."
            ],
        )

    plan_rows = _parse_plan_rows(plan_path)
    if not _plan_step_completed(plan_rows, "plan-step-scope"):
        return _workflow_guidance_payload(
            phase="scope",
            state="scope_required",
            next_required_action="log task scope before source edits",
            suggested_cli=(
                f"./.aegis/bin/aegis log --target-dir . --handler {scope_handler} "
                f"--evidence {_quote_cli(findings_rel)} --note 'Confirmed task scope before implementation' "
                "--plan-step auto --plan-status completed"
            ),
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments={
                "target_dir": ".",
                "handler": scope_handler,
                "evidence": findings_rel,
                "note": "Confirmed task scope before implementation",
                "event_class": "scope",
                "plan_step": "auto",
                "plan_status": "completed",
                "apply": True,
            },
            missing_gates=["plan.scope", "tracker.scope"],
            copyable_repairs=[
                f"./.aegis/bin/aegis log --target-dir . --handler {scope_handler} "
                f"--evidence {_quote_cli(findings_rel)} --note 'Confirmed task scope before implementation' "
                "--plan-step auto --plan-status completed"
            ],
        )

    if not _plan_step_completed(plan_rows, "plan-step-implement"):
        if pending_tracking_expected:
            suggested_cli = (
                "./.aegis/bin/aegis log --target-dir . --pending-id current "
                "--note '<past-tense implementation note>' --plan-step auto --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "pending_event_id": "current",
                "note": "<past-tense implementation note>",
                "plan_step": "auto",
                "plan_status": "completed",
                "apply": True,
            }
            copyable_repairs = [
                "Use native agent tools for the source edit.",
                suggested_cli,
            ]
            next_required_action = (
                "make the task-scoped change with native tools, then log the pending mutation"
            )
        else:
            suggested_cli = (
                f"./.aegis/bin/aegis log --target-dir . --handler {implementation_handler} "
                "--evidence '<changed-file-or-command>' --note '<past-tense implementation note>' "
                "--plan-step plan-step-implement --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "handler": implementation_handler,
                "evidence": "<changed-file-or-command>",
                "note": "<past-tense implementation note>",
                "event_class": "implementation",
                "plan_step": "plan-step-implement",
                "plan_status": "completed",
                "apply": True,
            }
            copyable_repairs = [
                "Use native agent tools for the source edit.",
                suggested_cli,
            ]
            next_required_action = "make the task-scoped change with native tools, then log explicit implementation evidence"
        return _workflow_guidance_payload(
            phase="implement",
            state="implementation_required",
            next_required_action=next_required_action,
            suggested_cli=suggested_cli,
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments=suggested_mcp_arguments,
            missing_gates=["plan.implement", "tracker.implement"],
            copyable_repairs=copyable_repairs,
            details={"pending_tracking_expected": pending_tracking_expected},
        )

    if not _plan_step_completed(plan_rows, "plan-step-verify"):
        verification_report_rel = f"{reports_rel}/task-verification.md"
        if pending_tracking_expected:
            suggested_cli = (
                f"# Save task verification under {_quote_cli(reports_rel)}/, then:\n"
                "./.aegis/bin/aegis log --target-dir . --pending-id current "
                "--note 'Recorded task-specific verification evidence' --plan-step auto --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "pending_event_id": "current",
                "note": "Recorded task-specific verification evidence",
                "plan_step": "auto",
                "plan_status": "completed",
                "apply": True,
            }
            copyable_repairs = [
                f"Save task verification under {reports_rel}/",
                "./.aegis/bin/aegis log --target-dir . --pending-id current --note 'Recorded task-specific verification evidence' --plan-step auto --plan-status completed",
            ]
        else:
            suggested_cli = (
                f"# Save task verification at {_quote_cli(verification_report_rel)}, then:\n"
                f"./.aegis/bin/aegis log --target-dir . --handler {verification_handler} "
                f"--evidence {_quote_cli(verification_report_rel)} "
                "--note 'Recorded task-specific verification evidence' "
                "--plan-step plan-step-verify --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "handler": verification_handler,
                "evidence": verification_report_rel,
                "note": "Recorded task-specific verification evidence",
                "event_class": "verification",
                "plan_step": "plan-step-verify",
                "plan_status": "completed",
                "apply": True,
            }
            copyable_repairs = [
                f"Save task verification at {verification_report_rel}",
                suggested_cli.splitlines()[-1],
            ]
        return _workflow_guidance_payload(
            phase="verify",
            state="task_verification_required",
            next_required_action="run project verification, save evidence, then log it",
            suggested_cli=suggested_cli,
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments=suggested_mcp_arguments,
            missing_gates=["plan.verify", "tracker.verify"],
            copyable_repairs=copyable_repairs,
            details={"pending_tracking_expected": pending_tracking_expected},
        )

    if not _strict_verify_passed(target_root):
        return _workflow_guidance_payload(
            phase="verify",
            state="strict_verification_required",
            next_required_action="run strict Aegis verification and log its pending event",
            suggested_cli="./.aegis/bin/aegis verify --target-dir . --strict",
            suggested_mcp_tool="aegis.verify",
            suggested_mcp_arguments={
                "target_dir": ".",
                "strict": True,
                "acknowledge_report_write": True,
            },
            missing_gates=["strict_verification"],
            copyable_repairs=[
                "./.aegis/bin/aegis verify --target-dir . --strict",
                "./.aegis/bin/aegis log --target-dir . --pending-id current --note 'Recorded strict verification evidence' --plan-step auto --plan-status completed",
            ],
        )

    if _closeout_passed(target_root):
        return _workflow_guidance_payload(
            phase="complete",
            state="closeout_passed",
            next_required_action="no workflow action required",
            suggested_cli="./.aegis/bin/aegis status --target-dir .",
            suggested_mcp_tool="aegis.status",
            suggested_mcp_arguments={"target_dir": "."},
            details={"closeout_report": AEGIS_CLOSEOUT_REPORT_REL},
        )

    return _workflow_guidance_payload(
        phase="closeout",
        state="closeout_required",
        next_required_action="run closeout dry-run/readiness, then final closeout before reporting the task complete",
        suggested_cli="./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff",
        suggested_mcp_tool="aegis.closeout_ready",
        suggested_mcp_arguments={
            "target_dir": ".",
            "update_handoff": True,
        },
        missing_gates=["closeout.readiness"],
        copyable_repairs=[
            "./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff",
            "./.aegis/bin/aegis closeout --target-dir . --update-handoff",
        ],
    )


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
    assets = _assets_for_target(target_root, _managed_assets(source, primary_agent, enabled_agents))
    manifest = _manifest_payload(
        source, target_root, primary_agent, enabled_agents, installed_at=installed_at
    )
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
    return [
        operation for operation in plan.get("operations", []) if not operation.get("safe_to_apply")
    ]


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


def _local_tasks_payload(target_root: Path) -> dict[str, Any]:
    payload = _read_json(target_root / AEGIS_LOCAL_TASKS_REL)
    if isinstance(payload, Mapping):
        tasks = payload.get("tasks")
        if isinstance(tasks, list):
            return dict(payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "next_id": 1,
        "tasks": [],
    }


def _allocate_local_task(target_root: Path, title: str, slug: str) -> dict[str, Any]:
    payload = _local_tasks_payload(target_root)
    raw_next = payload.get("next_id", 1)
    try:
        task_id = int(raw_next)
    except (TypeError, ValueError):
        task_id = 1
    if task_id < 1:
        task_id = 1
    existing_ids = {
        int(task.get("id"))
        for task in payload.get("tasks", [])
        if isinstance(task, Mapping) and str(task.get("id") or "").isdigit()
    }
    while task_id in existing_ids:
        task_id += 1
    task = {
        "id": str(task_id),
        "slug": slug,
        "title": title,
        "status": "in-progress",
        "source": "aegis-local",
        "created_at": _iso_now(),
        "updated_at": _iso_now(),
    }
    payload["next_id"] = task_id + 1
    payload.setdefault("tasks", []).append(task)
    payload["updated_at"] = _iso_now()
    _write_text(target_root, AEGIS_LOCAL_TASKS_REL, _dump_json(payload))
    return task


def _normalize_task_id(task_id: str | int) -> str:
    value = str(task_id).strip()
    if not re.fullmatch(r"\d+", value):
        raise AegisError("Aegis kickoff currently requires a numeric task id")
    return value


def _normalize_task_slug(slug: str, *, task_id: str | int) -> str:
    normalized = _slugify(slug)
    task_text = _normalize_task_id(task_id)
    for prefix in (f"task-{task_text}-", f"{task_text}-"):
        if normalized.startswith(prefix):
            stripped = normalized[len(prefix) :].strip("-")
            if stripped:
                return stripped
    return normalized


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


def _task_ids_from_text(value: str) -> list[str]:
    """Extract probable task ids from branch/title text for reconciliation only."""

    ids = {
        match.group(1)
        for match in re.finditer(r"(?:^|[^a-z0-9])task[-_\s#]*(\d+)(?:[^a-z0-9]|$)", value.lower())
    }
    return sorted(ids, key=lambda item: int(item))


def _taskmaster_tasks_by_id_from_state(
    taskmaster: TaskmasterState,
) -> dict[str, dict[str, Any]]:
    if taskmaster.state != "valid":
        return {}
    tasks: dict[str, dict[str, Any]] = {}
    for task in taskmaster.tasks:
        task_id = _numeric_task_id(task.get("id"))
        if task_id is None:
            continue
        tasks[task_id] = {
            "id": task_id,
            "title": str(task.get("title") or f"Task {task_id}").strip() or f"Task {task_id}",
            "status": str(task.get("status") or "").strip().lower() or "unknown",
            "raw": dict(task),
        }
    return tasks


def _taskmaster_tasks_by_id(target_root: Path) -> dict[str, dict[str, Any]]:
    return _taskmaster_tasks_by_id_from_state(_taskmaster_state(target_root))


def _git_ref_exists(target_root: Path, ref: str) -> bool:
    return _run_target_git(target_root, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def _validate_reconcile_base_ref(base_ref: str | None) -> str:
    requested = (base_ref or "origin/main").strip() or "origin/main"
    if requested.startswith("-") or any(ch.isspace() for ch in requested) or "\0" in requested:
        raise AegisError(
            "invalid reconcile base_ref: expected a ref-like value without whitespace, NUL bytes, or leading '-'"
        )
    return requested


def _resolve_reconcile_base_ref(target_root: Path, base_ref: str | None) -> dict[str, Any]:
    requested = _validate_reconcile_base_ref(base_ref)
    candidates = [requested]
    if requested == "origin/main":
        candidates.extend(["main", "master"])
    for candidate in dict.fromkeys(candidates):
        if _git_ref_exists(target_root, candidate):
            return {
                "requested": requested,
                "selected": candidate,
                "available": True,
                "fallback_used": candidate != requested,
            }
    return {
        "requested": requested,
        "selected": requested,
        "available": False,
        "fallback_used": False,
    }


def _git_commit_for_ref(target_root: Path, ref: str) -> str | None:
    result = _run_target_git(target_root, "rev-parse", "--verify", ref)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _reconcile_branch_kind(name: str) -> str:
    return (
        "remote"
        if "/" in name and not name.startswith(("feat/", "fix/", "docs/", "chore/", "task-"))
        else "local"
    )


def _reconcile_branch_candidates(target_root: Path) -> list[dict[str, Any]]:
    result = _run_target_git(
        target_root,
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/heads",
        "refs/remotes",
    )
    if result.returncode != 0:
        return []
    branches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in result.stdout.splitlines():
        name = raw.strip()
        if not name or name.endswith("/HEAD") or name in seen:
            continue
        seen.add(name)
        task_id = _branch_task_id(name)
        if task_id is None:
            continue
        branches.append(
            {
                "name": name,
                "kind": _reconcile_branch_kind(name),
                "task_id": task_id,
                "commit": _git_commit_for_ref(target_root, name),
            }
        )
    return sorted(branches, key=lambda branch: (int(branch["task_id"]), branch["name"]))


def _branch_merge_truth(
    target_root: Path, branch: Mapping[str, Any], base: Mapping[str, Any]
) -> dict[str, Any]:
    if not base.get("available"):
        return {
            "status": "unknown",
            "proof": "base_ref_missing",
            "confidence": "none",
            "reason": "base ref is unavailable; cannot prove ancestry",
        }
    branch_name = str(branch.get("name") or "")
    if not branch.get("commit"):
        return {
            "status": "unknown",
            "proof": "branch_ref_unresolved",
            "confidence": "none",
            "reason": "branch ref could not be resolved",
        }
    base_commit = _git_commit_for_ref(target_root, str(base["selected"]))
    if base_commit and str(branch.get("commit")) == base_commit:
        return {
            "status": "unknown",
            "proof": "branch_at_base",
            "confidence": "none",
            "reason": "branch points at the base ref; no task-specific merge proof exists yet",
        }
    result = _run_target_git(
        target_root, "merge-base", "--is-ancestor", branch_name, str(base["selected"])
    )
    if result.returncode == 0:
        return {
            "status": "merged",
            "proof": "git_ancestor",
            "confidence": "high",
            "reason": f"{branch_name} is an ancestor of {base['selected']}",
        }
    if result.returncode == 1:
        return {
            "status": "unknown",
            "proof": "git_non_ancestor",
            "confidence": "low",
            "reason": "branch tip is not an ancestor; this may be unmerged work or a squash merge",
        }
    return {
        "status": "unknown",
        "proof": "git_merge_base_error",
        "confidence": "none",
        "reason": (result.stderr or result.stdout or "git merge-base failed").strip(),
    }


def _run_gh_pr_list(target_root: Path) -> dict[str, Any]:
    gh = shutil.which("gh")
    if gh is None:
        return {"available": False, "reason": "gh executable not found", "prs": []}
    result = subprocess.run(
        [
            gh,
            "pr",
            "list",
            "--state",
            "all",
            "--limit",
            "200",
            "--json",
            "number,state,title,headRefName,baseRefName,mergedAt,url,isDraft",
        ],
        cwd=target_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return {
            "available": False,
            "reason": (result.stderr or result.stdout or "gh pr list failed").strip(),
            "prs": [],
        }
    try:
        raw_prs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"available": False, "reason": "gh pr list returned invalid JSON", "prs": []}
    if not isinstance(raw_prs, list):
        return {"available": False, "reason": "gh pr list returned non-list JSON", "prs": []}
    prs = [dict(pr) for pr in raw_prs if isinstance(pr, Mapping)]
    return {"available": True, "reason": "", "prs": prs}


def _task_ids_for_pr(pr: Mapping[str, Any]) -> list[str]:
    ids = set(_task_ids_from_text(str(pr.get("headRefName") or "")))
    ids.update(_task_ids_from_text(str(pr.get("title") or "")))
    return sorted(ids, key=lambda item: int(item))


def _prs_by_task_id(gh: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for pr in gh.get("prs", []):
        if not isinstance(pr, Mapping):
            continue
        clean = {
            "number": pr.get("number"),
            "state": str(pr.get("state") or "").upper(),
            "title": str(pr.get("title") or ""),
            "headRefName": str(pr.get("headRefName") or ""),
            "baseRefName": str(pr.get("baseRefName") or ""),
            "mergedAt": pr.get("mergedAt"),
            "url": pr.get("url"),
            "isDraft": bool(pr.get("isDraft")),
        }
        for task_id in _task_ids_for_pr(clean):
            grouped.setdefault(task_id, []).append(clean)
    return grouped


def _github_truth_for_prs(prs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    merged = [
        pr for pr in prs if str(pr.get("state") or "").upper() == "MERGED" or pr.get("mergedAt")
    ]
    if merged:
        pr = merged[0]
        return {
            "status": "merged",
            "proof": "github_pr_merged",
            "confidence": "high",
            "reason": f"PR #{pr.get('number')} is merged",
            "pr": dict(pr),
        }
    open_prs = [pr for pr in prs if str(pr.get("state") or "").upper() == "OPEN"]
    if open_prs:
        pr = open_prs[0]
        return {
            "status": "not_merged",
            "proof": "github_pr_open",
            "confidence": "high",
            "reason": f"PR #{pr.get('number')} is still open",
            "pr": dict(pr),
        }
    closed = [pr for pr in prs if str(pr.get("state") or "").upper() == "CLOSED"]
    if closed:
        pr = closed[0]
        return {
            "status": "not_merged",
            "proof": "github_pr_closed_unmerged",
            "confidence": "high",
            "reason": f"PR #{pr.get('number')} is closed without merge metadata",
            "pr": dict(pr),
        }
    return None


def _task_merge_truth(
    target_root: Path,
    branches: Sequence[Mapping[str, Any]],
    prs: Sequence[Mapping[str, Any]],
    base: Mapping[str, Any],
) -> dict[str, Any]:
    github_truth = _github_truth_for_prs(prs)
    branch_truths = [_branch_merge_truth(target_root, branch, base) for branch in branches]
    if github_truth is not None and github_truth["status"] == "merged":
        return {**github_truth, "branches": branch_truths}
    for truth in branch_truths:
        if truth["status"] == "merged":
            return {**truth, "branches": branch_truths}
    if github_truth is not None:
        return {**github_truth, "branches": branch_truths}
    if branch_truths:
        return {
            "status": "unknown",
            "proof": "git_only_non_ancestor_or_missing_base",
            "confidence": "low",
            "reason": "git ancestry did not prove merge; without GitHub metadata this may be squash-merged or unmerged",
            "branches": branch_truths,
        }
    return {
        "status": "no_evidence",
        "proof": "no_branch_or_pr",
        "confidence": "none",
        "reason": "no task branch or PR metadata was found",
        "branches": [],
    }


def _current_aegis_work_summary(target_root: Path) -> dict[str, Any] | None:
    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if not isinstance(current_work, Mapping):
        return None
    task = current_work.get("task") if isinstance(current_work.get("task"), Mapping) else {}
    branch = current_work.get("branch") if isinstance(current_work.get("branch"), Mapping) else {}
    return {
        "status": str(current_work.get("status") or ""),
        "task_id": _numeric_task_id(task.get("id")),
        "task_status": str(task.get("status") or ""),
        "task_slug": str(task.get("slug") or ""),
        "branch": str(branch.get("current") or branch.get("name") or ""),
        "closeout_passed_at": current_work.get("closeout_passed_at"),
    }


def _local_aegis_task_stubs(target_root: Path) -> list[dict[str, Any]]:
    payload = _read_json(target_root / AEGIS_LOCAL_TASKS_REL)
    if not isinstance(payload, Mapping):
        return []
    stubs: list[dict[str, Any]] = []
    for task in payload.get("tasks", []):
        if not isinstance(task, Mapping):
            continue
        task_id = _numeric_task_id(task.get("id"))
        if task_id is None:
            continue
        stubs.append(
            {
                "id": task_id,
                "title": str(task.get("title") or f"Local task {task_id}"),
                "status": str(task.get("status") or "").lower(),
                "slug": str(task.get("slug") or ""),
                "source": str(task.get("source") or "aegis-local"),
            }
        )
    return stubs


def _reconcile_finding(
    kind: str,
    *,
    severity: str,
    task_id: str,
    message: str,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "severity": severity,
        "task_id": task_id,
        "message": message,
        "evidence": dict(evidence or {}),
    }


RECONCILE_PREVIEW_BLOCKED_REASON = "report-only per Task 147 contract"
RECONCILE_PREVIEW_ROLLBACK_CONTRACT_REL = "docs/aegis/reconcile-mutation-rollback-contract.md"
RECONCILE_PREVIEW_ACTUAL_BLAST_RADIUS_AUTHORITY = (
    "No live apply-time blast-radius oracle is wired; Task 145 is test-side proof only"
)


def _reconcile_finding_proof(finding: Mapping[str, Any]) -> str:
    evidence = finding.get("evidence") if isinstance(finding.get("evidence"), Mapping) else {}
    merge_truth = (
        evidence.get("merge_truth") if isinstance(evidence.get("merge_truth"), Mapping) else {}
    )
    return str(merge_truth.get("proof") or "")


def _taskmaster_generated_task_markdown_rel(task_id: str) -> str:
    try:
        suffix = f"{int(task_id):03d}"
    except ValueError:
        suffix = task_id
    return f".taskmaster/tasks/task_{suffix}.md"


def _reconcile_preview_exclusion(kind: str, proof: str) -> tuple[str, list[str]]:
    if kind == "merged_but_not_done" and proof == "github_pr_merged":
        return (
            "excluded from first candidate preview because GitHub/squash proof needs a separate contract",
            ["separate github_pr_merged precision, blast-radius, and rollback evidence"],
        )
    if kind == "done_but_not_merged":
        return (
            "excluded from first candidate preview because done-but-not-merged repair is a different mutation class",
            ["separate not-merged status correction contract"],
        )
    if kind in {
        "multi_pr_epic_ambiguity",
        "abandoned_in_progress_branch",
        "stale_local_stub",
        "local_ad_hoc_stub",
    }:
        return (
            "manual-only by reconcile precision contract",
            ["operator review outside reconcile mutation preview"],
        )
    if proof == "git_only_non_ancestor_or_missing_base":
        return (
            "excluded because git-only non-ancestor merge truth is unknown, not drift",
            ["positive merge proof from GitHub metadata or another separate proof contract"],
        )
    return (
        "excluded from first candidate preview by Task 147 boundary",
        ["separate precision, blast-radius, rollback, and inertness evidence"],
    )


def _reconcile_mutation_candidate_preview(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for finding in findings:
        kind = str(finding.get("kind") or "")
        task_id = str(finding.get("task_id") or "")
        proof = _reconcile_finding_proof(finding)
        if kind == "merged_but_not_done" and proof == "git_ancestor":
            candidates.append(
                {
                    "record_type": "mutation_candidate",
                    "task_id": task_id,
                    "finding_kind": kind,
                    "proof": proof,
                    "executable": False,
                    "apply_path_exists": False,
                    "blocked_reason": RECONCILE_PREVIEW_BLOCKED_REASON,
                    "operator_confirmation_required": True,
                    "predicted_blast_radius_paths": [
                        ".taskmaster/tasks/tasks.json",
                        _taskmaster_generated_task_markdown_rel(task_id),
                    ],
                    "rollback_contract": {
                        "path": RECONCILE_PREVIEW_ROLLBACK_CONTRACT_REL,
                        "requires_before_snapshot": True,
                        "requires_before_audit_breadcrumb": True,
                        "requires_after_audit_breadcrumb": True,
                        "requires_rollback_verification": True,
                    },
                    "actual_blast_radius_authority": RECONCILE_PREVIEW_ACTUAL_BLAST_RADIUS_AUTHORITY,
                    "prediction_authority": "Task 147 isolated Taskmaster done-cascade inventory",
                    "candidate_boundary": "only merged_but_not_done with git_ancestor proof",
                }
            )
            continue

        reason, would_require = _reconcile_preview_exclusion(kind, proof)
        excluded.append(
            {
                "record_type": "contract_exclusion",
                "task_id": task_id,
                "class": kind,
                "proof": proof or None,
                "reason": reason,
                "would_require": would_require,
                "manual_only": kind
                in {
                    "multi_pr_epic_ambiguity",
                    "abandoned_in_progress_branch",
                    "stale_local_stub",
                    "local_ad_hoc_stub",
                },
            }
        )
    return {
        "enabled": True,
        "read_only": True,
        "executable": False,
        "apply_path_exists": False,
        "blocked_reason": RECONCILE_PREVIEW_BLOCKED_REASON,
        "candidates": candidates,
        "excluded": excluded,
        "notes": [
            "This opt-in preview is inert data for operator review, not an execution surface.",
            "A future live mutation task must add a separate apply-time side-effect oracle before claiming actual mutation-time blast-radius verification.",
        ],
    }


def reconcile(
    target_dir: str | Path,
    *,
    source_root: str | Path | None = None,
    base_ref: str | None = None,
    use_github: bool = True,
    preview_candidates: bool = False,
) -> dict[str, Any]:
    """Report Taskmaster/Aegis/git/PR drift without mutating any repository state."""

    target_root = _resolve_target_root(target_dir)
    _ensure_git_work_tree(target_root)
    taskmaster = _taskmaster_state(target_root)
    tasks = _taskmaster_tasks_by_id_from_state(taskmaster)
    branches = _reconcile_branch_candidates(target_root)
    branches_by_task: dict[str, list[dict[str, Any]]] = {}
    for branch in branches:
        branches_by_task.setdefault(str(branch["task_id"]), []).append(branch)
    gh = (
        _run_gh_pr_list(target_root)
        if use_github
        else {"available": False, "reason": "disabled", "prs": []}
    )
    prs_by_task = _prs_by_task_id(gh)
    base = _resolve_reconcile_base_ref(target_root, base_ref)
    current_work = _current_aegis_work_summary(target_root)
    active_task_id = (
        current_work.get("task_id")
        if current_work and current_work.get("status") == "in-progress"
        else None
    )
    try:
        current_branch = _current_branch(target_root)
    except AegisError:
        current_branch = ""
    current_branch_task_id = _branch_task_id(current_branch)
    local_stubs = _local_aegis_task_stubs(target_root)
    if taskmaster.state == "invalid":
        all_task_ids: list[str] = []
    else:
        all_task_ids = sorted(
            set(tasks)
            | set(branches_by_task)
            | set(prs_by_task)
            | {stub["id"] for stub in local_stubs},
            key=lambda item: int(item),
        )

    task_reports: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    if taskmaster.state == "invalid":
        findings.append(
            _reconcile_finding(
                "taskmaster_invalid",
                severity="warning",
                task_id="",
                message=(
                    f"{TASKMASTER_TASKS_REL} is present but invalid; repair Taskmaster "
                    "before deriving task/branch drift"
                ),
                evidence=taskmaster.details(),
            )
        )
    done_statuses = {"done", "completed"}
    for task_id in all_task_ids:
        task = tasks.get(task_id)
        task_status = str(task.get("status") if task else "missing")
        task_branches = branches_by_task.get(task_id, [])
        task_prs = prs_by_task.get(task_id, [])
        merge_truth = _task_merge_truth(target_root, task_branches, task_prs, base)
        report = {
            "task_id": task_id,
            "task": task,
            "taskmaster_status": task_status,
            "branches": task_branches,
            "pull_requests": task_prs,
            "merge_truth": merge_truth,
            "active_aegis_current_work": active_task_id == task_id,
        }
        task_reports.append(report)

        if task is None:
            for branch in task_branches:
                findings.append(
                    _reconcile_finding(
                        "stale_local_stub",
                        severity="warning",
                        task_id=task_id,
                        message=f"branch {branch['name']} references task {task_id}, but Taskmaster has no such task",
                        evidence={"branch": branch},
                    )
                )
            for stub in [stub for stub in local_stubs if stub["id"] == task_id]:
                findings.append(
                    _reconcile_finding(
                        "local_ad_hoc_stub",
                        severity="warning",
                        task_id=task_id,
                        message=f"Aegis local task {task_id} exists without a Taskmaster task",
                        evidence={"local_task": stub},
                    )
                )
            continue

        if len(task_prs) > 1:
            findings.append(
                _reconcile_finding(
                    "multi_pr_epic_ambiguity",
                    severity="warning",
                    task_id=task_id,
                    message=f"task {task_id} has {len(task_prs)} PR candidates; merge truth requires review",
                    evidence={"pull_requests": task_prs},
                )
            )
        if task_status not in done_statuses and merge_truth["status"] == "merged":
            findings.append(
                _reconcile_finding(
                    "merged_but_not_done",
                    severity="error",
                    task_id=task_id,
                    message=f"task {task_id} is {task_status}, but merge truth says merged",
                    evidence={"merge_truth": merge_truth},
                )
            )
        if task_status in done_statuses and merge_truth["status"] == "not_merged":
            findings.append(
                _reconcile_finding(
                    "done_but_not_merged",
                    severity="error",
                    task_id=task_id,
                    message=f"task {task_id} is {task_status}, but PR metadata says it is not merged",
                    evidence={"merge_truth": merge_truth},
                )
            )
        if (
            task_status == "in-progress"
            and task_branches
            and active_task_id != task_id
            and current_branch_task_id != task_id
        ):
            findings.append(
                _reconcile_finding(
                    "abandoned_in_progress_branch",
                    severity="warning",
                    task_id=task_id,
                    message=f"task {task_id} is in-progress with task branches but no matching active Aegis current work",
                    evidence={"branches": task_branches, "active_aegis_task_id": active_task_id},
                )
            )

    severity_counts = {
        severity: sum(1 for finding in findings if finding["severity"] == severity)
        for severity in ("error", "warning", "info")
    }
    status_value = (
        "drift"
        if severity_counts["error"]
        else "needs_review" if severity_counts["warning"] else "clean"
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": status_value,
        "read_only": True,
        "generated_at": _iso_now(),
        "target_root": target_root.as_posix(),
        "source_root": Path(source_root).resolve().as_posix() if source_root is not None else None,
        "base_ref": base,
        "github": {
            "enabled": bool(use_github),
            "available": bool(gh.get("available")),
            "reason": gh.get("reason") or "",
            "pr_count": len(gh.get("prs", [])),
        },
        "taskmaster": {
            **taskmaster.details(),
            "path": TASKMASTER_TASKS_REL,
            "available": taskmaster.state == "valid",
            "task_count": len(tasks),
        },
        "active_aegis_current_work": current_work,
        "tasks": task_reports,
        "findings": findings,
        "summary": {
            "tasks_checked": len(task_reports),
            "findings": len(findings),
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "info": severity_counts["info"],
        },
        "notes": [
            "This command is read-only and never mutates Taskmaster, Aegis state, git refs, or PRs.",
            "Git ancestry proves true merges and fast-forwards; non-ancestor branches are reported as unknown without GitHub merge metadata because squash merges are possible.",
            "GitHub PR state is optional acceleration; when unavailable, squash-ambiguous cases remain unknown instead of being reported as not merged.",
        ],
    }
    if preview_candidates:
        preview = _reconcile_mutation_candidate_preview(findings)
        report["mutation_candidate_preview"] = preview
        report["summary"]["mutation_candidates"] = len(preview["candidates"])
        report["summary"]["mutation_candidate_exclusions"] = len(preview["excluded"])
    return report


def format_reconcile_summary(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        f"Aegis reconcile: {str(report.get('status') or 'unknown').upper()}",
        f"target: {report.get('target_root')}",
        f"base_ref: {report.get('base_ref', {}).get('selected') if isinstance(report.get('base_ref'), Mapping) else None}",
        (
            "summary: "
            f"{summary.get('tasks_checked', 0)} tasks, "
            f"{summary.get('findings', 0)} findings "
            f"({summary.get('errors', 0)} errors, {summary.get('warnings', 0)} warnings, {summary.get('info', 0)} info)"
        ),
    ]
    github = report.get("github") if isinstance(report.get("github"), Mapping) else {}
    lines.append(
        "github: "
        + (
            f"available ({github.get('pr_count', 0)} PRs scanned)"
            if github.get("available")
            else f"unavailable/disabled ({github.get('reason') or 'no reason reported'})"
        )
    )
    findings = report.get("findings") if isinstance(report.get("findings"), list) else []
    if findings:
        lines.append("findings:")
        for finding in findings[:20]:
            if not isinstance(finding, Mapping):
                continue
            lines.append(
                f"- [{finding.get('severity')}] {finding.get('kind')} task {finding.get('task_id')}: "
                f"{finding.get('message')}"
            )
        if len(findings) > 20:
            lines.append(
                f"- ... {len(findings) - 20} more finding(s); rerun with --json for full detail"
            )
    else:
        lines.append("findings: none")
    preview = (
        report.get("mutation_candidate_preview")
        if isinstance(report.get("mutation_candidate_preview"), Mapping)
        else None
    )
    if preview:
        lines.append(
            "mutation_candidate_preview: "
            f"report-only, executable=false, candidates={len(preview.get('candidates', []))}, "
            f"excluded={len(preview.get('excluded', []))}"
        )
    lines.append("")
    return "\n".join(lines)


def _ensure_task_branch(
    target_root: Path, task_id: str, slug: str, *, create_branch: bool
) -> dict[str, Any]:
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
        raise AegisError(
            f"Workflow template {template_name} has unresolved variable(s): {', '.join(unresolved)}"
        )
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


def _quote_cli(value: str) -> str:
    return shlex.quote(value)


def _workflow_next_action(
    action: str,
    message: str,
    *,
    suggested_cli: str | None = None,
    suggested_mcp_tool: str | None = None,
    suggested_mcp_arguments: Mapping[str, Any] | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": action,
        "message": message,
        "native_tools_policy": (
            "Use native agent tools for source reads, edits, and project tests. "
            "Use Aegis CLI/MCP only for workflow state: install, start, kickoff for explicit external numeric task ids, log, verify, closeout."
        ),
    }
    if suggested_cli:
        payload["suggested_cli"] = suggested_cli
    if suggested_mcp_tool:
        payload["suggested_mcp"] = {
            "tool": suggested_mcp_tool,
            "arguments": dict(suggested_mcp_arguments or {}),
        }
    if details:
        payload["details"] = dict(details)
    return payload


def _post_init_next_action(install_report: Mapping[str, Any]) -> dict[str, Any]:
    client_reload = install_report.get("client_reload")
    if isinstance(client_reload, Mapping) and bool(client_reload.get("required")):
        changed_paths = [
            str(path)
            for path in client_reload.get("changed_paths", [])
            if isinstance(path, str) and path
        ]
        return _workflow_next_action(
            "restart_claude_before_mutation",
            "HARD STOP: Aegis installed or changed Claude hooks/settings. Do not edit source, run project tests, mutate Taskmaster, or call start/kickoff in this same Claude session. restart Claude before any mutation so .claude/settings.json enforcement is active.",
            suggested_cli="Restart Claude Code in this project, then run ./.aegis/bin/aegis next --target-dir .",
            suggested_mcp_tool="aegis.next",
            suggested_mcp_arguments={"target_dir": "."},
            details={
                "client_reload_required": True,
                "must_stop": True,
                "agent": client_reload.get("agent"),
                "changed_paths": changed_paths,
                "reload_reason": client_reload.get("reason"),
                "forbidden_until_reload": client_reload.get("forbidden_until_reload", []),
                "allowed_until_reload": client_reload.get("allowed_until_reload", []),
                "post_reload": "Run aegis.next, then start/kickoff tracked work before source edits.",
            },
        )

    return _workflow_next_action(
        "start_tracked_work",
        "Aegis is installed. Start local tracked work before mutating source files.",
        suggested_cli='./.aegis/bin/aegis start "<task title>"',
        suggested_mcp_tool="aegis.start",
        suggested_mcp_arguments={
            "target_dir": ".",
            "title": "<task title>",
            "apply": True,
        },
        details={
            "public_flow": "aegis init -> aegis start -> native edit -> aegis log/verify/closeout"
        },
    )


def _update_manifest_after_kickoff(target_root: Path) -> None:
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest = _read_json(manifest_path)
    if manifest is None:
        return
    capabilities = manifest.get("capabilities")
    if isinstance(capabilities, dict):
        capabilities["work_tracking"] = True
    manifest_path.write_text(_dump_json(manifest), encoding="utf-8")


def _ensure_client_reload_cleared(target_root: Path, operation: str) -> None:
    marker = _client_reload_marker(target_root)
    if marker is None:
        return
    raise AegisError(
        f"Aegis {operation} is blocked because Claude must restart before workflow mutations. "
        f"Marker: {AEGIS_CLIENT_RELOAD_REL}. Please restart Claude in this project so the installed "
        ".claude/settings.json hooks run, then call aegis.next and retry."
    )


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
    _ensure_client_reload_cleared(target_root, "kickoff")
    _ensure_git_work_tree(target_root)

    normalized_task_id = _normalize_task_id(task_id)
    normalized_slug = _normalize_task_slug(slug, task_id=normalized_task_id)
    clean_title = title.strip()
    if not clean_title:
        raise AegisError("title is required")

    existing_current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if isinstance(existing_current_work, Mapping):
        existing_status = str(existing_current_work.get("status") or "")
        existing_task = (
            existing_current_work.get("task")
            if isinstance(existing_current_work.get("task"), Mapping)
            else {}
        )
        existing_id = str(existing_task.get("id") or "")
        existing_slug = str(existing_task.get("slug") or "")
        if existing_status == "in-progress":
            if existing_id == normalized_task_id and existing_slug == normalized_slug:
                return _already_started_report(target_root, existing_current_work)
            raise AegisError(
                "Aegis current work is already in progress: "
                f"task {existing_id} {existing_slug}. Close it out before starting task {normalized_task_id} {normalized_slug}."
            )

    now = datetime.now().astimezone().replace(microsecond=0)
    selected_goals = list(goals or _default_goals())
    branch = _ensure_task_branch(
        target_root, normalized_task_id, normalized_slug, create_branch=create_branch
    )

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

    _write_text(
        target_root,
        session_rel,
        _render_workflow_template(target_root, resolved_source, "session.md", template_context),
    )
    _replace_symlink(
        target_root / "sessions" / "current", str(Path(session_rel).relative_to("sessions"))
    )
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

    _write_text(
        target_root,
        plan_rel,
        _render_workflow_template(target_root, resolved_source, "plan.md", template_context),
    )
    _replace_symlink(target_root / "plans" / "current", Path(plan_rel).name)

    work_files = {
        f"{work_rel}/TRACKER.md": _render_workflow_template(
            target_root, resolved_source, "tracker.md", template_context
        ),
        f"{work_rel}/FINDINGS.md": _render_workflow_template(
            target_root, resolved_source, "findings.md", template_context
        ),
        f"{work_rel}/DECISIONS.md": _render_workflow_template(
            target_root, resolved_source, "decisions.md", template_context
        ),
        f"{work_rel}/HANDOFF.md": _render_workflow_template(
            target_root, resolved_source, "handoff.md", template_context
        ),
        f"{work_rel}/IMPLEMENTATION.md": _render_workflow_template(
            target_root, resolved_source, "implementation.md", template_context
        ),
        f"{work_rel}/CHANGELOG.md": _render_workflow_template(
            target_root, resolved_source, "changelog.md", template_context
        ),
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

    scope_handler = _workflow_log_handler(target_root, "scope")
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
        "next_action": _workflow_next_action(
            "log_scope_before_edit",
            "Before any source edit, record scope against plan-step-scope so closeout can pass first time.",
            suggested_cli=(
                f"./.aegis/bin/aegis log --target-dir . --handler {scope_handler} "
                f"--evidence {_quote_cli(f'{work_rel}/FINDINGS.md')} "
                "--note 'Confirmed task scope before implementation' "
                "--plan-step auto --plan-status completed"
            ),
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments={
                "target_dir": ".",
                "handler": scope_handler,
                "evidence": f"{work_rel}/FINDINGS.md",
                "note": "Confirmed task scope before implementation",
                "event_class": "scope",
                "plan_step": "auto",
                "plan_status": "completed",
                "apply": True,
            },
            details={
                "scope_evidence": f"{work_rel}/FINDINGS.md",
                "required_before": "native source edits",
            },
        ),
    }
    _write_text(target_root, AEGIS_KICKOFF_REPORT_REL, _dump_json(report))
    return report


def _already_started_report(target_root: Path, current_work: Mapping[str, Any]) -> dict[str, Any]:
    task = current_work.get("task") if isinstance(current_work.get("task"), Mapping) else {}
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    work_rel = str(paths.get("work_tracking") or "")
    task_id = str(task.get("id") or "")
    slug = str(task.get("slug") or "")
    scope_handler = _workflow_log_handler(target_root, "scope")
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "already_started",
        "started_at": current_work.get("created_at"),
        "checked_at": _iso_now(),
        "target_root": str(target_root),
        "task": dict(task),
        "branch": current_work.get("branch"),
        "paths": dict(paths),
        "integrations": current_work.get("integrations", {}),
        "workflow_templates": AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT,
        "idempotent": True,
        "next_action": _workflow_next_action(
            "continue_existing_work",
            "Current work already exists; continue by logging scope, implementation, or verification evidence as appropriate.",
            suggested_cli=(
                (
                    f"./.aegis/bin/aegis log --target-dir . --handler {scope_handler} "
                    f"--evidence {_quote_cli(f'{work_rel}/FINDINGS.md')} "
                    "--note 'Confirmed task scope before implementation' "
                    "--plan-step auto --plan-status completed"
                )
                if work_rel
                else None
            ),
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments=(
                {
                    "target_dir": ".",
                    "handler": scope_handler,
                    "evidence": f"{work_rel}/FINDINGS.md",
                    "note": "Confirmed task scope before implementation",
                    "event_class": "scope",
                    "plan_step": "auto",
                    "plan_status": "completed",
                    "apply": True,
                }
                if work_rel
                else None
            ),
            details={"task": task_id, "slug": slug},
        ),
    }
    if isinstance(current_work.get("local_task"), Mapping):
        report["local_task"] = dict(current_work["local_task"])
        report["public_command"] = 'aegis start "<task title>"'
    return report


def start_local_work(
    target_dir: str | Path,
    *,
    title: str,
    slug: str | None = None,
    goals: Sequence[str] | None = None,
    create_branch: bool = True,
    source_root: str | Path | None = None,
) -> dict[str, Any]:
    """Allocate a local task id and reuse kickoff for projects without Taskmaster."""

    target_root = _resolve_target_root(target_dir)
    if not (target_root / AEGIS_MANIFEST_REL).is_file():
        raise AegisError(
            "Aegis start requires an installed .aegis/foundation-manifest.json; run aegis init first"
        )
    _ensure_client_reload_cleared(target_root, "start")
    _ensure_git_work_tree(target_root)
    clean_title = title.strip()
    if not clean_title:
        raise AegisError("task title is required")
    normalized_slug = _slugify(slug or clean_title)
    existing_current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if isinstance(existing_current_work, Mapping):
        existing_status = str(existing_current_work.get("status") or "")
        existing_task = (
            existing_current_work.get("task")
            if isinstance(existing_current_work.get("task"), Mapping)
            else {}
        )
        existing_slug = str(existing_task.get("slug") or "")
        existing_title = str(existing_task.get("title") or "")
        if existing_status == "in-progress":
            if existing_slug == normalized_slug and existing_title == clean_title:
                return _already_started_report(target_root, existing_current_work)
            raise AegisError(
                "Aegis current work is already in progress: "
                f"task {existing_task.get('id')} {existing_slug}. Close it out before starting {normalized_slug}."
            )
    taskmaster = _taskmaster_state(target_root)
    if taskmaster.state == "invalid":
        raise AegisError(
            "Taskmaster task state is present but invalid at "
            f"{TASKMASTER_TASKS_REL}; repair it before starting Aegis work. "
            f"Reason: {taskmaster.reason}. "
            "Run task-master validate-dependencies or python3 scripts/codex-task taskmaster health."
        )
    if taskmaster.state == "valid":
        raise AegisError(
            "Taskmaster is present at "
            f"{TASKMASTER_TASKS_REL}; use task-master next/show and then "
            "./.aegis/bin/aegis kickoff --target-dir . --task <id> --slug <slug> "
            "--title '<title>' instead of aegis start. Aegis local task allocation is only "
            "available when Taskmaster is absent."
        )
    local_task = _allocate_local_task(target_root, clean_title, normalized_slug)
    report = kickoff(
        target_root,
        task_id=local_task["id"],
        slug=normalized_slug,
        title=clean_title,
        goals=goals,
        create_branch=create_branch,
        source_root=source_root,
    )
    current_work_path = target_root / AEGIS_CURRENT_WORK_REL
    current_work = _read_json(current_work_path)
    if isinstance(current_work, MutableMapping):
        task_payload = current_work.get("task")
        if isinstance(task_payload, MutableMapping):
            task_payload["source"] = "aegis-local"
        current_work["local_task"] = local_task
        current_work_path.write_text(_dump_json(current_work), encoding="utf-8")
    report["local_task"] = local_task
    report["public_command"] = 'aegis start "<task title>"'
    return report


def _current_work_payload(target_root: Path) -> dict[str, Any]:
    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if current_work is None:
        raise AegisError(
            "Aegis log requires .aegis/state/current-work.json; run aegis kickoff first"
        )
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


def _normalize_log_event_class(value: str | None) -> str:
    clean = (value or "").strip().lower().replace("-", "_")
    aliases = {
        "implement": "implementation",
        "implementation": "implementation",
        "verify": "verification",
        "verification": "verification",
        "scope": "scope",
        "note": "note",
        "generic": "note",
    }
    if not clean:
        return ""
    if clean not in aliases:
        choices = ", ".join(AEGIS_LOG_EVENT_CLASSES)
        raise AegisError(f"unknown log event class: {value}; expected one of: {choices}")
    return aliases[clean]


def _infer_log_event_class(
    *,
    plan_step: str | None,
    handler: str,
    evidence: str,
    explicit_event_class: str | None = None,
) -> str:
    explicit = _normalize_log_event_class(explicit_event_class)
    if explicit:
        return explicit

    step = (plan_step or "").strip().lower()
    if "scope" in step:
        return "scope"
    if "verify" in step:
        return "verification"
    if "implement" in step:
        return "implementation"

    handler_lower = handler.lower()
    evidence_lower = evidence.lower()
    if "scope" in handler_lower:
        return "scope"
    if (
        "verify" in handler_lower
        or "verification" in handler_lower
        or evidence_lower == AEGIS_VERIFY_REPORT_REL.lower()
        or "/verification" in evidence_lower
        or evidence_lower.endswith("verification-report.json")
    ):
        return "verification"
    return "note"


def _default_log_surfaces_for_event(event_class: str) -> tuple[str, ...]:
    return AEGIS_EVENT_DEFAULT_LOG_SURFACES.get(event_class, AEGIS_DEFAULT_LOG_SURFACES)


def _normalize_log_surfaces(
    surfaces: Sequence[str] | None,
    *,
    default_surfaces: Sequence[str] = AEGIS_DEFAULT_LOG_SURFACES,
) -> tuple[str, ...]:
    selected = tuple(default_surfaces if surfaces is None else surfaces)
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
        raise AegisError(
            f"unknown log surface(s): {', '.join(unknown)}; expected one of: {choices}"
        )
    return tuple(normalized)


def _normalize_plan_status(status: str | None) -> str:
    clean = (status or "in-progress").strip().lower()
    if clean not in AEGIS_PLAN_STATUS_CHOICES:
        choices = ", ".join(sorted(AEGIS_PLAN_STATUS_CHOICES))
        raise AegisError(f"unknown plan status: {status}; expected one of: {choices}")
    return "completed" if clean == "done" else clean


AEGIS_PLAN_STEP_IDS = ("plan-step-scope", "plan-step-implement", "plan-step-verify")
AEGIS_PLAN_STEP_ROW_RE = re.compile(r"^\|\s*(plan-step-[A-Za-z0-9_-]+)\s*\|")
AEGIS_PLAN_STEP_DEFAULTS: dict[str, dict[str, str]] = {
    "plan-step-scope": {
        "description": "Confirm task scope, constraints, expected outputs, and affected files before implementation",
        "status": "in-progress",
    },
    "plan-step-implement": {
        "description": "Make only task-scoped changes and record implementation notes",
        "status": "pending",
    },
    "plan-step-verify": {
        "description": "Run verification, capture reports, and update handoff state",
        "status": "pending",
    },
    "plan-step-emergency": {
        "description": "Optional - only if a bypass is explicitly authorized",
        "evidence": "Waiver plus post-mortem note in DECISIONS.md and FINDINGS.md",
        "status": "n/a",
    },
}


def _pending_event_is_confident_implementation(pending_event: Mapping[str, Any] | None) -> bool:
    if not isinstance(pending_event, Mapping):
        return False
    event_class_value = str(pending_event.get("event_class") or pending_event.get("classification") or "")
    if event_class_value.strip().lower().replace("-", "_") == "implementation":
        return True
    tool_name = str(pending_event.get("tool") or pending_event.get("tool_name") or "")
    return tool_name in {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _infer_auto_plan_step(
    *,
    event_class: str,
    handler: str,
    evidence: str,
    pending_event: Mapping[str, Any] | None,
) -> tuple[str, str]:
    candidates: dict[str, str] = {}

    if event_class == "scope":
        candidates["plan-step-scope"] = "event_class=scope"
    elif event_class == "implementation":
        candidates["plan-step-implement"] = "event_class=implementation"
    elif event_class == "verification":
        candidates["plan-step-verify"] = "event_class=verification"

    handler_lower = handler.lower()
    evidence_lower = evidence.lower()
    if "scope" in handler_lower:
        candidates.setdefault("plan-step-scope", "handler contains scope")
    if (
        evidence_lower == AEGIS_VERIFY_REPORT_REL.lower()
        or "verify" in handler_lower
        or "verification" in handler_lower
    ):
        candidates.setdefault("plan-step-verify", "verification handler/evidence")

    if _pending_event_is_confident_implementation(pending_event):
        candidates.setdefault("plan-step-implement", "pending file mutation event")

    if len(candidates) == 1:
        step, reason = next(iter(candidates.items()))
        return step, reason

    choices = ", ".join(AEGIS_PLAN_STEP_IDS)
    if not candidates:
        raise AegisError(
            "plan-step auto could not infer a deterministic plan step; " f"pass one of: {choices}"
        )
    observed = ", ".join(f"{step} ({reason})" for step, reason in candidates.items())
    raise AegisError(
        "plan-step auto is ambiguous; "
        f"observed candidates: {observed}; pass one explicit plan step: {choices}"
    )


def _resolve_plan_step_argument(
    plan_step: str | None,
    *,
    event_class: str,
    handler: str,
    evidence: str,
    pending_event: Mapping[str, Any] | None,
) -> tuple[str, bool, str | None]:
    clean = (plan_step or "").strip()
    if not clean:
        return "", False, None
    if clean.lower() != "auto":
        return clean, False, None
    inferred, reason = _infer_auto_plan_step(
        event_class=event_class,
        handler=handler,
        evidence=evidence,
        pending_event=pending_event,
    )
    return inferred, True, reason


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


def _markdown_table_cell(value: str) -> str:
    """Render untrusted evidence text as a single markdown-table cell."""
    collapsed = re.sub(r"\s+", " ", str(value)).strip()
    return collapsed.replace("|", "&#124;")


def _canonical_plan_step_rows(current_work: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    work_rel = str(paths.get("work_tracking") or "docs/ai/work-tracking/active/<folder>")
    reports_rel = str(paths.get("reports") or f"{work_rel}/reports")
    tracker_rel = f"{work_rel}/TRACKER.md"
    rows = {step: dict(payload) for step, payload in AEGIS_PLAN_STEP_DEFAULTS.items()}
    rows["plan-step-scope"]["evidence"] = f"{work_rel}/FINDINGS.md; {work_rel}/DECISIONS.md"
    rows["plan-step-implement"]["evidence"] = f"{work_rel}/IMPLEMENTATION.md; changed files"
    rows["plan-step-verify"]["evidence"] = f"{reports_rel}/; {work_rel}/HANDOFF.md; {tracker_rel}"
    return rows


def _plan_table_row_line(step: str, row: Mapping[str, str]) -> str:
    description = _markdown_table_cell(str(row.get("description") or ""))
    evidence = _markdown_table_cell(str(row.get("evidence") or ""))
    status = str(row.get("status") or "pending").strip().lower()
    if status not in AEGIS_PLAN_STATUS_CHOICES:
        status = "pending"
    return f"| {step} | {description} | {evidence} | {status} |"


def _recover_plan_table_row(
    step: str,
    block: Sequence[str],
    *,
    canonical_rows: Mapping[str, Mapping[str, str]],
    tracker_steps: Mapping[str, str],
) -> dict[str, str]:
    canonical = canonical_rows[step]
    joined = " ".join(line.strip() for line in block if line.strip())
    cells = [cell.strip() for cell in joined.strip().strip("|").split("|")]
    status = str(canonical.get("status") or "pending").strip().lower()
    status_index: int | None = None
    for index in range(len(cells) - 1, 1, -1):
        candidate = cells[index].strip().lower()
        if candidate in AEGIS_PLAN_STATUS_CHOICES:
            status = candidate
            status_index = index
            break
    if status_index is None and tracker_steps.get(step) == "completed":
        status = "completed"
    evidence_cells = cells[2:status_index] if status_index is not None else cells[2:]
    evidence = " | ".join(cell for cell in evidence_cells if cell).strip()
    if not evidence:
        evidence = str(canonical.get("evidence") or "")
    return {
        "description": str(canonical.get("description") or ""),
        "evidence": evidence,
        "status": status,
    }


def _normalize_plan_table_text(
    text: str,
    current_work: Mapping[str, Any],
    *,
    tracker_steps: Mapping[str, str] | None = None,
) -> tuple[str, list[str]]:
    canonical_rows = _canonical_plan_step_rows(current_work)
    tracker_statuses = dict(tracker_steps or {})
    lines = text.splitlines()
    output: list[str] = []
    repaired_steps: list[str] = []
    seen_steps: set[str] = set()
    index = 0
    while index < len(lines):
        line = lines[index]
        match = AEGIS_PLAN_STEP_ROW_RE.match(line)
        if match and match.group(1) in canonical_rows:
            step = match.group(1)
            block = [line]
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if AEGIS_PLAN_STEP_ROW_RE.match(next_line) or next_line.lstrip().startswith("## "):
                    break
                block.append(next_line)
                index += 1
            repaired = _recover_plan_table_row(
                step,
                block,
                canonical_rows=canonical_rows,
                tracker_steps=tracker_statuses,
            )
            repaired_line = _plan_table_row_line(step, repaired)
            if block != [repaired_line]:
                repaired_steps.append(step)
            output.append(repaired_line)
            seen_steps.add(step)
            continue
        output.append(line)
        index += 1

    missing_steps = [step for step in canonical_rows if step not in seen_steps]
    if missing_steps:
        try:
            separator_index = next(
                idx
                for idx, value in enumerate(output)
                if value.strip() == "| --- | --- | --- | --- |"
            )
        except StopIteration:
            separator_index = -1
        if separator_index >= 0:
            insertion = separator_index + 1
            for step in missing_steps:
                output.insert(insertion, _plan_table_row_line(step, canonical_rows[step]))
                repaired_steps.append(step)
                insertion += 1
    normalized = "\n".join(output).rstrip() + "\n"
    return normalized, sorted(set(repaired_steps), key=lambda step: tuple(canonical_rows).index(step))


def _plan_table_repair_preview(
    target_root: Path,
    current_work: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(current_work, Mapping):
        return None
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    plan_rel = str(paths.get("plan") or "").strip()
    work_rel = str(paths.get("work_tracking") or "").strip()
    if not plan_rel:
        return None
    plan_path = target_root / plan_rel
    if not plan_path.is_file():
        return None
    tracker_path = target_root / work_rel / "TRACKER.md" if work_rel else None
    tracker_steps = _parse_tracker_plan_steps(tracker_path) if tracker_path is not None else {}
    original = plan_path.read_text(encoding="utf-8")
    normalized, repaired_steps = _normalize_plan_table_text(
        original,
        current_work,
        tracker_steps=tracker_steps,
    )
    if normalized == original:
        return None
    return {
        "path": plan_rel,
        "text": normalized,
        "steps": repaired_steps,
    }


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
        evidence_cell = _markdown_table_cell(evidence_rel)
        if evidence_cell not in evidence:
            evidence = f"{evidence}; {evidence_cell}" if evidence else evidence_cell
        current_status = columns[3]
        next_status = current_status
        if current_status not in {"completed", "n/a"} or plan_status == "completed":
            next_status = plan_status
        lines[index] = f"| {columns[0]} | {columns[1]} | {evidence} | {next_status} |"
        changed = True
        break
    if not changed:
        raise AegisError(f"plan step not found in current plan: {plan_step}")
    amendment_evidence = _markdown_table_cell(evidence_rel).replace("`", "'")
    amendment = f"- {timestamp} - `aegis log` updated `{plan_step}` to `{plan_status}` with evidence `{amendment_evidence}`."
    if amendment not in lines:
        try:
            heading_index = next(
                index
                for index, value in enumerate(lines)
                if value.strip() == "## Amendments & Versioning"
            )
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
    return (
        [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    )


def _degraded_events(target_root: Path) -> list[dict[str, Any]]:
    payload = _read_json(target_root / AEGIS_DEGRADED_EVENTS_REL)
    if not payload:
        return []
    events = payload.get("events")
    return (
        [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []
    )


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


def _event_matches_current_work(event: Mapping[str, Any], *, task_id: str, slug: str) -> bool:
    task = event.get("task") if isinstance(event.get("task"), Mapping) else {}
    return str(task.get("id") or "") == task_id and str(task.get("slug") or "") == slug


def _resolve_pending_tracking_event(
    events: Sequence[Mapping[str, Any]],
    pending_event_id: str,
    *,
    task_id: str,
    slug: str,
) -> Mapping[str, Any]:
    clean = pending_event_id.strip()
    if not clean:
        raise AegisError("pending event id cannot be empty")
    current_events = [
        event for event in events if _event_matches_current_work(event, task_id=task_id, slug=slug)
    ]
    if clean in AEGIS_PENDING_EVENT_SENTINELS:
        if len(current_events) != 1:
            valid = (
                ", ".join(str(event.get("id") or "unknown") for event in current_events) or "<none>"
            )
            raise AegisError(
                f"pending event sentinel '{clean}' requires exactly one current-work event; valid ids: {valid}"
            )
        return current_events[0]
    matches = [event for event in current_events if str(event.get("id") or "") == clean]
    if len(matches) == 1:
        return matches[0]
    valid = ", ".join(str(event.get("id") or "unknown") for event in current_events) or "<none>"
    raise AegisError(f"unknown pending event id: {clean}; valid ids: {valid}")


def _format_pending_tracking_for_error(events: Sequence[Mapping[str, Any]]) -> str:
    lines = []
    for event in events:
        event_id = event.get("id", "unknown")
        lines.append(
            f"- {event_id}: "
            f"H={event.get('handler', 'unknown')} "
            f"E={event.get('evidence', 'unknown')}"
        )
        location = event.get("evidence_location")
        if isinstance(location, Mapping) and location.get("display"):
            lines.append(
                f"  location: {location['display']} ({location.get('confidence', 'unknown')})"
            )
        lines.append(
            "  repair: aegis log --pending-id "
            f'{event_id} --note "<past-tense note>" '
            "--plan-step <plan-step-id> --plan-status completed"
        )
    return "\n".join(lines)


def _evidence_file_location(target_root: Path, evidence_rel: str) -> dict[str, Any] | None:
    if not evidence_rel or evidence_rel.startswith("cmd`"):
        return None
    path = Path(evidence_rel)
    resolved = path if path.is_absolute() else target_root / evidence_rel
    try:
        line_count = len(resolved.read_text(encoding="utf-8").splitlines())
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None
    line_start = 1 if line_count > 0 else None
    line_end = line_count if line_count > 0 else None
    display = evidence_rel
    if line_start is not None:
        display = (
            f"{evidence_rel}:{line_start}"
            if line_end == line_start
            else f"{evidence_rel}:{line_start}-{line_end}"
        )
    return {
        "path": evidence_rel,
        "line_start": line_start,
        "line_end": line_end,
        "line_count": line_count,
        "source": "log_file_snapshot",
        "confidence": "file_snapshot",
        "display": display,
    }


def _next_action_after_log(
    *,
    target_root: Path,
    remaining: Sequence[Mapping[str, Any]],
    normalized_plan_step: str,
    normalized_plan_status: str,
    evidence_rel: str,
    work_rel: str,
    reports_rel: str,
) -> dict[str, Any]:
    implementation_handler = _workflow_log_handler(target_root, "implementation")
    verification_handler = _workflow_log_handler(target_root, "verification")
    pending_tracking_expected = _expects_pending_tracking(target_root)
    if remaining:
        event_ids = [str(event.get("id") or "unknown") for event in remaining]
        return _workflow_next_action(
            "log_remaining_pending_event",
            "A pending mutation still exists. Log it before any further mutation or closeout.",
            suggested_cli=(
                "./.aegis/bin/aegis log --target-dir . --pending-id current "
                "--note '<past-tense note>' --plan-step <plan-step-id> --plan-status completed"
            ),
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments={
                "target_dir": ".",
                "pending_event_id": "current",
                "note": "<past-tense note>",
                "plan_step": "<plan-step-id>",
                "plan_status": "completed",
                "apply": True,
            },
            details={"remaining_pending_event_ids": event_ids},
        )
    if normalized_plan_step == "plan-step-scope" and normalized_plan_status == "completed":
        if pending_tracking_expected:
            after_mutation = (
                "./.aegis/bin/aegis log --target-dir . --pending-id current "
                "--note '<past-tense note>' --plan-step plan-step-implement --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "pending_event_id": "current",
                "note": "<past-tense implementation note>",
                "plan_step": "plan-step-implement",
                "plan_status": "completed",
                "apply": True,
            }
        else:
            after_mutation = (
                f"./.aegis/bin/aegis log --target-dir . --handler {implementation_handler} "
                "--evidence '<changed-file-or-command>' --note '<past-tense implementation note>' "
                "--plan-step plan-step-implement --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "handler": implementation_handler,
                "evidence": "<changed-file-or-command>",
                "note": "<past-tense implementation note>",
                "event_class": "implementation",
                "plan_step": "plan-step-implement",
                "plan_status": "completed",
                "apply": True,
            }
        return _workflow_next_action(
            "make_task_scoped_source_change",
            (
                "Scope is logged. Make the requested code/docs change with native tools, "
                "then log the pending event."
                if pending_tracking_expected
                else "Scope is logged. Make the requested code/docs change with native tools, then log explicit implementation evidence."
            ),
            suggested_cli=after_mutation,
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments=suggested_mcp_arguments,
            details={
                "after_mutation": after_mutation,
                "pending_tracking_expected": pending_tracking_expected,
            },
        )
    if normalized_plan_step == "plan-step-implement" and normalized_plan_status == "completed":
        verification_rel = f"{reports_rel}/task-verification.md"
        if pending_tracking_expected:
            suggested_cli = (
                "# write verification evidence, then:\n"
                "./.aegis/bin/aegis log --target-dir . --pending-id current "
                "--note 'Recorded task-specific verification evidence' "
                "--plan-step plan-step-verify --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "pending_event_id": "current",
                "note": "Recorded task-specific verification evidence",
                "plan_step": "plan-step-verify",
                "plan_status": "completed",
                "apply": True,
            }
        else:
            suggested_cli = (
                f"# write verification evidence, then:\n"
                f"./.aegis/bin/aegis log --target-dir . --handler {verification_handler} "
                f"--evidence {_quote_cli(verification_rel)} "
                "--note 'Recorded task-specific verification evidence' "
                "--plan-step plan-step-verify --plan-status completed"
            )
            suggested_mcp_arguments = {
                "target_dir": ".",
                "handler": verification_handler,
                "evidence": verification_rel,
                "note": "Recorded task-specific verification evidence",
                "event_class": "verification",
                "plan_step": "plan-step-verify",
                "plan_status": "completed",
                "apply": True,
            }
        return _workflow_next_action(
            "run_task_specific_verification",
            "Implementation is logged. Run the project's relevant verification and save a short report before strict Aegis verify.",
            suggested_cli=suggested_cli,
            suggested_mcp_tool="aegis.log",
            suggested_mcp_arguments=suggested_mcp_arguments,
            details={
                "verification_report_pattern": verification_rel,
                "pending_tracking_expected": pending_tracking_expected,
            },
        )
    if normalized_plan_step == "plan-step-verify" and normalized_plan_status == "completed":
        if evidence_rel == AEGIS_VERIFY_REPORT_REL:
            return _workflow_next_action(
                "run_closeout",
                "Strict verification is logged. Run closeout readiness/dry-run, then final closeout before reporting the task complete.",
                suggested_cli="./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff",
                suggested_mcp_tool="aegis.closeout_ready",
                suggested_mcp_arguments={
                    "target_dir": ".",
                    "update_handoff": True,
                },
            )
        return _workflow_next_action(
            "run_strict_verify",
            "Task-specific verification is logged. Run strict Aegis verification next, then log its pending event.",
            suggested_cli="./.aegis/bin/aegis verify --target-dir . --strict",
            suggested_mcp_tool="aegis.verify",
            suggested_mcp_arguments={
                "target_dir": ".",
                "strict": True,
                "acknowledge_report_write": True,
            },
        )
    return _workflow_next_action(
        "continue_workflow",
        "Progress was logged. Check readiness and pending tracking before the next mutation.",
        suggested_cli="bash .claude/scripts/readiness.sh --quick --root .",
    )


def log_work(
    target_dir: str | Path,
    *,
    handler: str | None = None,
    evidence: str | None = None,
    note: str,
    surfaces: Sequence[str] | None = None,
    plan_step: str | None = None,
    plan_status: str | None = "in-progress",
    event_class: str | None = None,
    pending_event_id: str | None = None,
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
    clean_note = note.strip()
    if not clean_note:
        raise AegisError("note is required")

    session_rel = str(paths.get("session") or "")
    plan_rel = str(paths.get("plan") or "")
    work_rel = str(paths.get("work_tracking") or "")
    reports_rel = str(paths.get("reports") or f"{work_rel}/reports/<slug>")
    if not session_rel or not plan_rel or not work_rel:
        raise AegisError("current work paths are incomplete; rerun aegis kickoff")
    session_path = target_root / session_rel
    plan_path = target_root / plan_rel
    tracker_path = target_root / work_rel / "TRACKER.md"

    pending_before = _pending_tracking_events(target_root)
    resolved_pending_event: Mapping[str, Any] | None = None
    if pending_event_id:
        resolved_pending_event = _resolve_pending_tracking_event(
            pending_before,
            pending_event_id,
            task_id=task_id,
            slug=slug,
        )
        handler = str(resolved_pending_event.get("handler") or "")
        evidence = str(resolved_pending_event.get("evidence") or "")

    clean_handler = (handler or "").strip()
    if not clean_handler:
        raise AegisError("handler is required unless --pending-id identifies a pending event")
    evidence_rel = _normalize_evidence(target_root, evidence or "")
    pending_location = (
        resolved_pending_event.get("evidence_location")
        if isinstance(resolved_pending_event, Mapping)
        else None
    )
    evidence_location = (
        dict(pending_location)
        if isinstance(pending_location, Mapping)
        else _evidence_file_location(target_root, evidence_rel)
    )
    normalized_event_class = _infer_log_event_class(
        plan_step="" if (plan_step or "").strip().lower() == "auto" else (plan_step or "").strip(),
        handler=clean_handler,
        evidence=evidence_rel,
        explicit_event_class=event_class,
    )
    if normalized_event_class == "note" and _pending_event_is_confident_implementation(resolved_pending_event):
        normalized_event_class = "implementation"
    normalized_plan_step, plan_step_inferred, plan_inference_reason = _resolve_plan_step_argument(
        plan_step,
        event_class=normalized_event_class,
        handler=clean_handler,
        evidence=evidence_rel,
        pending_event=resolved_pending_event,
    )
    normalized_plan_status = _normalize_plan_status(plan_status) if normalized_plan_step else ""
    log_surfaces = _normalize_log_surfaces(
        surfaces,
        default_surfaces=_default_log_surfaces_for_event(normalized_event_class),
    )

    now = datetime.now().astimezone().replace(microsecond=0)
    session_value = now.strftime("%Y%m%d")
    date_value = now.strftime("%Y-%m-%d")
    work_context = f"task{task_id}-{slug}"
    swhe = f"[S:{session_value}|W:{work_context}|H:{clean_handler}|E:{evidence_rel}]"
    session_line = f"- **[{now.strftime('%H:%M')}]** - {swhe} {clean_note}"
    tracker_line = f"- **{now.strftime('%Y-%m-%d %H:%M %Z').strip()}** - {swhe} {clean_note}"

    existing_session_text = _read_text_or_empty(session_path)
    existing_tracker_text = _read_text_or_empty(tracker_path)
    already_logged = swhe in existing_session_text and swhe in existing_tracker_text

    if resolved_pending_event is not None:
        resolved_id = str(resolved_pending_event.get("id") or "")
        cleared = [event for event in pending_before if str(event.get("id") or "") == resolved_id]
    else:
        cleared = [
            event for event in pending_before if str(event.get("evidence") or "") == evidence_rel
        ]
    if pending_before and not cleared:
        pending_summary = _format_pending_tracking_for_error(pending_before)
        raise AegisError(
            "aegis log evidence does not match any pending S:W:H:E tracking event. "
            "Log the pending evidence first or inspect .aegis/state/pending-tracking.json.\n"
            f"Pending tracking:\n{pending_summary}"
        )
    if already_logged and not pending_before:
        updated_surfaces: dict[str, str] = {}
        replay_line = f"- **{now.strftime('%Y-%m-%d %H:%M %Z').strip()}** - {swhe} {clean_note}"
        for surface in log_surfaces:
            rel_path = f"{work_rel}/{AEGIS_LOG_SURFACES[surface]}"
            surface_path = target_root / rel_path
            if swhe in _read_text_or_empty(surface_path):
                continue
            _append_progress_entry(surface_path, "## Progress Log", replay_line)
            updated_surfaces[surface] = rel_path

        plan_updated = False
        if normalized_plan_step:
            plan_rows = _parse_plan_rows(plan_path)
            row = plan_rows.get(normalized_plan_step)
            evidence_text = str(row.get("evidence") or "") if isinstance(row, Mapping) else ""
            row_status = str(row.get("status") or "") if isinstance(row, Mapping) else ""
            evidence_cell = _markdown_table_cell(evidence_rel)
            needs_plan_update = evidence_cell not in evidence_text or (
                normalized_plan_status == "completed" and row_status not in {"completed", "done"}
            )
            if needs_plan_update:
                plan_updated = _update_plan_table(
                    plan_path,
                    plan_step=normalized_plan_step,
                    plan_status=normalized_plan_status,
                    evidence_rel=evidence_rel,
                    timestamp=date_value,
                )
                _update_tracker_plan_step(
                    tracker_path, normalized_plan_step, normalized_plan_status
                )

        if updated_surfaces or plan_updated:
            _update_tracker_timestamp(tracker_path, date_value)
            current_work["updated_at"] = _iso_now()
            _write_text(target_root, AEGIS_CURRENT_WORK_REL, _dump_json(current_work))

        return {
            "schema_version": SCHEMA_VERSION,
            "status": "logged" if (updated_surfaces or plan_updated) else "already_logged",
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
                "event_class": normalized_event_class,
                "evidence_location": evidence_location,
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
                "inferred": plan_step_inferred,
                "inference_reason": plan_inference_reason,
                "strict_verification_evidence": (
                    evidence_rel == AEGIS_VERIFY_REPORT_REL
                    and normalized_plan_step == "plan-step-verify"
                ),
            },
            "pending": {
                "cleared": 0,
                "remaining": 0,
                "cleared_events": [],
                "pending_event_id": pending_event_id or None,
            },
            "idempotent": not (updated_surfaces or plan_updated),
            "replay_completed_missing_surfaces": bool(updated_surfaces or plan_updated),
            "next_action": _next_action_after_log(
                target_root=target_root,
                remaining=[],
                normalized_plan_step=normalized_plan_step,
                normalized_plan_status=normalized_plan_status,
                evidence_rel=evidence_rel,
                work_rel=work_rel,
                reports_rel=reports_rel,
            ),
        }

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

    if resolved_pending_event is not None:
        resolved_id = str(resolved_pending_event.get("id") or "")
        remaining = [event for event in pending_before if str(event.get("id") or "") != resolved_id]
    else:
        remaining = [
            event for event in pending_before if str(event.get("evidence") or "") != evidence_rel
        ]
    _write_pending_tracking_events(target_root, remaining)

    current_work["updated_at"] = _iso_now()
    _write_text(target_root, AEGIS_CURRENT_WORK_REL, _dump_json(current_work))

    entry_payload: dict[str, Any] = {
        "session": session_line,
        "tracker": tracker_line,
        "s": session_value,
        "w": work_context,
        "h": clean_handler,
        "e": evidence_rel,
        "note": clean_note,
        "event_class": normalized_event_class,
    }
    if evidence_location:
        entry_payload["evidence_location"] = evidence_location

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "logged",
        "logged_at": _iso_now(),
        "target_root": str(target_root),
        "entry": entry_payload,
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
            "inferred": plan_step_inferred,
            "inference_reason": plan_inference_reason,
            "strict_verification_evidence": (
                evidence_rel == AEGIS_VERIFY_REPORT_REL
                and normalized_plan_step == "plan-step-verify"
            ),
        },
        "pending": {
            "cleared": len(cleared),
            "remaining": len(remaining),
            "cleared_events": cleared,
            "pending_event_id": pending_event_id or None,
        },
        "next_action": _next_action_after_log(
            target_root=target_root,
            remaining=remaining,
            normalized_plan_step=normalized_plan_step,
            normalized_plan_status=normalized_plan_status,
            evidence_rel=evidence_rel,
            work_rel=work_rel,
            reports_rel=reports_rel,
        ),
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
    assets = _assets_for_target(target_root, _managed_assets(source, primary_agent, enabled_agents))
    manifest = _manifest_payload(
        source, target_root, primary_agent, enabled_agents, installed_at=installed_at
    )
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
        client_reload = _client_reload_report(target_root, plan, enabled_agents)
        if client_reload.get("required") and not client_reload.get("pending_marker"):
            _write_client_reload_marker(target_root, client_reload)
            client_reload = _client_reload_report(target_root, plan, enabled_agents)
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": "applied",
            "applied_at": _iso_now(),
            "target_root": str(target_root),
            "plan": plan,
            "manifest_path": AEGIS_MANIFEST_REL,
            "client_reload": client_reload,
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


def initialize_project(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    profile: str = PROFILE_GENERIC,
    primary_agent: str = "claude",
    agents: Sequence[str] | None = None,
    verify_after_install: bool = True,
) -> dict[str, Any]:
    """Install Aegis into a project using public task-master-init style defaults."""

    target_root = _resolve_target_root(target_dir)
    target_root.mkdir(parents=True, exist_ok=True)
    selected_agents = list(agents or [primary_agent])
    enabled_agents = _enabled_agents(primary_agent, selected_agents)
    inspect_before = inspect_project(
        target_root,
        profile=profile,
        source_root=source_root,
        default_primary_agent=primary_agent,
        default_agents=enabled_agents,
    )
    plan = plan_install(
        target_root,
        source_root=source_root,
        profile=profile,
        primary_agent=primary_agent,
        agents=enabled_agents,
        mode="apply",
        apply_confirmed=True,
    )
    install_report = install(
        target_root,
        source_root=source_root,
        profile=profile,
        primary_agent=primary_agent,
        agents=enabled_agents,
        apply=True,
    )
    verification: dict[str, Any] | None = None
    status_value = str(install_report.get("status") or "unknown")
    if status_value == "applied" and verify_after_install:
        verification = verify(
            target_root,
            source_root=source_root,
            default_primary_agent=primary_agent,
            default_agents=enabled_agents,
        )
        if verification.get("status") == "failed":
            status_value = "failed"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "initialized" if status_value == "applied" else status_value,
        "initialized_at": _iso_now(),
        "target_root": str(target_root),
        "profile": profile,
        "agent_selection": {
            "source": "public_defaults",
            "primary_agent": primary_agent,
            "enabled_agents": list(enabled_agents),
        },
        "public_commands": {
            "status": "aegis status",
            "next": "aegis next",
            "start": 'aegis start "<task title>"',
            "verify": "aegis verify --strict",
            "closeout": "aegis closeout --update-handoff",
        },
        "inspect_before": inspect_before,
        "plan": plan,
        "install": install_report,
        "verification": verification,
        "reports": {
            "plan_json": AEGIS_PLAN_REPORT_REL,
            "install_json": AEGIS_INSTALL_REPORT_REL,
            "verification_json": AEGIS_VERIFY_REPORT_REL if verification is not None else None,
        },
        "next_action": _post_init_next_action(install_report),
    }
    return payload


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
    message = (
        "all manifest managed files exist"
        if passed
        else "manifest managed files missing or invalid"
    )
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


def _strict_current_work_checks(
    target_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
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
    work_status = str(current_work.get("status") or "").strip()
    active_payload = work_status == "in-progress"
    completed_payload = work_status == "completed" and bool(current_work.get("closeout_passed_at"))
    valid_payload = (
        (active_payload or completed_payload)
        and bool(task_id)
        and bool(task_slug)
        and not missing_path_keys
    )
    status_message = (
        "current work payload is active and complete"
        if active_payload
        else (
            "current work payload is completed and closeout-passed"
            if completed_payload
            else "current work payload is incomplete"
        )
    )
    checks = [
        _strict_check(
            "workflow.current_work",
            category="workflow",
            required=True,
            passed=valid_payload,
            message=status_message,
            details={
                "task": task,
                "status": work_status,
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
                    message=(
                        "branch task id matches current work"
                        if branch_matches
                        else "branch task id does not match current work"
                    ),
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

    plan_rel = str(paths.get("plan") or "").strip()
    if plan_rel and (target_root / plan_rel).is_file():
        plan_rows = _parse_plan_rows(target_root / plan_rel)
        expected_rows = _canonical_plan_step_rows(current_work)
        missing_steps = [step for step in expected_rows if step not in plan_rows]
        malformed_steps = [
            step
            for step, row in plan_rows.items()
            if str(step).startswith("plan-step-") and isinstance(row, Mapping) and row.get("malformed")
        ]
        checks.append(
            _strict_check(
                "workflow.plan_table",
                category="workflow",
                required=True,
                passed=not missing_steps and not malformed_steps,
                message=(
                    "active plan table is parseable"
                    if not missing_steps and not malformed_steps
                    else "active plan table has malformed or missing rows"
                ),
                details={
                    "path": plan_rel,
                    "missing_steps": missing_steps,
                    "malformed_steps": malformed_steps,
                },
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
                message=(
                    "all work-tracking surfaces exist"
                    if not missing_surfaces
                    else "work-tracking surfaces missing"
                ),
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
        message=(
            "pending tracking queue empty"
            if event_count == 0
            else "pending tracking queue has unlogged mutation events"
        ),
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
        rel_path for rel_path in CLAUDE_REQUIRED_FILES if not (target_root / rel_path).is_file()
    ]
    checks = [
        _strict_check(
            "claude.required_files",
            category="claude",
            required=True,
            passed=not missing_required_files,
            message=(
                "all Claude required files exist"
                if not missing_required_files
                else "Claude required files missing"
            ),
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
        str(result.get("gate_id")) for result in hook_results if result.get("status") != "pass"
    ]
    checks.append(
        _strict_check(
            "claude.hooks_registered",
            category="claude",
            required=True,
            passed=len(hook_results) == len(hook_gate_ids) and not failed_hooks,
            message=(
                "Claude hook registrations are present"
                if not failed_hooks and len(hook_results) == len(hook_gate_ids)
                else "Claude hook registrations are missing or invalid"
            ),
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


def _strict_integration_checks(
    target_root: Path, current_work: Mapping[str, Any] | None
) -> list[dict[str, Any]]:
    integrations = (
        current_work.get("integrations")
        if isinstance(current_work, Mapping)
        and isinstance(current_work.get("integrations"), Mapping)
        else {}
    )
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
                    else (
                        f"{name} integration is optional and absent"
                        if not required
                        else f"{name} integration is required but absent"
                    )
                ),
                details={
                    "path": rel_path,
                    "required": required,
                    "detected": detected,
                },
            )
        )
    return checks


def _strict_verification_checks(
    target_root: Path, manifest: Mapping[str, Any]
) -> list[dict[str, Any]]:
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


def _manifest_primary_agent(manifest: Mapping[str, Any]) -> str:
    primary = str(manifest.get("primary_agent") or "claude")
    return primary if primary in PRIMARY_AGENT_CHOICES else "claude"


def _manifest_enabled_agents(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    agents = manifest.get("agents")
    if not isinstance(agents, Mapping):
        return ("claude",)
    enabled = [
        name
        for name, payload in agents.items()
        if name in AGENT_CHOICES and isinstance(payload, Mapping) and payload.get("enabled") is True
    ]
    return tuple(enabled or ("claude",))


def _doctor_summary(checks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(checks)
    failed_required = sum(
        1 for check in checks if check.get("required") is True and check.get("status") == "fail"
    )
    warnings = sum(
        1 for check in checks if check.get("required") is False and check.get("status") == "fail"
    )
    return {
        "total": total,
        "failed_required": failed_required,
        "warnings": warnings,
    }


def _doctor_action(
    action_id: str,
    *,
    kind: str,
    path: str,
    reason: str,
    safe: bool = True,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    action: dict[str, Any] = {
        "id": action_id,
        "kind": kind,
        "path": path,
        "reason": reason,
        "safe": safe,
    }
    if details:
        action["details"] = dict(details)
    return action


def _doctor_manifest_assets(
    target_root: Path,
    source_root: Path,
    manifest: Mapping[str, Any],
) -> dict[str, Asset]:
    primary_agent = _manifest_primary_agent(manifest)
    enabled_agents = _manifest_enabled_agents(manifest)
    assets = _assets_for_target(
        target_root,
        _managed_assets(source_root, primary_agent, enabled_agents),
    )
    return {asset.path: asset for asset in assets}


def _current_work_pointer_actions(
    target_root: Path,
    current_work: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(current_work, Mapping):
        return []
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    actions: list[dict[str, Any]] = []
    for key, target_key in (("session_current", "session"), ("plan_current", "plan")):
        link_rel = str(paths.get(key) or "").strip()
        target_rel = str(paths.get(target_key) or "").strip()
        if not link_rel or not target_rel:
            continue
        link = target_root / link_rel
        target = target_root / target_rel
        if not target.is_file():
            continue
        desired = os.path.relpath(target, start=link.parent)
        needs_repair = False
        if not link.exists() and not link.is_symlink():
            needs_repair = True
        elif link.is_symlink():
            try:
                needs_repair = os.readlink(link) != desired
            except OSError:
                needs_repair = True
        else:
            needs_repair = True
        if needs_repair:
            actions.append(
                _doctor_action(
                    f"workflow.recreate_{key}",
                    kind="recreate_symlink",
                    path=link_rel,
                    reason=f"{link_rel} should point at {target_rel}",
                    details={"target": target_rel, "link_target": desired},
                )
            )
    reports_rel = str(paths.get("reports") or "").strip()
    if reports_rel and not (target_root / reports_rel).is_dir():
        actions.append(
            _doctor_action(
                "workflow.ensure_reports_dir",
                kind="ensure_directory",
                path=reports_rel,
                reason="active reports directory is missing",
            )
        )
    return actions


def _completed_closeout_action(
    target_root: Path,
    current_work: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(current_work, Mapping):
        return None
    status_value = str(current_work.get("status") or "")
    if status_value == "completed" and current_work.get("closeout_passed_at"):
        return None
    closeout_report = _read_json(target_root / AEGIS_CLOSEOUT_REPORT_REL)
    if not isinstance(closeout_report, Mapping) or closeout_report.get("status") != "passed":
        return None
    return _doctor_action(
        "workflow.normalize_completed_closeout",
        kind="normalize_completed_closeout",
        path=AEGIS_CURRENT_WORK_REL,
        reason="closeout report passed but current-work is not marked completed",
        details={"closeout_report": AEGIS_CLOSEOUT_REPORT_REL},
    )


def _doctor_repair_actions(
    target_root: Path,
    source_root: Path,
    manifest: Mapping[str, Any] | None,
    current_work: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if isinstance(manifest, Mapping):
        asset_map = _doctor_manifest_assets(target_root, source_root, manifest)
        managed_files = manifest.get("managed_files")
        if isinstance(managed_files, list):
            for item in managed_files:
                if not isinstance(item, Mapping):
                    continue
                rel_path = str(item.get("path") or "").strip()
                if not rel_path:
                    continue
                target = target_root / rel_path
                asset = asset_map.get(rel_path)
                if not target.exists() and asset is not None:
                    actions.append(
                        _doctor_action(
                            f"managed.restore:{rel_path}",
                            kind="restore_managed_file",
                            path=rel_path,
                            reason="manifest-managed file is missing",
                            details={"executable": asset.executable, "managed_kind": asset.kind},
                        )
                    )
                elif target.is_dir():
                    actions.append(
                        _doctor_action(
                            f"managed.manual:{rel_path}",
                            kind="manual_review",
                            path=rel_path,
                            reason="manifest-managed path is a directory, not a file",
                            safe=False,
                        )
                    )
        shim = target_root / AEGIS_LOCAL_BIN_REL
        if shim.is_file() and not os.access(shim, os.X_OK):
            actions.append(
                _doctor_action(
                    "runtime.chmod_local_cli_shim",
                    kind="chmod_executable",
                    path=AEGIS_LOCAL_BIN_REL,
                    reason="project-local Aegis CLI shim is not executable",
                )
            )
    actions.extend(_current_work_pointer_actions(target_root, current_work))
    plan_table_repair = _plan_table_repair_preview(target_root, current_work)
    if plan_table_repair is not None:
        actions.append(
            _doctor_action(
                "workflow.normalize_plan_table",
                kind="normalize_plan_table",
                path=str(plan_table_repair["path"]),
                reason="active plan table has malformed or unsafe markdown rows",
                details={"steps": plan_table_repair["steps"]},
            )
        )
    completed_action = _completed_closeout_action(target_root, current_work)
    if completed_action is not None:
        actions.append(completed_action)
    return actions


def _classify_doctor_state(
    *,
    manifest: Mapping[str, Any] | None,
    current_work: Mapping[str, Any] | None,
    checks: Sequence[Mapping[str, Any]],
    repair_actions: Sequence[Mapping[str, Any]],
) -> tuple[str, str]:
    if manifest is None:
        return "not_installed", "failed"
    if not isinstance(current_work, Mapping):
        return "installed_no_current_work", (
            "healthy" if not _doctor_summary(checks)["failed_required"] else "repairable"
        )
    pending_check = next(
        (check for check in checks if check.get("id") == "mutation.pending_tracking_empty"),
        None,
    )
    if isinstance(pending_check, Mapping) and pending_check.get("status") == "fail":
        return "pending_tracking", "blocked"
    status_value = str(current_work.get("status") or "")
    if status_value == "completed" and current_work.get("closeout_passed_at"):
        summary = _doctor_summary(checks)
        if summary["failed_required"]:
            return "completed_closeout", "repairable"
        return "completed_closeout", "degraded" if summary["warnings"] else "healthy"
    workflow_failed = any(
        check.get("category") == "workflow" and check.get("status") == "fail" for check in checks
    )
    if workflow_failed:
        return "workflow_scaffold_incomplete", "repairable" if repair_actions else "failed"
    summary = _doctor_summary(checks)
    if summary["failed_required"]:
        return "installed_with_failures", "repairable" if repair_actions else "failed"
    if summary["warnings"]:
        return "in_progress_ready", "degraded"
    return "in_progress_ready", "healthy"


def doctor(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    default_primary_agent: str = "claude",
    default_agents: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Diagnose installed Aegis state without mutating the target repository."""

    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest = _read_json(manifest_path)
    checks: list[dict[str, Any]] = []
    current_work: dict[str, Any] | None = None

    if manifest is None:
        checks.append(
            _strict_check(
                "aegis.manifest",
                category="manifest",
                required=True,
                passed=False,
                message="Aegis manifest missing or invalid JSON",
                details={"path": AEGIS_MANIFEST_REL},
            )
        )
    else:
        try:
            _validate_with_schema(source, "foundation-manifest.schema.json", manifest)
            checks.append(
                _strict_check(
                    "aegis.manifest",
                    category="manifest",
                    required=True,
                    passed=True,
                    message="Aegis manifest is valid",
                    details={"path": AEGIS_MANIFEST_REL},
                )
            )
        except ValidationError as exc:
            checks.append(
                _strict_check(
                    "aegis.manifest",
                    category="manifest",
                    required=True,
                    passed=False,
                    message=f"Aegis manifest schema validation failed: {exc.message}",
                    details={"path": AEGIS_MANIFEST_REL, "schema_path": list(exc.schema_path)},
                )
            )
        strict_checks = _strict_verification_checks(target_root, manifest)
        checks.extend(strict_checks)
        current_work_path = target_root / AEGIS_CURRENT_WORK_REL
        current_work = _read_json(current_work_path)
        if not current_work_path.exists():
            for check in checks:
                if check.get("id") == "workflow.current_work":
                    check["required"] = False
                    check["status"] = "pass"
                    check["message"] = (
                        "no active current work; run aegis start or aegis kickoff before source edits"
                    )

    repair_actions = _doctor_repair_actions(target_root, source, manifest, current_work)
    active_root = target_root / "docs/ai/work-tracking/active"
    active_folders = sorted(
        path.relative_to(target_root).as_posix()
        for path in active_root.glob("*-ACTIVE")
        if path.is_dir()
    )
    current_work_rel = ""
    if isinstance(current_work, Mapping):
        paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
        current_work_rel = str(paths.get("work_tracking") or "").strip()
    stale_active = [path for path in active_folders if path != current_work_rel]
    if stale_active:
        checks.append(
            _strict_check(
                "workflow.stale_active_folders",
                category="workflow",
                required=False,
                passed=False,
                message="non-current ACTIVE work-tracking folders exist",
                details={"folders": stale_active, "current": current_work_rel},
            )
        )
    degraded_events = _degraded_events(target_root)
    unacknowledged_degraded = [
        event
        for event in degraded_events
        if not event.get("acknowledged_at") and not event.get("resolved_at")
    ]
    checks.append(
        _strict_check(
            "runtime.degraded_events_acknowledged",
            category="runtime",
            required=False,
            passed=not unacknowledged_degraded,
            message=(
                "no unacknowledged degraded gate events"
                if not unacknowledged_degraded
                else "unacknowledged degraded gate events require operator review"
            ),
            details={
                "path": AEGIS_DEGRADED_EVENTS_REL,
                "total": len(degraded_events),
                "unacknowledged": unacknowledged_degraded,
            },
        )
    )

    current_state, status_value = _classify_doctor_state(
        manifest=manifest,
        current_work=current_work,
        checks=checks,
        repair_actions=repair_actions,
    )
    safe_actions = [action for action in repair_actions if action.get("safe") is True]
    manual_actions = [action for action in repair_actions if action.get("safe") is not True]
    return {
        "schema_version": SCHEMA_VERSION,
        "checked_at": _iso_now(),
        "target_root": str(target_root),
        "read_only": True,
        "status": status_value,
        "current_state": current_state,
        "checks": checks,
        "summary": _doctor_summary(checks),
        "repair_plan": {
            "available": bool(repair_actions),
            "safe": len(safe_actions),
            "manual_review": len(manual_actions),
            "actions": repair_actions,
            "apply_command": "aegis repair --apply" if safe_actions else None,
        },
        "next_action": next_action(
            target_root,
            source_root=source,
            default_primary_agent=default_primary_agent,
            default_agents=default_agents,
        ),
    }


def _apply_repair_action(
    target_root: Path,
    source_root: Path,
    manifest: Mapping[str, Any] | None,
    action: Mapping[str, Any],
) -> dict[str, Any]:
    kind = str(action.get("kind") or "")
    rel_path = str(action.get("path") or "")
    target = target_root / rel_path
    if action.get("safe") is not True:
        return {"id": action.get("id"), "status": "skipped", "reason": "manual review action"}
    if kind == "restore_managed_file":
        if not isinstance(manifest, Mapping):
            return {"id": action.get("id"), "status": "skipped", "reason": "manifest unavailable"}
        asset = _doctor_manifest_assets(target_root, source_root, manifest).get(rel_path)
        if asset is None:
            return {
                "id": action.get("id"),
                "status": "skipped",
                "reason": "managed asset unavailable",
            }
        if target.exists():
            return {"id": action.get("id"), "status": "skipped", "reason": "path already exists"}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(asset.content)
        if asset.executable:
            target.chmod(target.stat().st_mode | 0o755)
        return {"id": action.get("id"), "status": "applied", "path": rel_path}
    if kind == "chmod_executable":
        if not target.is_file():
            return {"id": action.get("id"), "status": "skipped", "reason": "file missing"}
        target.chmod(target.stat().st_mode | 0o755)
        return {"id": action.get("id"), "status": "applied", "path": rel_path}
    if kind == "ensure_directory":
        target.mkdir(parents=True, exist_ok=True)
        return {"id": action.get("id"), "status": "applied", "path": rel_path}
    if kind == "recreate_symlink":
        details = action.get("details") if isinstance(action.get("details"), Mapping) else {}
        target_rel = str(details.get("target") or "")
        link_target = str(details.get("link_target") or "")
        if not target_rel or not (target_root / target_rel).is_file():
            return {"id": action.get("id"), "status": "skipped", "reason": "target file missing"}
        if target.exists() and not target.is_symlink():
            return {
                "id": action.get("id"),
                "status": "skipped",
                "reason": "non-symlink path exists",
            }
        if target.is_symlink():
            target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(
            link_target or os.path.relpath(target_root / target_rel, start=target.parent)
        )
        return {"id": action.get("id"), "status": "applied", "path": rel_path}
    if kind == "normalize_completed_closeout":
        current_path = target_root / AEGIS_CURRENT_WORK_REL
        current_work = _read_json(current_path)
        closeout_report = _read_json(target_root / AEGIS_CLOSEOUT_REPORT_REL)
        if (
            current_work is None
            or closeout_report is None
            or closeout_report.get("status") != "passed"
        ):
            return {
                "id": action.get("id"),
                "status": "skipped",
                "reason": "completed closeout evidence unavailable",
            }
        current_work["status"] = "completed"
        task = (
            current_work.get("task")
            if isinstance(current_work.get("task"), MutableMapping)
            else None
        )
        if task is not None:
            task["status"] = "completed"
        current_work["closeout_passed_at"] = str(closeout_report.get("checked_at") or _iso_now())
        current_work["closeout_report"] = AEGIS_CLOSEOUT_REPORT_REL
        current_path.write_text(_dump_json(current_work), encoding="utf-8")
        return {"id": action.get("id"), "status": "applied", "path": rel_path}
    if kind == "normalize_plan_table":
        current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
        preview = _plan_table_repair_preview(target_root, current_work)
        if preview is None:
            return {"id": action.get("id"), "status": "skipped", "reason": "plan table already clean"}
        plan_path = target_root / str(preview["path"])
        plan_path.write_text(str(preview["text"]), encoding="utf-8")
        return {
            "id": action.get("id"),
            "status": "applied",
            "path": str(preview["path"]),
            "details": {"steps": list(preview["steps"])},
        }
    return {
        "id": action.get("id"),
        "status": "skipped",
        "reason": f"unsupported repair kind: {kind}",
    }


def repair(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    apply: bool = False,
) -> dict[str, Any]:
    """Preview or apply safe Aegis state repairs."""

    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    preflight = doctor(target_root, source_root=source)
    actions = list(preflight.get("repair_plan", {}).get("actions") or [])
    safe_actions = [
        action for action in actions if isinstance(action, Mapping) and action.get("safe") is True
    ]
    if not apply:
        return {
            "schema_version": SCHEMA_VERSION,
            "checked_at": _iso_now(),
            "target_root": str(target_root),
            "read_only": True,
            "status": "preview",
            "current_state": preflight.get("current_state"),
            "repair_plan": preflight.get("repair_plan"),
            "applied": [],
            "report_written": False,
        }
    if preflight.get("current_state") == "pending_tracking":
        return {
            "schema_version": SCHEMA_VERSION,
            "checked_at": _iso_now(),
            "target_root": str(target_root),
            "read_only": False,
            "status": "blocked",
            "reason": "pending S:W:H:E tracking must be logged before repair can mutate workflow state",
            "current_state": preflight.get("current_state"),
            "repair_plan": preflight.get("repair_plan"),
            "applied": [],
            "report_written": False,
            "next_action": preflight.get("next_action"),
        }

    manifest = _read_json(target_root / AEGIS_MANIFEST_REL)
    applied = [
        _apply_repair_action(target_root, source, manifest, action) for action in safe_actions
    ]
    postflight = doctor(target_root, source_root=source)
    report = {
        "schema_version": SCHEMA_VERSION,
        "checked_at": _iso_now(),
        "target_root": str(target_root),
        "read_only": False,
        "status": "applied",
        "preflight": {
            "status": preflight.get("status"),
            "current_state": preflight.get("current_state"),
            "summary": preflight.get("summary"),
        },
        "applied": applied,
        "postflight": {
            "status": postflight.get("status"),
            "current_state": postflight.get("current_state"),
            "summary": postflight.get("summary"),
        },
        "report_written": True,
        "reports": [AEGIS_REPAIR_REPORT_REL],
    }
    report_path = target_root / AEGIS_REPAIR_REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_dump_json(report), encoding="utf-8")
    return report


def format_doctor_summary(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    repair_plan = (
        report.get("repair_plan") if isinstance(report.get("repair_plan"), Mapping) else {}
    )
    return "\n".join(
        [
            f"Aegis doctor: {report.get('status')} ({report.get('current_state')})",
            f"Checks: {summary.get('total', 0)} total, {summary.get('failed_required', 0)} required failures, {summary.get('warnings', 0)} warnings",
            f"Repair plan: {repair_plan.get('safe', 0)} safe, {repair_plan.get('manual_review', 0)} manual-review",
            "",
        ]
    )


def format_repair_summary(report: Mapping[str, Any]) -> str:
    applied = report.get("applied") if isinstance(report.get("applied"), list) else []
    return "\n".join(
        [
            f"Aegis repair: {report.get('status')}",
            f"Applied/skipped actions: {len(applied)}",
            f"Report written: {report.get('report_written')}",
            "",
        ]
    )


def verify(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    strict: bool = False,
    dry_run: bool = False,
    default_primary_agent: str = "claude",
    default_agents: Sequence[str] | None = None,
) -> dict[str, Any]:
    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    manifest_path = target_root / AEGIS_MANIFEST_REL
    manifest = _read_json(manifest_path)
    mode = "strict" if strict else "standard"
    checks: list[dict[str, Any]] = []
    if manifest is None:
        guidance_primary_agent, guidance_agents = _normalise_default_agent_selection(
            default_primary_agent,
            default_agents,
        )
        install_cli = (
            f"./.aegis/bin/aegis install --target-dir . "
            f"{_agent_selection_cli_args(guidance_primary_agent, guidance_agents)} --apply"
        )
        report = {
            "schema_version": SCHEMA_VERSION,
            "mode": mode,
            "status": "failed",
            "verified_at": _iso_now(),
            "target_root": str(target_root),
            "manifest_path": AEGIS_MANIFEST_REL,
            "dry_run": dry_run,
            "report_written": False,
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
            "next_action": _workflow_next_action(
                "install_aegis_before_verify",
                "Aegis is not installed in this target. Install it before running strict verification.",
                suggested_cli=install_cli,
                suggested_mcp_tool="aegis.install",
                suggested_mcp_arguments={
                    "target_dir": ".",
                    "profile": "generic",
                    "primary_agent": guidance_primary_agent,
                    "agents": list(guidance_agents),
                    "apply": True,
                },
            ),
        }
        if not dry_run:
            _write_verify_report(target_root, report)
            report["report_written"] = True
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

    failed_required = [
        check for check in checks if check.get("required") and check.get("status") == "fail"
    ]
    pending_tracking_expected = _expects_pending_tracking(target_root)
    verification_handler = _workflow_log_handler(target_root, "verification")
    if pending_tracking_expected:
        strict_log_cli = (
            "./.aegis/bin/aegis log --target-dir . --pending-id current "
            "--note 'Recorded strict verification evidence' "
            "--plan-step plan-step-verify --plan-status completed"
        )
        strict_log_mcp_arguments = {
            "target_dir": ".",
            "pending_event_id": "current",
            "note": "Recorded strict verification evidence",
            "plan_step": "plan-step-verify",
            "plan_status": "completed",
            "apply": True,
        }
    else:
        strict_log_cli = (
            f"./.aegis/bin/aegis log --target-dir . --handler {verification_handler} "
            f"--evidence {AEGIS_VERIFY_REPORT_REL} "
            "--note 'Recorded strict verification evidence' "
            "--plan-step plan-step-verify --plan-status completed"
        )
        strict_log_mcp_arguments = {
            "target_dir": ".",
            "handler": verification_handler,
            "evidence": AEGIS_VERIFY_REPORT_REL,
            "note": "Recorded strict verification evidence",
            "event_class": "verification",
            "plan_step": "plan-step-verify",
            "plan_status": "completed",
            "apply": True,
        }

    report = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "status": "failed" if failed_required else "passed",
        "verified_at": _iso_now(),
        "target_root": str(target_root),
        "manifest_path": AEGIS_MANIFEST_REL,
        "dry_run": dry_run,
        "report_written": False,
        "summary": {
            "total": len(checks),
            "failed_required": len(failed_required),
            "warnings": sum(1 for check in checks if check.get("status") == "warn"),
            "unsupported": sum(1 for check in checks if check.get("status") == "unsupported"),
        },
        "checks": checks,
        "next_action": (
            _workflow_next_action(
                "log_strict_verification_before_closeout",
                "Strict verification passed. Log the verification evidence against plan-step-verify before closeout.",
                suggested_cli=strict_log_cli,
                suggested_mcp_tool="aegis.log",
                suggested_mcp_arguments=strict_log_mcp_arguments,
                details={
                    "evidence": AEGIS_VERIFY_REPORT_REL,
                    "pending_tracking_expected": pending_tracking_expected,
                },
            )
            if strict and not failed_required
            else (
                _workflow_next_action(
                    "repair_verify_failures",
                    "Verification failed. Fix failed required checks before closeout.",
                    details={
                        "failed_required_gates": [
                            str(check.get("gate_id")) for check in failed_required
                        ]
                    },
                )
                if failed_required
                else _workflow_next_action(
                    "standard_verify_complete",
                    "Standard verification report was written. Run strict verification before closeout.",
                    suggested_cli="./.aegis/bin/aegis verify --target-dir . --strict",
                    suggested_mcp_tool="aegis.verify",
                    suggested_mcp_arguments={
                        "target_dir": ".",
                        "strict": True,
                        "acknowledge_report_write": True,
                    },
                )
            )
        ),
    }
    if not dry_run:
        _write_verify_report(target_root, report)
        report["report_written"] = True
    if report["status"] == "passed" and not dry_run:
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
            statuses[match.group("step")] = (
                "completed" if match.group("mark").lower() == "x" else "pending"
            )
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


def _first_markdown_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.strip()
    return fallback


def _markdown_tail_from_heading(text: str, heading: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == heading:
            return "\n".join(lines[index:]).rstrip()
    return ""


def _bullet_lines(tokens: Sequence[str], *, fallback: str) -> list[str]:
    unique_tokens = list(dict.fromkeys(token for token in tokens if token))
    if not unique_tokens:
        return [f"- {fallback}"]
    return [f"- `{token}`" for token in unique_tokens]


def _current_work_branch_name(current_work: Mapping[str, Any], paths: Mapping[str, Any]) -> str:
    branch_payload = current_work.get("branch")
    if isinstance(branch_payload, Mapping):
        return str(branch_payload.get("current") or branch_payload.get("name") or "")
    if isinstance(branch_payload, str):
        return branch_payload
    path_branch = paths.get("branch")
    return path_branch if isinstance(path_branch, str) else ""


def _render_closeout_handoff(
    existing_text: str,
    *,
    current_work: Mapping[str, Any],
    implementation_tokens: Sequence[str],
    verification_tokens: Sequence[str],
    strict_verify_rel: str,
) -> str:
    task = current_work.get("task") if isinstance(current_work.get("task"), Mapping) else {}
    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    task_id = str(task.get("id") or "")
    slug = str(task.get("slug") or "")
    title = str(task.get("title") or f"Task {task_id}")
    branch = _current_work_branch_name(current_work, paths)
    work_label = f"task{task_id}-{slug}" if task_id or slug else "current-work"
    semantic_title = _first_markdown_title(
        existing_text, f"# Task {task_id} {title} - Handoff Summary"
    )
    progress_log = _markdown_tail_from_heading(existing_text, "## Progress Log")
    all_evidence = list(
        dict.fromkeys([*implementation_tokens, *verification_tokens, strict_verify_rel])
    )
    evidence_summary = (
        ", ".join(f"`{token}`" for token in all_evidence) if all_evidence else "none available"
    )

    lines = [
        semantic_title,
        "",
        "## Current State",
        f"- Task {task_id} `{slug}` is ready for closeout validation.",
        f"- Title: {title}.",
        f"- Branch: `{branch}`.",
        f"- Current work: `{work_label}`.",
        f"- Strict verification report: `{strict_verify_rel}`.",
        f"- Closeout report target: `{AEGIS_CLOSEOUT_REPORT_REL}`.",
        "",
        "## What Was Done",
        "- Completed scope, implementation, and verification plan steps through Aegis logging.",
        "- Updated required workflow evidence across session, tracker, implementation, changelog, handoff, and plan surfaces.",
        "- Prepared closeout evidence so final closeout can write the report without ad hoc handoff edits.",
        "",
        "## Implementation Evidence",
        *_bullet_lines(
            implementation_tokens, fallback="No implementation evidence tokens were available."
        ),
        "",
        "## Verification Evidence",
        *_bullet_lines(
            verification_tokens,
            fallback="No task-specific verification evidence tokens were available.",
        ),
        "",
        "## Strict Verification Evidence",
        f"- `{strict_verify_rel}`",
        "",
        "## Current Issues/Blockers",
        "- None known at closeout.",
        "",
        "## Next Steps",
        f"1. Review `{AEGIS_CLOSEOUT_REPORT_REL}` after final closeout writes it.",
        "2. Commit and open a pull request with normal git/GitHub commands when delegated.",
        "3. Archive or continue the active work-tracking folder according to the project lifecycle.",
        "",
        "## Important Context",
        f"- Current work authority remains `{AEGIS_CURRENT_WORK_REL}` and final closeout marks it `completed`.",
        f"- Session: `{paths.get('session', 'unknown')}`.",
        f"- Plan: `{paths.get('plan', 'unknown')}`.",
        f"- Active work-tracking: `{paths.get('work_tracking', 'unknown')}`.",
        f"- Required closeout evidence: {evidence_summary}.",
        "- Taskmaster and Serena are optional unless current work marks them required.",
        "- Use normal git and GitHub commands by default. `gac` is legacy/manual only.",
    ]
    if progress_log:
        lines.extend(["", progress_log])
    return "\n".join(lines).rstrip() + "\n"


def _closeout_readiness(
    target_root: Path, current_work: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    current_work_status = str((current_work or {}).get("status") or "").strip()
    if current_work_status == "completed" and bool((current_work or {}).get("closeout_passed_at")):
        return {
            "status": "passed",
            "command": None,
            "returncode": 0,
            "stdout": "READY from completed closeout state",
            "stderr": "",
            "current_work_status": current_work_status,
        }

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
    failed = [
        check
        for check in workflow_checks
        if check.get("required") and check.get("status") == "fail"
    ]
    return {
        "status": "passed" if not failed else "failed",
        "command": None,
        "returncode": 0 if not failed else 2,
        "stdout": (
            "READY from strict current-work checks"
            if not failed
            else "BLOCKED by strict current-work checks"
        ),
        "stderr": "",
        "checks": workflow_checks,
    }


def _update_handoff_for_closeout(
    target_root: Path,
    *,
    handoff_path: Path,
    current_work: Mapping[str, Any],
    implementation_tokens: Sequence[str],
    verification_tokens: Sequence[str],
    strict_verify_rel: str,
) -> None:
    text = _read_text_or_empty(handoff_path)
    next_text = _render_closeout_handoff(
        text,
        current_work=current_work,
        implementation_tokens=implementation_tokens,
        verification_tokens=verification_tokens,
        strict_verify_rel=strict_verify_rel,
    )
    handoff_path.write_text(next_text, encoding="utf-8")


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
    next_steps_ok = bool(next_steps.strip()) and not any(
        phrase in next_steps for phrase in kickoff_only_phrases
    )

    checks = [
        _closeout_check(
            "closeout.handoff.current_state",
            passed=current_state_ok,
            message=(
                "handoff current state is semantic"
                if current_state_ok
                else "handoff current state is still placeholder/kickoff-oriented"
            ),
        ),
        _closeout_check(
            "closeout.handoff.next_steps",
            passed=next_steps_ok,
            message=(
                "handoff next steps are semantic"
                if next_steps_ok
                else "handoff next steps are still placeholder/kickoff-oriented"
            ),
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
                message=(
                    f"handoff semantic sections reference {label} evidence"
                    if not missing
                    else f"handoff semantic sections missing {label} evidence"
                ),
                details={"missing": missing},
            )
        )
    return checks


def _closeout_git_report(
    target_root: Path, *, require_clean_git: bool, include_guidance: bool
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    status_result = _run_target_git(target_root, "status", "--short")
    status_short = (
        status_result.stdout.strip().splitlines() if status_result.returncode == 0 else []
    )
    if require_clean_git:
        checks.append(
            _closeout_check(
                "closeout.git.clean",
                passed=status_result.returncode == 0 and not status_short,
                message=(
                    "git worktree is clean"
                    if status_result.returncode == 0 and not status_short
                    else "git worktree has uncommitted changes"
                ),
                category="git",
                details={"status_short": status_short, "stderr": status_result.stderr.strip()},
            )
        )
    guidance = []
    if include_guidance:
        guidance = [
            "git status --short",
            "git add <paths>",
            'git commit -m "<type(scope): summary>"',
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


SWHE_LINE_RE = re.compile(
    r"\[S:(?P<s>[^\]|]+)\|W:(?P<w>[^\]|]+)\|H:(?P<h>[^\]|]+)\|E:(?P<e>[^\]]+)\]\s*(?P<note>.*)"
)


def _swhe_entries_by_evidence(surface_texts: Mapping[str, str]) -> dict[str, list[dict[str, str]]]:
    entries: dict[str, list[dict[str, str]]] = {}
    for surface, text in surface_texts.items():
        for line in text.splitlines():
            match = SWHE_LINE_RE.search(line)
            if not match:
                continue
            evidence = match.group("e")
            entries.setdefault(evidence, []).append(
                {
                    "surface": surface,
                    "handler": match.group("h"),
                    "note": match.group("note").strip(),
                }
            )
    return entries


def _suggested_plan_step_for_evidence(
    evidence: str,
    *,
    implementation_tokens: Sequence[str],
    verification_tokens: Sequence[str],
    strict_verify_rel: str,
) -> str | None:
    if evidence == strict_verify_rel or evidence in verification_tokens:
        return "plan-step-verify"
    if evidence in implementation_tokens:
        return "plan-step-implement"
    return None


def _build_closeout_repair_guidance(
    *,
    surface_texts: Mapping[str, str],
    evidence_matrix: Mapping[str, Mapping[str, bool]],
    implementation_tokens: Sequence[str],
    verification_tokens: Sequence[str],
    strict_verify_rel: str,
    pending_events: Sequence[Mapping[str, Any]],
    checks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    entries_by_evidence = _swhe_entries_by_evidence(surface_texts)
    repair_items: list[dict[str, Any]] = []
    for evidence, surfaces in evidence_matrix.items():
        present_entries = entries_by_evidence.get(evidence, [])
        inferred = present_entries[0] if present_entries else {}
        handler = inferred.get("handler")
        note = inferred.get("note")
        suggested_plan_step = _suggested_plan_step_for_evidence(
            evidence,
            implementation_tokens=implementation_tokens,
            verification_tokens=verification_tokens,
            strict_verify_rel=strict_verify_rel,
        )
        suggested_event_class = _infer_log_event_class(
            plan_step=suggested_plan_step,
            handler=handler or "",
            evidence=evidence,
        )
        for surface, present in surfaces.items():
            if present:
                continue
            item: dict[str, Any] = {
                "kind": "missing_evidence_reference",
                "surface": surface,
                "evidence": evidence,
                "suggested_event_class": suggested_event_class,
                "suggested_plan_step": suggested_plan_step,
                "source_surface": inferred.get("surface"),
                "handler": handler,
                "note": note,
            }
            if handler and note:
                command_parts = [
                    "aegis",
                    "log",
                    "--handler",
                    _quote_cli(handler),
                    "--evidence",
                    _quote_cli(evidence),
                    "--note",
                    _quote_cli(note),
                ]
                if surface in AEGIS_LOG_SURFACES:
                    command_parts.extend(["--surface", _quote_cli(surface)])
                elif surface == "plan" and suggested_plan_step:
                    command_parts.extend(
                        [
                            "--plan-step",
                            _quote_cli(suggested_plan_step),
                            "--plan-status",
                            "completed",
                        ]
                    )
                item["command"] = " ".join(command_parts)
            else:
                command_template = (
                    "aegis log --handler <handler> --evidence "
                    f'{_quote_cli(evidence)} --note "<past-tense note>"'
                )
                if surface in AEGIS_LOG_SURFACES:
                    command_template = f"{command_template} --surface {_quote_cli(surface)}"
                elif surface == "plan" and suggested_plan_step:
                    command_template = (
                        f"{command_template} --plan-step {_quote_cli(suggested_plan_step)} "
                        "--plan-status completed"
                    )
                item["command_template"] = command_template
            repair_items.append(item)

    for event in pending_events:
        event_id = str(event.get("id") or "")
        repair_items.append(
            {
                "kind": "pending_tracking_event",
                "pending_event_id": event_id,
                "handler": event.get("handler"),
                "evidence": event.get("evidence"),
                "command_template": (
                    "aegis log --pending-id "
                    f'{_quote_cli(event_id)} --note "<past-tense note>" '
                    "--plan-step <plan-step-id> --plan-status completed"
                ),
            }
        )

    failing_gate_ids = [
        str(check.get("gate_id"))
        for check in checks
        if check.get("required") and check.get("status") == "fail"
    ]
    return {
        "summary": {
            "items": len(repair_items),
            "failing_required_gates": failing_gate_ids,
        },
        "items": repair_items,
    }


def _handoff_repairable_closeout_failure(gate_ids: Sequence[str]) -> bool:
    """Return true when deterministic handoff repair is the right next action."""

    if not gate_ids:
        return False
    return all(
        gate_id.startswith("closeout.handoff.") or gate_id == "closeout.evidence.handoff"
        for gate_id in gate_ids
    )


def _closeout_failed_required_gate_ids(report: Mapping[str, Any]) -> list[str]:
    return [
        str(check.get("gate_id") or check.get("id") or "unknown")
        for check in report.get("checks", [])
        if isinstance(check, Mapping) and check.get("required") and check.get("status") == "fail"
    ]


def format_closeout_summary(report: Mapping[str, Any]) -> str:
    """Render a concise human closeout summary while preserving JSON reports for automation."""

    dry_run = bool(report.get("dry_run"))
    label = "Aegis closeout readiness" if dry_run else "Aegis closeout"
    status = str(report.get("status") or "unknown").upper()
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    pending = (
        report.get("pending_tracking")
        if isinstance(report.get("pending_tracking"), Mapping)
        else {}
    )
    pending_events = pending.get("events") if isinstance(pending.get("events"), list) else []
    failed_gates = _closeout_failed_required_gate_ids(report)
    next_action = (
        report.get("next_action") if isinstance(report.get("next_action"), Mapping) else {}
    )
    repair_guidance = (
        report.get("repair_guidance") if isinstance(report.get("repair_guidance"), Mapping) else {}
    )
    repair_items = (
        repair_guidance.get("items") if isinstance(repair_guidance.get("items"), list) else []
    )
    first_repair = repair_items[0] if repair_items and isinstance(repair_items[0], Mapping) else {}
    first_repair_command = str(
        first_repair.get("command") or first_repair.get("command_template") or ""
    ).strip()
    report_written = bool(report.get("report_written"))
    closeout_report_state = "written" if report_written else "not written by this run"
    lines = [
        f"{label}: {status}",
        f"mode: {'dry-run' if dry_run else 'final'}",
        f"failed_required: {summary.get('failed_required', 0)}",
        f"warnings: {summary.get('warnings', 0)}",
        f"pending_tracking: {len(pending_events)}",
        f"closeout_report: {AEGIS_CLOSEOUT_REPORT_REL} ({closeout_report_state})",
    ]
    if failed_gates:
        lines.append("failed_gates:")
        lines.extend(f"- {gate}" for gate in failed_gates[:10])
        if len(failed_gates) > 10:
            lines.append(f"- ... {len(failed_gates) - 10} more")
    if first_repair_command:
        lines.append(f"repair: {first_repair_command}")
    suggested_cli = str(next_action.get("suggested_cli") or "").strip()
    if suggested_cli:
        lines.append(f"next: {suggested_cli}")
    lines.append("json: rerun with --json for the full structured report")
    return "\n".join(lines) + "\n"


def repair_handoff(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Repair Aegis-owned semantic HANDOFF.md sections without final closeout side effects."""

    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    checked_at = _iso_now()
    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    if not isinstance(current_work, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "failed",
            "dry_run": dry_run,
            "report_written": False,
            "state_updated": False,
            "checked_at": checked_at,
            "target_root": str(target_root),
            "reason": f"{AEGIS_CURRENT_WORK_REL} missing or invalid; run aegis kickoff first",
            "next_action": _workflow_next_action(
                "kickoff_before_handoff_repair",
                "Aegis handoff repair requires active current work state.",
                suggested_cli='./.aegis/bin/aegis kickoff --target-dir . --task <id> --slug <slug> --title "<title>"',
                suggested_mcp_tool="aegis.kickoff",
            ),
        }

    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    plan_rel = str(paths.get("plan") or "")
    work_rel = str(paths.get("work_tracking") or "")
    plan_path = target_root / plan_rel if plan_rel else target_root / "plans" / "current"
    work_path = (
        target_root / work_rel
        if work_rel
        else target_root / "docs" / "ai" / "work-tracking" / "active"
    )
    handoff_path = work_path / "HANDOFF.md"
    if not handoff_path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "failed",
            "dry_run": dry_run,
            "report_written": False,
            "state_updated": False,
            "checked_at": checked_at,
            "target_root": str(target_root),
            "current_work": current_work,
            "handoff": {
                "path": _repo_path(handoff_path, target_root),
                "exists": False,
                "updated": False,
                "would_update": False,
            },
            "reason": "HANDOFF.md is missing from the active work-tracking folder.",
            "next_action": _workflow_next_action(
                "repair_missing_work_tracking_before_handoff_repair",
                "Aegis handoff repair can only update an existing active HANDOFF.md.",
                suggested_cli='./.aegis/bin/aegis kickoff --target-dir . --task <id> --slug <slug> --title "<title>"',
            ),
        }

    before = closeout(
        target_root,
        source_root=source,
        update_handoff=True,
        dry_run=True,
    )
    plan_rows = _parse_plan_rows(plan_path)
    implementation_tokens = [
        token
        for token in _split_evidence_tokens(
            str(plan_rows.get("plan-step-implement", {}).get("evidence") or "")
        )
        if _is_closeout_required_evidence(token)
    ]
    verification_tokens = [
        token
        for token in _split_evidence_tokens(
            str(plan_rows.get("plan-step-verify", {}).get("evidence") or "")
        )
        if _is_closeout_required_evidence(token)
    ]
    strict_verify_rel = _normalize_evidence(target_root, AEGIS_VERIFY_REPORT_REL)
    before_text = _read_text_or_empty(handoff_path)
    repaired_text = _render_closeout_handoff(
        before_text,
        current_work=current_work,
        implementation_tokens=implementation_tokens,
        verification_tokens=verification_tokens,
        strict_verify_rel=strict_verify_rel,
    )
    changed = repaired_text != before_text
    after: dict[str, Any] | None = None
    if not dry_run and changed:
        handoff_path.write_text(repaired_text, encoding="utf-8")
        after = closeout(
            target_root,
            source_root=source,
            update_handoff=True,
            dry_run=True,
        )
    elif not dry_run:
        after = before

    failing_before = [
        str(check.get("gate_id"))
        for check in before.get("checks", [])
        if check.get("required") and check.get("status") == "fail"
    ]
    failing_after = [
        str(check.get("gate_id"))
        for check in (after or {}).get("checks", [])
        if check.get("required") and check.get("status") == "fail"
    ]
    status_value = "planned" if dry_run else "repaired"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status_value,
        "dry_run": dry_run,
        "report_written": False,
        "state_updated": False,
        "checked_at": checked_at,
        "target_root": str(target_root),
        "current_work": current_work,
        "handoff": {
            "path": _repo_path(handoff_path, target_root),
            "exists": True,
            "updated": changed and not dry_run,
            "would_update": changed and dry_run,
            "changed": changed,
            "preserved_progress_log": "## Progress Log" in before_text,
            "sections": [
                "Current State",
                "What Was Done",
                "Implementation Evidence",
                "Verification Evidence",
                "Strict Verification Evidence",
                "Current Issues/Blockers",
                "Next Steps",
                "Important Context",
            ],
        },
        "evidence": {
            "implementation": implementation_tokens,
            "verification": verification_tokens,
            "strict_verify": strict_verify_rel,
        },
        "closeout_ready_before": {
            "status": before.get("status"),
            "failed_required_gates": failing_before,
            "repair_items": before.get("repair_guidance", {}).get("summary", {}).get("items"),
        },
        "closeout_ready_after": (
            {
                "status": after.get("status"),
                "failed_required_gates": failing_after,
                "repair_items": after.get("repair_guidance", {}).get("summary", {}).get("items"),
            }
            if after is not None
            else None
        ),
        "preview": repaired_text if dry_run else None,
        "next_action": (
            _workflow_next_action(
                "apply_handoff_repair",
                "Aegis can repair the active handoff without writing closeout reports or current-work state.",
                suggested_cli="./.aegis/bin/aegis handoff repair --target-dir .",
                suggested_mcp_tool="aegis.handoff_repair",
                suggested_mcp_arguments={"target_dir": ".", "apply": True},
            )
            if dry_run and changed
            else (
                _workflow_next_action(
                    "rerun_closeout_ready",
                    "Handoff repair applied. Re-run closeout_ready; if it passes, run final closeout.",
                    suggested_cli="./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff",
                    suggested_mcp_tool="aegis.closeout_ready",
                    suggested_mcp_arguments={"target_dir": ".", "update_handoff": True},
                    details={
                        "closeout_ready_status": (
                            after.get("status") if after else before.get("status")
                        )
                    },
                )
                if not dry_run
                else _workflow_next_action(
                    "no_handoff_repair_needed",
                    "The active handoff already matches the deterministic repair rendering.",
                    suggested_cli="./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff",
                )
            )
        ),
    }


def closeout(
    target_dir: str | Path,
    *,
    source_root: str | Path,
    update_handoff: bool = False,
    require_clean_git: bool = False,
    include_git_guidance: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Validate that Aegis workflow state is complete enough to report task completion."""

    target_root = _resolve_target_root(target_dir)
    source = Path(source_root).resolve()
    checked_at = _iso_now()
    checks: list[dict[str, Any]] = []

    current_work = _read_json(target_root / AEGIS_CURRENT_WORK_REL)
    current_work_status = (
        str(current_work.get("status") or "").strip() if isinstance(current_work, Mapping) else ""
    )
    current_work_ok = isinstance(current_work, dict) and (
        current_work_status == "in-progress"
        or (current_work_status == "completed" and bool(current_work.get("closeout_passed_at")))
    )
    current_work_message = (
        "current work payload is active"
        if current_work_status == "in-progress"
        else (
            "current work payload is completed"
            if current_work_ok
            else f"{AEGIS_CURRENT_WORK_REL} missing, invalid, or not active/completed"
        )
    )
    checks.append(
        _closeout_check(
            "closeout.current_work",
            passed=current_work_ok,
            message=current_work_message,
            details={"path": AEGIS_CURRENT_WORK_REL, "status": current_work_status},
        )
    )
    if not isinstance(current_work, dict):
        current_work = {}

    paths = current_work.get("paths") if isinstance(current_work.get("paths"), Mapping) else {}
    session_rel = str(paths.get("session") or "")
    plan_rel = str(paths.get("plan") or "")
    work_rel = str(paths.get("work_tracking") or "")
    session_path = (
        target_root / session_rel if session_rel else target_root / "sessions" / "current"
    )
    plan_path = target_root / plan_rel if plan_rel else target_root / "plans" / "current"
    work_path = (
        target_root / work_rel
        if work_rel
        else target_root / "docs" / "ai" / "work-tracking" / "active"
    )
    tracker_path = work_path / "TRACKER.md"
    implementation_path = work_path / "IMPLEMENTATION.md"
    changelog_path = work_path / "CHANGELOG.md"
    handoff_path = work_path / "HANDOFF.md"

    readiness = _closeout_readiness(target_root, current_work=current_work)
    checks.append(
        _closeout_check(
            "closeout.readiness",
            passed=readiness.get("status") == "passed",
            message=(
                "readiness is READY"
                if readiness.get("status") == "passed"
                else "readiness is not READY"
            ),
            details=readiness,
        )
    )

    pending_events = _pending_tracking_events(target_root)
    checks.append(
        _closeout_check(
            "closeout.pending_tracking",
            passed=not pending_events,
            message=(
                "pending tracking queue is empty"
                if not pending_events
                else "pending tracking queue has unlogged mutation events"
            ),
            details={"path": AEGIS_PENDING_TRACKING_REL, "events": pending_events},
        )
    )
    degraded_events = _degraded_events(target_root)
    unacknowledged_degraded = [
        event
        for event in degraded_events
        if not event.get("acknowledged_at") and not event.get("resolved_at")
    ]
    checks.append(
        _closeout_check(
            "closeout.degraded_events_acknowledged",
            passed=not unacknowledged_degraded,
            message=(
                "degraded gate events are acknowledged or resolved"
                if not unacknowledged_degraded
                else "unacknowledged degraded gate events block closeout"
            ),
            details={
                "path": AEGIS_DEGRADED_EVENTS_REL,
                "total": len(degraded_events),
                "unacknowledged": unacknowledged_degraded,
            },
        )
    )

    strict_verify = verify(target_root, source_root=source, strict=True, dry_run=dry_run)
    checks.append(
        _closeout_check(
            "closeout.strict_verify",
            passed=strict_verify.get("status") == "passed",
            message=(
                "strict verification passed"
                if strict_verify.get("status") == "passed"
                else "strict verification failed"
            ),
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
                message=(
                    f"{step} completed in current plan"
                    if plan_completed
                    else f"{step} missing or not completed in current plan"
                ),
                category="plan",
                details={"row": row},
            )
        )
        tracker_completed = tracker_steps.get(step) == "completed"
        checks.append(
            _closeout_check(
                f"closeout.tracker.{step.removeprefix('plan-step-')}",
                passed=tracker_completed,
                message=(
                    f"{step} completed in tracker"
                    if tracker_completed
                    else f"{step} missing or unchecked in tracker"
                ),
                category="tracker",
                details={"tracker_status": tracker_steps.get(step)},
            )
        )

    ordered = all(step in plan_rows for step in required_steps) and [
        int(plan_rows[step]["index"]) for step in required_steps
    ] == sorted(int(plan_rows[step]["index"]) for step in required_steps)
    checks.append(
        _closeout_check(
            "closeout.plan.order",
            passed=ordered,
            message=(
                "required plan steps are in scope -> implement -> verify order"
                if ordered
                else "required plan steps are missing or out of order"
            ),
            category="plan",
            details={"order": [step for step in plan_rows if step in required_steps]},
        )
    )

    implementation_tokens = [
        token
        for token in _split_evidence_tokens(
            str(plan_rows.get("plan-step-implement", {}).get("evidence") or "")
        )
        if _is_closeout_required_evidence(token)
    ]
    verification_tokens = [
        token
        for token in _split_evidence_tokens(
            str(plan_rows.get("plan-step-verify", {}).get("evidence") or "")
        )
        if _is_closeout_required_evidence(token)
    ]
    strict_verify_rel = _normalize_evidence(target_root, AEGIS_VERIFY_REPORT_REL)
    required_evidence = tuple(
        dict.fromkeys([*implementation_tokens, *verification_tokens, strict_verify_rel])
    )

    surface_texts = {
        "session": _read_text_or_empty(session_path),
        "tracker": _read_text_or_empty(tracker_path),
        "implementation": _read_text_or_empty(implementation_path),
        "changelog": _read_text_or_empty(changelog_path),
        "handoff": _read_text_or_empty(handoff_path),
        "plan": _read_text_or_empty(plan_path),
    }
    evidence_matrix = {
        token: {surface: token in text for surface, text in surface_texts.items()}
        for token in required_evidence
    }
    for surface, text in surface_texts.items():
        missing = [token for token in required_evidence if token not in text]
        checks.append(
            _closeout_check(
                f"closeout.evidence.{surface}",
                passed=not missing,
                message=(
                    f"{surface} references all required evidence"
                    if not missing
                    else f"{surface} is missing required evidence"
                ),
                category="evidence",
                details={"missing": missing},
            )
        )

    if update_handoff and not dry_run and handoff_path.is_file():
        _update_handoff_for_closeout(
            target_root,
            handoff_path=handoff_path,
            current_work=current_work,
            implementation_tokens=implementation_tokens,
            verification_tokens=verification_tokens,
            strict_verify_rel=strict_verify_rel,
        )
        surface_texts["handoff"] = _read_text_or_empty(handoff_path)
        evidence_matrix = {
            token: {surface: (token in surface_texts[surface]) for surface in surface_texts}
            for token in required_evidence
        }
        checks = [check for check in checks if check.get("gate_id") != "closeout.evidence.handoff"]
        missing = [token for token in required_evidence if token not in surface_texts["handoff"]]
        checks.append(
            _closeout_check(
                "closeout.evidence.handoff",
                passed=not missing,
                message=(
                    "handoff references all required evidence"
                    if not missing
                    else "handoff is missing required evidence"
                ),
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

    integrations = (
        current_work.get("integrations")
        if isinstance(current_work.get("integrations"), Mapping)
        else {}
    )
    integration_report: dict[str, Any] = {}
    for name, rel_path in (("taskmaster", ".taskmaster"), ("serena", ".serena")):
        integration = integrations.get(name) if isinstance(integrations, Mapping) else {}
        required = isinstance(integration, Mapping) and integration.get("required") is True
        detected = (target_root / rel_path).exists()
        integration_report[name] = {
            "detected": detected,
            "required": required,
            "status": (
                "present" if detected else "optional_absent" if not required else "required_missing"
            ),
        }

    git_report, git_checks = _closeout_git_report(
        target_root,
        require_clean_git=require_clean_git,
        include_guidance=include_git_guidance,
    )
    checks.extend(git_checks)

    failed_required = [
        check for check in checks if check.get("required") and check.get("status") == "fail"
    ]
    failed_required_gate_ids = [str(check.get("gate_id")) for check in failed_required]
    status_value = "failed" if failed_required else "passed"
    repair_guidance = _build_closeout_repair_guidance(
        surface_texts=surface_texts,
        evidence_matrix=evidence_matrix,
        implementation_tokens=implementation_tokens,
        verification_tokens=verification_tokens,
        strict_verify_rel=strict_verify_rel,
        pending_events=pending_events,
        checks=checks,
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status_value,
        "dry_run": dry_run,
        "report_written": False,
        "state_updated": False,
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
        "degraded_events": {
            "path": AEGIS_DEGRADED_EVENTS_REL,
            "events": degraded_events,
            "unacknowledged": unacknowledged_degraded,
        },
        "evidence_matrix": evidence_matrix,
        "handoff": {
            "path": _repo_path(handoff_path, target_root),
            "updated": update_handoff and not dry_run,
            "would_update": update_handoff and dry_run,
        },
        "integrations": integration_report,
        "git": git_report,
        "repair_guidance": repair_guidance,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "failed_required": len(failed_required),
            "warnings": 0,
        },
        "next_action": (
            _workflow_next_action(
                "run_closeout_to_write_report",
                "Closeout readiness passed. Run non-dry-run closeout to write the closeout report before reporting the task complete.",
                suggested_cli="./.aegis/bin/aegis closeout --target-dir . --update-handoff",
                suggested_mcp_tool="aegis.closeout",
                suggested_mcp_arguments={
                    "target_dir": ".",
                    "acknowledge_report_write": True,
                    "update_handoff": True,
                },
                details={"dry_run": True, "closeout_report": AEGIS_CLOSEOUT_REPORT_REL},
            )
            if status_value == "passed"
            and dry_run
            and not (
                current_work_status == "completed" and bool(current_work.get("closeout_passed_at"))
            )
            else (
                _workflow_next_action(
                    "run_post_closeout_doctor",
                    "Closeout passed and wrote the report. Run read-only doctor once before the final user report.",
                    suggested_cli="./.aegis/bin/aegis doctor --target-dir .",
                    suggested_mcp_tool="aegis.doctor",
                    suggested_mcp_arguments={"target_dir": "."},
                    details={"closeout_report": AEGIS_CLOSEOUT_REPORT_REL},
                )
                if status_value == "passed" and not dry_run
                else (
                    _workflow_next_action(
                        "task_complete",
                        "Closeout passed. It is now valid to report the task complete and proceed with normal git/GitHub commands.",
                        suggested_cli="git status --short",
                        details={"closeout_report": AEGIS_CLOSEOUT_REPORT_REL},
                    )
                    if status_value == "passed"
                    else (
                        _workflow_next_action(
                            "apply_handoff_repair_before_retry",
                            "Closeout failed only on handoff gates. Run deterministic handoff repair, then re-run closeout readiness.",
                            suggested_cli="./.aegis/bin/aegis handoff repair --target-dir .",
                            suggested_mcp_tool="aegis.handoff_repair",
                            suggested_mcp_arguments={
                                "target_dir": ".",
                                "apply": True,
                            },
                            details={
                                "failed_required_gates": failed_required_gate_ids,
                                "repair_items": repair_guidance["summary"]["items"],
                                "after_repair": "./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff",
                            },
                        )
                        if _handoff_repairable_closeout_failure(failed_required_gate_ids)
                        else _workflow_next_action(
                            "repair_closeout_gates_before_retry",
                            "Closeout failed. Do not report the task complete; apply repair_guidance and retry closeout.",
                            suggested_cli=(
                                "./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff"
                                if dry_run
                                else "./.aegis/bin/aegis closeout --target-dir . --update-handoff"
                            ),
                            suggested_mcp_tool=(
                                "aegis.closeout_ready" if dry_run else "aegis.closeout"
                            ),
                            suggested_mcp_arguments={
                                "target_dir": ".",
                                "update_handoff": True,
                                **({} if dry_run else {"acknowledge_report_write": True}),
                            },
                            details={
                                "failed_required_gates": failed_required_gate_ids,
                                "repair_items": repair_guidance["summary"]["items"],
                            },
                        )
                    )
                )
            )
        ),
    }
    if status_value == "passed" and not dry_run:
        report["closed_at"] = _iso_now()

    if status_value == "passed" and current_work and not dry_run:
        current_work["updated_at"] = _iso_now()
        current_work["closeout_passed_at"] = report["closed_at"]
        current_work["closeout_report"] = AEGIS_CLOSEOUT_REPORT_REL
        current_work["status"] = "completed"
        task_payload = current_work.get("task")
        if isinstance(task_payload, dict):
            task_payload["status"] = "completed"
        _write_text(target_root, AEGIS_CURRENT_WORK_REL, _dump_json(current_work))
        report["state_updated"] = True

    if not dry_run:
        report["report_written"] = True
        reports_dir = target_root / AEGIS_REPORTS_REL
        reports_dir.mkdir(parents=True, exist_ok=True)
        (target_root / AEGIS_CLOSEOUT_REPORT_REL).write_text(_dump_json(report), encoding="utf-8")

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
        suffix for suffix in required if not any(member.endswith(suffix) for member in members)
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

        command_steps: list[
            tuple[str, list[str], Path, Sequence[int], str | None, Mapping[str, str] | None]
        ] = [
            ("aegis_version", [aegis_bin.as_posix(), "--version"], target, (0,), None, env),
            ("git_init", ["git", "init", "-b", "main"], target, (0,), None, env),
            (
                "aegis_inspect",
                [aegis_bin.as_posix(), "inspect", "--target-dir", "."],
                target,
                (0,),
                None,
                env,
            ),
            (
                "aegis_plan_install",
                [
                    aegis_bin.as_posix(),
                    "plan-install",
                    "--target-dir",
                    ".",
                    "--primary-agent",
                    "claude",
                    "--agent",
                    "claude",
                ],
                target,
                (0,),
                None,
                env,
            ),
            (
                "aegis_install",
                [
                    aegis_bin.as_posix(),
                    "install",
                    "--target-dir",
                    ".",
                    "--primary-agent",
                    "claude",
                    "--agent",
                    "claude",
                    "--apply",
                ],
                target,
                (0,),
                None,
                env,
            ),
            (
                "aegis_status",
                [aegis_bin.as_posix(), "status", "--target-dir", "."],
                target,
                (0,),
                None,
                env,
            ),
            (
                "aegis_kickoff",
                [
                    aegis_bin.as_posix(),
                    "kickoff",
                    "--target-dir",
                    ".",
                    "--task",
                    "42",
                    "--slug",
                    "release-cert",
                    "--title",
                    "Release Certification",
                ],
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
        tracking_steps: list[
            tuple[str, list[str], Sequence[int], str | None, Mapping[str, str]]
        ] = [
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
                json.dumps(
                    {
                        "tool_name": "Write",
                        "tool_input": {"file_path": f"{reports_rel}/blocked-before-log.txt"},
                    }
                ),
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
                "status": (
                    "pass" if payload.get("distribution_name") == "aegis-foundation" else "fail"
                ),
                "observed": payload.get("distribution_name"),
            },
            {
                "id": "default_target_dir",
                "status": (
                    "pass" if payload.get("default_target_dir") == target.as_posix() else "fail"
                ),
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
            else [
                sys.executable,
                "-m",
                "build",
                "--sdist",
                "--wheel",
                "--outdir",
                dist_path.as_posix(),
            ]
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
        cli_smoke = {
            "status": "failed",
            "reason": "no wheel artifact available for clean CLI smoke",
        }
        mcp_config_smoke = {
            "status": "failed",
            "reason": "no wheel artifact available for MCP server config smoke",
        }
    else:
        cli_smoke = {"status": "skipped", "reason": "clean CLI smoke disabled by caller"}
        mcp_config_smoke = {
            "status": "skipped",
            "reason": "MCP server config smoke disabled by caller",
        }

    failures: list[dict[str, Any]] = []
    if build_payload.get("status") == "failed":
        failures.append({"stage": "build", "message": "artifact build failed"})
    if missing_kinds:
        failures.append(
            {
                "stage": "artifacts",
                "message": "required artifact kind missing",
                "missing": missing_kinds,
            }
        )
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
        failures.append(
            {"stage": "mcp_server_config_smoke", "message": "MCP server config smoke failed"}
        )

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
            "github_release_candidate_ready": status_value == "passed"
            and cli_smoke.get("status") == "passed",
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
