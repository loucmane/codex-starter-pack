"""Tests for Aegis Foundation schema contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schemas" / "aegis"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    schema = load_schema(name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(name: str, payload: dict) -> None:
    validator(name).validate(payload)


def valid_manifest() -> dict:
    return {
        "schema_version": "1.0.0",
        "foundation_name": "Aegis Foundation",
        "foundation_version": "0.1.0",
        "installer_version": "0.1.0",
        "installed_at": "2026-05-16T11:46:53+02:00",
        "profile": "generic",
        "primary_agent": "claude",
        "entrypoints": {
            "shared": "AGENTS.md",
            "contract": ".aegis/contract.md",
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
        "agents": {
            "claude": {
                "enabled": True,
                "available": True,
                "entrypoint": "CLAUDE.md",
                "managed_files": [
                    "CLAUDE.md",
                    ".claude/settings.json",
                    ".claude/scripts/readiness.sh",
                    ".claude/scripts/pretooluse-gate.sh",
                    ".claude/scripts/posttooluse-tracking.sh",
                    ".claude/scripts/tracking-stop-gate.sh",
                    ".claude/scripts/bash-command-guard.sh",
                    ".claude/scripts/codex-path-guard.sh",
                ],
                "gate_ids": [
                    "claude.readiness",
                    "claude.pretooluse",
                    "claude.posttooluse_tracking",
                    "claude.stop_tracking",
                    "claude.bash_command",
                    "claude.protected_path",
                ],
            },
            "codex": {
                "enabled": False,
                "available": True,
                "entrypoint": "CODEX.md",
                "managed_files": [],
                "gate_ids": [
                    "codex.guard",
                    "codex.work_tracking_audit",
                ],
            },
            "gemini": {
                "enabled": False,
                "available": False,
                "entrypoint": None,
                "managed_files": [],
                "gate_ids": [],
            },
        },
        "capabilities": {
            "taskmaster": True,
            "work_tracking": True,
            "ci": False,
            "mcp_contract": True,
        },
        "gates": [
            {
                "id": "claude.readiness",
                "required": True,
                "enforcement": "mechanical",
                "scope": "adapter",
                "adapter": "claude",
                "path": ".claude/scripts/readiness.sh",
                "verification": {
                    "method": "executable",
                    "failure_mode": "fail",
                    "expected": True,
                },
            },
            {
                "id": "claude.pretooluse",
                "required": True,
                "enforcement": "mechanical",
                "scope": "adapter",
                "adapter": "claude",
                "path": ".claude/scripts/pretooluse-gate.sh",
                "settings_path": ".claude/settings.json",
                "hook_event": "PreToolUse",
                "hook_matcher": "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$",
                "verification": {
                    "method": "settings_hook",
                    "failure_mode": "fail",
                    "expected": "bash $CLAUDE_PROJECT_DIR/.claude/scripts/pretooluse-gate.sh",
                },
            },
            {
                "id": "claude.posttooluse_tracking",
                "required": True,
                "enforcement": "mechanical",
                "scope": "adapter",
                "adapter": "claude",
                "path": ".claude/scripts/posttooluse-tracking.sh",
                "settings_path": ".claude/settings.json",
                "hook_event": "PostToolUse",
                "hook_matcher": "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$",
                "verification": {
                    "method": "settings_hook",
                    "failure_mode": "fail",
                    "expected": "bash $CLAUDE_PROJECT_DIR/.claude/scripts/posttooluse-tracking.sh",
                },
            },
            {
                "id": "claude.stop_tracking",
                "required": True,
                "enforcement": "mechanical",
                "scope": "adapter",
                "adapter": "claude",
                "path": ".claude/scripts/tracking-stop-gate.sh",
                "settings_path": ".claude/settings.json",
                "hook_event": "Stop",
                "verification": {
                    "method": "settings_hook",
                    "failure_mode": "fail",
                    "expected": "bash $CLAUDE_PROJECT_DIR/.claude/scripts/tracking-stop-gate.sh",
                },
            },
            {
                "id": "claude.bash_command",
                "required": True,
                "enforcement": "mechanical",
                "scope": "adapter",
                "adapter": "claude",
                "path": ".claude/scripts/bash-command-guard.sh",
                "verification": {
                    "method": "executable",
                    "failure_mode": "fail",
                    "expected": True,
                },
            },
            {
                "id": "claude.protected_path",
                "required": True,
                "enforcement": "mechanical",
                "scope": "adapter",
                "adapter": "claude",
                "path": ".claude/scripts/codex-path-guard.sh",
                "verification": {
                    "method": "executable",
                    "failure_mode": "fail",
                    "expected": True,
                },
            },
            {
                "id": "codex.guard",
                "required": False,
                "enforcement": "verification",
                "scope": "adapter",
                "adapter": "codex",
                "command": "python3 scripts/codex-guard validate --include-untracked",
                "verification": {
                    "method": "command",
                    "failure_mode": "warn",
                    "expected": True,
                },
            },
            {
                "id": "mcp.memory_write",
                "required": False,
                "enforcement": "policy",
                "scope": "shared",
                "unsupported_reason": "MCP memory writes are not mechanically hookable in every client.",
                "verification": {
                    "method": "manual",
                    "failure_mode": "unsupported",
                    "expected": None,
                },
            },
        ],
        "managed_files": [
            {
                "path": ".aegis/foundation-manifest.json",
                "kind": "managed",
            },
            {
                "path": "CLAUDE.md",
                "kind": "adapter",
            },
        ],
        "customized_files": [],
        "verification": {
            "status": "never",
            "last_verified_at": None,
            "reports": [],
        },
    }


def valid_profile() -> dict:
    return {
        "schema_version": "1.0.0",
        "name": "generic",
        "description": "Generic Aegis install profile for unknown repositories.",
        "default_primary_agent": "claude",
        "supported_agents": [
            "claude",
            "codex",
        ],
        "agent_selection_required": True,
        "paths": {
            "manifest": ".aegis/foundation-manifest.json",
            "reports": ".aegis/reports",
            "state": ".aegis/state",
            "local_cli": ".aegis/bin/aegis",
        },
        "adapter_requirements": {
            "claude": {
                "entrypoint": "CLAUDE.md",
                "required_files": [
                    "CLAUDE.md",
                    ".claude/settings.json",
                    ".claude/scripts/readiness.sh",
                    ".claude/scripts/pretooluse-gate.sh",
                    ".claude/scripts/posttooluse-tracking.sh",
                    ".claude/scripts/tracking-stop-gate.sh",
                    ".claude/scripts/bash-command-guard.sh",
                    ".claude/scripts/codex-path-guard.sh",
                ],
                "required_hook_registrations": [
                    {
                        "settings_path": ".claude/settings.json",
                        "event": "PreToolUse",
                        "matcher": "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$",
                        "command": "bash $CLAUDE_PROJECT_DIR/.claude/scripts/pretooluse-gate.sh",
                    },
                    {
                        "settings_path": ".claude/settings.json",
                        "event": "PostToolUse",
                        "matcher": "^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$",
                        "command": "bash $CLAUDE_PROJECT_DIR/.claude/scripts/posttooluse-tracking.sh",
                    },
                    {
                        "settings_path": ".claude/settings.json",
                        "event": "Stop",
                        "command": "bash $CLAUDE_PROJECT_DIR/.claude/scripts/tracking-stop-gate.sh",
                    },
                ],
            },
            "codex": {
                "entrypoint": "CODEX.md",
                "required_files": [
                    "CODEX.md",
                    ".codex/hooks.json",
                    ".claude/scripts/readiness.sh",
                    ".claude/scripts/gate_lib.py",
                    ".claude/scripts/pretooluse-gate.sh",
                    ".claude/scripts/posttooluse-tracking.sh",
                    ".claude/scripts/tracking-stop-gate.sh",
                    ".claude/scripts/ledger-record.sh",
                    ".claude/scripts/session-brief.sh",
                ],
                "required_hook_registrations": [
                    {
                        "settings_path": ".codex/hooks.json",
                        "event": "PreToolUse",
                        "matcher": "^(Bash|apply_patch|mcp__.*)$",
                        "command": "AEGIS_INVOKING_AGENT=codex bash \"$(git rev-parse --show-toplevel)/.claude/scripts/pretooluse-gate.sh\"",
                    },
                    {
                        "settings_path": ".codex/hooks.json",
                        "event": "PostToolUse",
                        "matcher": "^(Bash|apply_patch|mcp__.*)$",
                        "command": "AEGIS_INVOKING_AGENT=codex bash \"$(git rev-parse --show-toplevel)/.claude/scripts/posttooluse-tracking.sh\"",
                    },
                ],
            },
        },
        "conditional_gates": {
            "agents.claude.enabled": [
                "claude.readiness",
                "claude.pretooluse",
                "claude.posttooluse_tracking",
                "claude.stop_tracking",
                "claude.bash_command",
                "claude.protected_path",
            ],
            "agents.codex.enabled": [
                "codex.readiness",
                "codex.pretooluse",
                "codex.posttooluse_tracking",
                "codex.posttooluse_ledger",
                "codex.session_brief",
                "codex.stop_tracking",
                "codex.apply_patch",
                "codex.hook_trust",
                "codex.guard",
                "codex.work_tracking_audit",
            ],
        },
        "verification": {
            "required_commands": [
                "aegis verify",
            ],
            "optional_smoke_tests": [
                "cold-session mutation blocked",
                "Aegis-native kickoff reaches READY without Taskmaster or Serena",
                "READY evidence write allowed",
            ],
        },
    }


def valid_install_plan() -> dict:
    return {
        "schema_version": "1.0.0",
        "plan_id": "aegis-generic-20260516",
        "generated_at": "2026-05-16T11:46:53+02:00",
        "target_root": ".",
        "profile": "generic",
        "mode": "dry_run",
        "apply_confirmed": False,
        "agent_selection": {
            "source": "non_interactive",
            "primary_agent": "claude",
            "enabled_agents": [
                "claude",
            ],
            "explicit_flags_required": True,
        },
        "operations": [
            {
                "action": "create",
                "path": ".aegis/foundation-manifest.json",
                "classification": "create",
                "safe_to_apply": True,
                "managed": True,
                "reason": "Aegis manifest is missing.",
            },
            {
                "action": "manual-review",
                "path": "CLAUDE.md",
                "classification": "manual-review",
                "safe_to_apply": False,
                "managed": False,
                "reason": "Existing Claude entrypoint requires review before overwrite.",
            },
        ],
        "expected_manifest": {
            "path": ".aegis/foundation-manifest.json",
            "profile": "generic",
            "primary_agent": "claude",
            "agents": {
                "claude": {
                    "enabled": True,
                    "gate_ids": [
                        "claude.readiness",
                        "claude.pretooluse",
                        "claude.posttooluse_tracking",
                        "claude.stop_tracking",
                        "claude.bash_command",
                        "claude.protected_path",
                    ],
                },
            },
            "gates": [
                "claude.readiness",
                "claude.pretooluse",
                "claude.posttooluse_tracking",
                "claude.stop_tracking",
                "claude.bash_command",
                "claude.protected_path",
            ],
        },
        "verification_requirements": [
            {
                "gate_id": "claude.readiness",
                "required": True,
                "enforcement": "mechanical",
                "failure_mode": "fail",
            },
            {
                "gate_id": "mcp.memory_write",
                "required": False,
                "enforcement": "policy",
                "failure_mode": "unsupported",
            },
        ],
        "reports": {
            "plan_json": ".aegis/reports/install-plan.json",
            "install_json": None,
            "verification_json": None,
            "markdown": ".aegis/reports/install-plan.md",
        },
        "summary": {
            "creates": 1,
            "modifies": 0,
            "skips": 0,
            "conflicts": 0,
            "manual_reviews": 1,
        },
    }


@pytest.mark.parametrize(
    "schema_name",
    [
        "foundation-manifest.schema.json",
        "profile.schema.json",
        "install-plan.schema.json",
        "delivery-policy.schema.json",
    ],
)
def test_aegis_schemas_are_valid_draft_2020_12(schema_name: str) -> None:
    Draft202012Validator.check_schema(load_schema(schema_name))


def test_valid_aegis_payloads_match_schemas() -> None:
    validate("foundation-manifest.schema.json", valid_manifest())
    validate("profile.schema.json", valid_profile())
    validate("install-plan.schema.json", valid_install_plan())
    validate(
        "delivery-policy.schema.json",
        json.loads((REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8")),
    )


def test_delivery_policy_rejects_unknown_authority_and_merge_modes() -> None:
    payload = json.loads((REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8"))
    payload["mode"] = "unrestricted"
    payload["merge"]["method"] = "merge"

    with pytest.raises(ValidationError):
        validate("delivery-policy.schema.json", payload)


def test_manifest_rejects_unknown_top_level_properties() -> None:
    payload = valid_manifest()
    payload["legacy_foundation"] = True

    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate("foundation-manifest.schema.json", payload)


def test_manifest_rejects_direct_aegis_writes() -> None:
    payload = valid_manifest()
    payload["access_policy"]["direct_aegis_writes"] = True

    with pytest.raises(ValidationError):
        validate("foundation-manifest.schema.json", payload)


def test_manifest_rejects_missing_required_claude_gate_when_claude_enabled() -> None:
    payload = valid_manifest()
    payload["gates"] = [gate for gate in payload["gates"] if gate["id"] != "claude.protected_path"]

    with pytest.raises(ValidationError):
        validate("foundation-manifest.schema.json", payload)


def test_manifest_rejects_required_gate_that_only_warns() -> None:
    payload = valid_manifest()
    payload["gates"][0]["verification"]["failure_mode"] = "warn"

    with pytest.raises(ValidationError):
        validate("foundation-manifest.schema.json", payload)


def test_manifest_rejects_required_policy_only_gate() -> None:
    payload = valid_manifest()
    policy_gate = copy.deepcopy(payload["gates"][-1])
    policy_gate["id"] = "mcp.unhookable_write"
    policy_gate["required"] = True
    payload["gates"].append(policy_gate)

    with pytest.raises(ValidationError):
        validate("foundation-manifest.schema.json", payload)


def test_profile_generic_requires_claude_default() -> None:
    payload = valid_profile()
    payload["default_primary_agent"] = "codex"

    with pytest.raises(ValidationError):
        validate("profile.schema.json", payload)


def test_profile_generic_requires_agent_selection_prompt() -> None:
    payload = valid_profile()
    payload["agent_selection_required"] = False

    with pytest.raises(ValidationError):
        validate("profile.schema.json", payload)


def test_profile_generic_requires_claude_hook_gate_set() -> None:
    payload = valid_profile()
    payload["conditional_gates"]["agents.claude.enabled"].remove("claude.bash_command")

    with pytest.raises(ValidationError):
        validate("profile.schema.json", payload)


def test_install_plan_requires_explicit_flags_for_non_interactive_agent_selection() -> None:
    payload = valid_install_plan()
    payload["agent_selection"]["explicit_flags_required"] = False

    with pytest.raises(ValidationError):
        validate("install-plan.schema.json", payload)


def test_install_plan_apply_mode_requires_apply_confirmation() -> None:
    payload = valid_install_plan()
    payload["mode"] = "apply"

    with pytest.raises(ValidationError):
        validate("install-plan.schema.json", payload)

    payload["apply_confirmed"] = True
    validate("install-plan.schema.json", payload)


def test_install_plan_rejects_required_policy_only_verification_requirement() -> None:
    payload = valid_install_plan()
    payload["verification_requirements"][-1]["required"] = True

    with pytest.raises(ValidationError):
        validate("install-plan.schema.json", payload)
