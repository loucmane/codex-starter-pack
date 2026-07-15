"""Tests for the Aegis Foundation installer CLI/core prototype."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from aegis_foundation import cli as aegis_cli
from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import (
    AEGIS_MANIFEST_REL,
    AEGIS_CLOSEOUT_REPORT_REL,
    AEGIS_CURRENT_WORK_REL,
    AEGIS_CLIENT_RELOAD_REL,
    AEGIS_DEGRADED_EVENTS_REL,
    AEGIS_ENFORCEMENT_REL,
    AEGIS_GATE_DECISIONS_REL,
    AEGIS_LOCAL_TASKS_REL,
    AEGIS_OBSERVATION_REPORT_REL,
    AEGIS_RUNTIME_ENV_REL,
    AEGIS_PENDING_TRACKING_REL,
    AEGIS_RELEASE_CERT_REPORT_REL,
    AEGIS_REPAIR_REPORT_REL,
    AEGIS_UPDATE_REPORT_REL,
    AEGIS_VERIFY_REPORT_REL,
    AegisError,
    certify_release_candidate,
    closeout,
    doctor,
    enforce_mode,
    enforcement_status,
    initialize_project,
    install,
    inspect_project,
    kickoff,
    log_work,
    next_action,
    plan_install,
    project_update,
    reconcile,
    repair,
    repair_handoff,
    runtime_status,
    runtime_update,
    status,
    start_observation,
    start_local_work,
    stop_observation,
    uninstall,
    verify,
)
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schemas" / "aegis"
RECONCILE_MUTATION_FLAGS = (
    "--apply",
    "--auto",
    "--auto-fix",
    "--fix",
    "--set-status",
    "--status",
    "--done",
    "--closeout",
    "--mutate",
    "--write",
    "--push",
)


def load_blog_completed_delivery_fixture() -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "tests/fixtures/aegis/blog-task67-completed-delivery.json").read_text(
            encoding="utf-8"
        )
    )


def load_blog_task40_advisory_pending_fixture() -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "tests/fixtures/aegis/blog-task40-advisory-pending-closeout.json").read_text(
            encoding="utf-8"
        )
    )


def load_task_module():
    name = "codex_task_aegis_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/codex-task")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def validate_schema(schema_name: str, payload: dict) -> None:
    schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def write_managed_baseline(target: Path, rel_path: str, content: bytes) -> None:
    """Simulate bytes installed by an older Aegis manifest."""

    (target / rel_path).write_bytes(content)
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(
        item
        for item in manifest["managed_files"]
        if isinstance(item, dict) and item.get("path") == rel_path
    )
    record["checksum"] = aegis_installer._content_checksum(content)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def managed_entrypoint_content(text: str, begin_marker: str, end_marker: str) -> str:
    """Return marker-delimited guidance, or the complete fresh entrypoint."""

    if begin_marker not in text or end_marker not in text:
        return text
    return text.split(begin_marker, 1)[1].split(end_marker, 1)[0].strip("\n")


def replace_managed_entrypoint_content(
    text: str,
    begin_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    before, marker, remainder = text.partition(begin_marker)
    assert marker, f"missing begin marker {begin_marker}"
    _managed, marker, after = remainder.partition(end_marker)
    assert marker, f"missing end marker {end_marker}"
    return f"{before}{begin_marker}\n{replacement.rstrip()}\n{end_marker}{after}"


def assert_mode_aware_entrypoint(text: str) -> None:
    assert "At orientation, inspect enforcement mode once" in text
    assert "aegis enforce status" in text
    assert "## Advisory mode" in text
    assert "## Strict mode" in text
    assert "`aegis brief`" in text
    assert "`aegis witness`" in text
    assert "Do not manually drain advisory pending events" in text
    assert ".aegis/contract.md" in text
    assert "readiness, kickoff, logging, verification, and closeout" in text
    assert "Missing hooks or unsupported clients are degraded coverage" in text

    advisory = text.split("## Advisory mode", 1)[1].split("## Strict mode", 1)[0]
    for commanded_ceremony in (
        "aegis log --",
        "aegis handoff repair",
        "aegis closeout --",
        "--pending-id",
    ):
        assert commanded_ceremony not in advisory

    nonblank_lines = [line for line in text.splitlines() if line.strip()]
    assert len(nonblank_lines) <= aegis_installer.AEGIS_MANAGED_ENTRYPOINT_MAX_NONBLANK_LINES


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/codex-task", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_target_readiness(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(target / ".claude" / "scripts" / "readiness.sh"),
            "--quick",
            "--root",
            str(target),
        ],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_target_pretooluse(target: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "pretooluse-gate.sh")],
        cwd=target,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def run_target_pretooluse_raw(target: Path, payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "pretooluse-gate.sh")],
        cwd=target,
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def simulate_claude_reload(target: Path) -> None:
    """Run an installed PreToolUse hook once to prove Claude hooks are active."""
    result = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_next",
            "tool_input": {"target_dir": target.as_posix()},
        },
    )
    assert result.returncode == 0, result.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()


def run_target_codex_sessionstart(
    target: Path, state_home: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the installed Codex SessionStart command after its hook has been trusted."""

    resolved_state_home = state_home or (target / ".test-xdg-state")
    return subprocess.run(
        [str(target / ".aegis" / "bin" / "aegis"), "hook", "sessionstart"],
        cwd=target,
        input=json.dumps(
            {
                "session_id": "codex-session-1",
                "turn_id": "codex-turn-1",
                "cwd": target.as_posix(),
                "source": "startup",
                "model": "gpt-5-codex",
                "hook_event_name": "SessionStart",
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            **os.environ,
            "CODEX_THREAD_ID": "codex-session-1",
            "XDG_STATE_HOME": resolved_state_home.as_posix(),
        },
        check=False,
    )


def simulate_codex_reload(target: Path) -> None:
    """Prove trusted Codex SessionStart and canonical apply_patch hooks are active."""

    session_result = run_target_codex_sessionstart(target)
    assert session_result.returncode == 0, session_result.stderr
    marker = target / AEGIS_CLIENT_RELOAD_REL
    if marker.exists():
        payload = json.loads(marker.read_text(encoding="utf-8"))
        assert "codex" not in payload.get("agents", [])

    patch_result = run_target_pretooluse(
        target,
        {
            "tool_name": "apply_patch",
            "tool_input": {
                "command": (
                    "*** Begin Patch\n"
                    "*** Add File: codex-hook-probe.txt\n"
                    "+probe\n"
                    "*** End Patch"
                )
            },
        },
    )
    # Hook execution proves that Codex loaded and trusted the definition. The
    # synthetic mutation may still receive the expected readiness denial on ``main``.
    assert patch_result.returncode in {0, 2}, patch_result.stderr


def configured_hook_commands(payload: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        return commands
    for groups in hooks.values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            for handler in group["hooks"]:
                if isinstance(handler, dict) and isinstance(handler.get("command"), str):
                    commands.append(handler["command"])
    return commands


def run_target_posttooluse(target: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "posttooluse-tracking.sh")],
        cwd=target,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def run_target_stop_gate(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "tracking-stop-gate.sh")],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", repo.as_posix(), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check:
        assert result.returncode == 0, result.stderr or result.stdout
    return result


def init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "aegis@example.invalid")
    git(repo, "config", "user.name", "Aegis Test")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "README.md").write_text("# target\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")


def write_taskmaster_tasks(repo: Path, tasks: list[dict[str, Any]]) -> None:
    task_dir = repo / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "tasks.json").write_text(
        json.dumps({"master": {"tasks": tasks}}, indent=2) + "\n", encoding="utf-8"
    )


def write_taskmaster_payload(repo: Path, payload: object | str) -> None:
    task_dir = repo / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n"
    (task_dir / "tasks.json").write_text(text, encoding="utf-8")


def commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(repo, "add", rel_path)
    git(repo, "commit", "-m", message)


def assert_reconcile_preserved_whole_tree(target: Path, before) -> None:
    before.assert_matches(snapshot_whole_tree(target))


def test_build_parser_accepts_aegis_commands() -> None:
    module = load_task_module()
    parser = module.build_parser()

    inspect_args = parser.parse_args(["aegis", "inspect", "--target-dir", "/tmp/example"])
    assert inspect_args.command == "aegis"
    assert inspect_args.subcommand == "inspect"
    assert inspect_args.target_dir == "/tmp/example"

    plan_args = parser.parse_args(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            "/tmp/example",
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )
    assert plan_args.primary_agent == "claude"
    assert plan_args.agent == ["claude"]

    init_args = parser.parse_args(["aegis", "init", "--target-dir", "/tmp/example"])
    assert init_args.subcommand == "init"
    assert init_args.primary_agent == "claude"
    assert init_args.agent is None

    start_args = parser.parse_args(["aegis", "start", "Improve BrandMark accessibility"])
    assert start_args.subcommand == "start"
    assert start_args.title == "Improve BrandMark accessibility"

    observe_start_args = parser.parse_args(
        ["aegis", "observe", "start", "Polish audit", "--slug", "polish-audit"]
    )
    assert observe_start_args.subcommand == "observe"
    assert observe_start_args.observe_subcommand == "start"
    assert observe_start_args.title == "Polish audit"
    assert observe_start_args.slug == "polish-audit"

    observe_stop_args = parser.parse_args(
        [
            "aegis",
            "observe",
            "stop",
            "--summary",
            "Observed app shell",
            "--allow-dirty",
            "--collect-artifacts",
        ]
    )
    assert observe_stop_args.subcommand == "observe"
    assert observe_stop_args.observe_subcommand == "stop"
    assert observe_stop_args.summary == "Observed app shell"
    assert observe_stop_args.allow_dirty is True
    assert observe_stop_args.collect_artifacts is True

    install_args = parser.parse_args(
        [
            "aegis",
            "install",
            "--target-dir",
            "/tmp/example",
            "--primary-agent",
            "multi",
            "--agent",
            "claude",
            "--agent",
            "codex",
            "--apply",
        ]
    )
    assert install_args.apply is True
    assert install_args.agent == ["claude", "codex"]

    verify_args = parser.parse_args(["aegis", "verify", "--target-dir", "/tmp/example", "--strict"])
    assert verify_args.subcommand == "verify"
    assert verify_args.strict is True

    next_args = parser.parse_args(["aegis", "next", "--target-dir", "/tmp/example"])
    assert next_args.subcommand == "next"
    assert next_args.target_dir == "/tmp/example"

    doctor_args = parser.parse_args(["aegis", "doctor", "--target-dir", "/tmp/example", "--json"])
    assert doctor_args.subcommand == "doctor"
    assert doctor_args.target_dir == "/tmp/example"
    assert doctor_args.json is True

    enforce_status_args = parser.parse_args(
        ["aegis", "enforce", "status", "--target-dir", "/tmp/example"]
    )
    assert enforce_status_args.subcommand == "enforce"
    assert enforce_status_args.enforce_subcommand == "status"
    assert enforce_status_args.target_dir == "/tmp/example"

    enforce_mode_args = parser.parse_args(
        [
            "aegis",
            "enforce",
            "--target-dir",
            "/tmp/example",
            "--mode",
            "advisory",
            "--reason",
            "pause product work",
        ]
    )
    assert enforce_mode_args.subcommand == "enforce"
    assert enforce_mode_args.mode == "advisory"
    assert enforce_mode_args.reason == "pause product work"

    reconcile_args = parser.parse_args(
        [
            "aegis",
            "reconcile",
            "--target-dir",
            "/tmp/example",
            "--base-ref",
            "main",
            "--no-github",
            "--json",
            "--preview-candidates",
        ]
    )
    assert reconcile_args.subcommand == "reconcile"
    assert reconcile_args.target_dir == "/tmp/example"
    assert reconcile_args.base_ref == "main"
    assert reconcile_args.no_github is True
    assert reconcile_args.json is True
    assert reconcile_args.preview_candidates is True

    repair_args = parser.parse_args(
        ["aegis", "repair", "--target-dir", "/tmp/example", "--apply", "--json"]
    )
    assert repair_args.subcommand == "repair"
    assert repair_args.target_dir == "/tmp/example"
    assert repair_args.apply is True
    assert repair_args.json is True

    uninstall_args = parser.parse_args(
        [
            "aegis",
            "uninstall",
            "--target-dir",
            "/tmp/example",
            "--apply",
            "--remove-hook-scripts",
            "--json",
        ]
    )
    assert uninstall_args.subcommand == "uninstall"
    assert uninstall_args.target_dir == "/tmp/example"
    assert uninstall_args.apply is True
    assert uninstall_args.remove_hook_scripts is True
    assert uninstall_args.json is True

    closeout_args = parser.parse_args(
        [
            "aegis",
            "closeout",
            "--target-dir",
            "/tmp/example",
            "--update-handoff",
            "--dry-run",
            "--json",
        ]
    )
    assert closeout_args.subcommand == "closeout"
    assert closeout_args.update_handoff is True
    assert closeout_args.dry_run is True
    assert closeout_args.json is True

    handoff_repair_args = parser.parse_args(
        [
            "aegis",
            "handoff",
            "repair",
            "--target-dir",
            "/tmp/example",
            "--dry-run",
        ]
    )
    assert handoff_repair_args.subcommand == "handoff"
    assert handoff_repair_args.handoff_subcommand == "repair"
    assert handoff_repair_args.target_dir == "/tmp/example"
    assert handoff_repair_args.dry_run is True

    certify_args = parser.parse_args(
        [
            "aegis",
            "certify-release",
            "--source-dir",
            "/tmp/source",
            "--dist-dir",
            "/tmp/dist",
            "--skip-build",
            "--skip-smoke",
        ]
    )
    assert certify_args.subcommand == "certify-release"
    assert certify_args.skip_build is True
    assert certify_args.skip_smoke is True

    kickoff_args = parser.parse_args(
        [
            "aegis",
            "kickoff",
            "--target-dir",
            "/tmp/example",
            "--task",
            "1",
            "--slug",
            "portable-smoke",
            "--title",
            "Portable Smoke",
        ]
    )
    assert kickoff_args.subcommand == "kickoff"
    assert kickoff_args.task == "1"

    kickoff_local_args = parser.parse_args(
        [
            "aegis",
            "kickoff",
            "--target-dir",
            "/tmp/example",
            "--local",
            "--title",
            "Improve BrandMark accessibility",
        ]
    )
    assert kickoff_local_args.local is True
    assert kickoff_local_args.title == "Improve BrandMark accessibility"

    log_args = parser.parse_args(
        [
            "aegis",
            "log",
            "--target-dir",
            "/tmp/example",
            "--handler",
            "claude-test",
            "--evidence",
            "reports/example.txt",
            "--note",
            "Recorded example evidence",
        ]
    )
    assert log_args.subcommand == "log"
    assert log_args.handler == "claude-test"
    assert log_args.plan_step == ""

    profile_args = parser.parse_args(["aegis", "explain-profile"])
    assert profile_args.profile == "generic"


def test_reconcile_cli_parsers_reject_mutation_flags() -> None:
    module = load_task_module()
    codex_parser = module.build_parser()
    package_parser = aegis_cli.build_arg_parser()

    codex_allowed = codex_parser.parse_args(
        [
            "aegis",
            "reconcile",
            "--target-dir",
            "/tmp/example",
            "--base-ref",
            "main",
            "--no-github",
            "--json",
            "--preview-candidates",
        ]
    )
    assert codex_allowed.subcommand == "reconcile"
    assert codex_allowed.target_dir == "/tmp/example"
    assert codex_allowed.base_ref == "main"
    assert codex_allowed.no_github is True
    assert codex_allowed.json is True
    assert codex_allowed.preview_candidates is True

    package_allowed = package_parser.parse_args(
        [
            "reconcile",
            "--target-dir",
            "/tmp/example",
            "--base-ref",
            "main",
            "--no-github",
            "--json",
            "--preview-candidates",
        ]
    )
    assert package_allowed.subcommand == "reconcile"
    assert package_allowed.target_dir == "/tmp/example"
    assert package_allowed.base_ref == "main"
    assert package_allowed.no_github is True
    assert package_allowed.json is True
    assert package_allowed.preview_candidates is True

    package_enforce = package_parser.parse_args(
        ["enforce", "--target-dir", "/tmp/example", "--mode", "strict", "--reason", "resume"]
    )
    assert package_enforce.subcommand == "enforce"
    assert package_enforce.mode == "strict"
    assert package_enforce.reason == "resume"

    for flag in RECONCILE_MUTATION_FLAGS:
        with pytest.raises(SystemExit):
            codex_parser.parse_args(["aegis", "reconcile", flag])
        with pytest.raises(SystemExit):
            package_parser.parse_args(["reconcile", flag])


def test_reconcile_rejects_option_shaped_base_ref(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-invalid-base-ref"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 42, "title": "Cart Button", "status": "pending", "dependencies": []}]
    )

    with pytest.raises(AegisError, match="invalid reconcile base_ref"):
        reconcile(target, source_root=REPO_ROOT, base_ref="--git-dir=/tmp/other", use_github=False)


def test_enforce_mode_writes_state_and_surfaces_in_diagnostics(tmp_path: Path) -> None:
    target = tmp_path / "enforce-mode"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="enforce-mode", title="Enforce Mode")

    default_status = enforcement_status(target, source_root=REPO_ROOT)
    assert default_status["status"] == "strict"
    assert default_status["enforcement"]["configured"] is False

    updated = enforce_mode(
        target,
        source_root=REPO_ROOT,
        mode="advisory",
        reason="product work",
        set_by="pytest",
    )

    assert updated["status"] == "updated"
    assert updated["previous_mode"] == "strict"
    state = json.loads((target / AEGIS_ENFORCEMENT_REL).read_text(encoding="utf-8"))
    assert state == {
        "mode": "advisory",
        "set_at": updated["updated_at"],
        "set_by": "pytest",
        "reason": "product work",
    }

    status_report = status(target, source_root=REPO_ROOT)
    assert status_report["enforcement"]["mode"] == "advisory"
    assert "advisory" in status_report["recommended_actions"][0]
    diagnosis = doctor(target, source_root=REPO_ROOT)
    assert diagnosis["enforcement"]["mode"] == "advisory"
    assert diagnosis["status"] == "degraded"
    assert any(
        check["id"] == "runtime.enforcement_mode" and check["status"] == "fail"
        for check in diagnosis["checks"]
    )
    verification = verify(target, source_root=REPO_ROOT, dry_run=True)
    assert verification["enforcement"]["mode"] == "advisory"
    assert verification["summary"]["warnings"] >= 1
    assert any(
        check["gate_id"] == "runtime.enforcement_mode" and check["status"] == "warn"
        for check in verification["checks"]
    )

    advisory_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": ".claude/settings.json", "content": "{}"},
        },
    )
    assert advisory_gate.returncode == 0
    decisions = [
        json.loads(line)
        for line in (target / AEGIS_GATE_DECISIONS_REL).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert decisions[-1]["hook"] == "pretooluse"
    assert decisions[-1]["verdict"] == "would_block"
    assert decisions[-1]["reason"] == "protected_path"

    (target / AEGIS_PENDING_TRACKING_REL).write_text(
        json.dumps({"events": [{"id": "adv1", "mode": "advisory"}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    strict = enforce_mode(
        target,
        source_root=REPO_ROOT,
        mode="strict",
        reason="resume strict",
        set_by="pytest",
    )
    assert strict["enforcement"]["mode"] == "strict"
    assert strict["pending"]["advisory"] == 1
    assert strict["pending"]["classification"] == "advisory_only"
    assert strict["pending"]["delivery_allowed"] is True
    assert strict["workflow_guidance"]["strict_reentry"]["suggested_cli"] is None
    assert "preserved audit evidence" in strict["workflow_guidance"]["strict_reentry"]["message"]

    first_strict_payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "src/strict-reentry.txt", "content": "first\n"},
    }
    first_strict_gate = run_target_pretooluse(target, first_strict_payload)
    assert first_strict_gate.returncode == 0, first_strict_gate.stderr
    first_strict_tracking = run_target_posttooluse(target, first_strict_payload)
    assert first_strict_tracking.returncode == 0, first_strict_tracking.stderr
    mixed = aegis_installer._classify_pending_tracking(target)
    assert mixed["classification"] == "mixed"
    assert mixed["counts"] == {
        "total": 2,
        "advisory": 1,
        "required": 1,
        "unknown": 0,
    }

    second_strict_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/strict-reentry-2.txt", "content": "second\n"},
        },
    )
    assert second_strict_gate.returncode == 2
    assert "pending S:W:H:E tracking" in second_strict_gate.stderr


def test_pending_tracking_classifier_is_fail_closed_and_provenance_aware(
    tmp_path: Path,
) -> None:
    target = tmp_path / "pending-classifier"
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True)

    cases: list[tuple[str, str, str, bool, bool, int, int, int]] = [
        ("empty", '{"events": []}\n', "empty", True, True, 0, 0, 0),
        (
            "advisory",
            '{"events": [{"id": "adv-1", "mode": "advisory"}]}\n',
            "advisory_only",
            True,
            True,
            1,
            0,
            0,
        ),
        (
            "required",
            '{"events": [{"id": "req-1", "mode": "strict"}]}\n',
            "required_only",
            True,
            False,
            0,
            1,
            0,
        ),
        (
            "mixed",
            (
                '{"events": [{"id": "adv-1", "mode": "advisory"}, '
                '{"id": "req-1", "mode": "strict"}]}\n'
            ),
            "mixed",
            True,
            False,
            1,
            1,
            0,
        ),
        (
            "missing provenance",
            '{"events": [{"id": "unknown-1"}]}\n',
            "unknown",
            True,
            False,
            0,
            0,
            1,
        ),
        (
            "unknown provenance",
            '{"events": [{"id": "unknown-1", "mode": "shadow"}]}\n',
            "unknown",
            True,
            False,
            0,
            0,
            1,
        ),
        (
            "invalid event shape",
            '{"events": [42]}\n',
            "unknown",
            False,
            False,
            0,
            0,
            1,
        ),
        (
            "non-list queue",
            '{"events": {}}\n',
            "malformed",
            False,
            False,
            0,
            0,
            0,
        ),
        ("invalid json", "{", "malformed", False, False, 0, 0, 0),
        ("non-object payload", "[]\n", "malformed", False, False, 0, 0, 0),
    ]

    for (
        label,
        raw,
        classification,
        queue_valid,
        delivery_allowed,
        advisory_count,
        required_count,
        unknown_count,
    ) in cases:
        pending_path.write_text(raw, encoding="utf-8")
        state = aegis_installer._classify_pending_tracking(target)
        assert state["classification"] == classification, label
        assert state["queue_valid"] is queue_valid, label
        assert state["delivery_allowed"] is delivery_allowed, label
        assert state["counts"]["advisory"] == advisory_count, label
        assert state["counts"]["required"] == required_count, label
        assert state["counts"]["unknown"] == unknown_count, label
        check = aegis_installer._strict_pending_tracking_check(target)
        assert (check["status"] == "pass") is delivery_allowed, label
        assert check["details"]["classification"] == classification, label

    pending_path.unlink()
    absent = aegis_installer._classify_pending_tracking(target)
    assert absent["classification"] == "absent"
    assert absent["queue_valid"] is True
    assert absent["delivery_allowed"] is True


def test_blog_task40_advisory_pending_replay_allows_delivery_and_preserves_queue(
    tmp_path: Path,
) -> None:
    fixture = load_blog_task40_advisory_pending_fixture()
    target = tmp_path / "blog-task40-replay"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="40", slug="blog-task40-replay", title="Blog Task 40 Replay")
    enforce_mode(
        target,
        source_root=REPO_ROOT,
        mode="advisory",
        reason="Task 251 fixture",
        set_by="pytest",
    )
    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    work_rel = current_work["paths"]["work_tracking"]
    implementation_evidence = f"{current_work['paths']['reports']}/implementation.txt"
    (target / implementation_evidence).write_text("implementation\n", encoding="utf-8")
    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed Blog Task 40 replay scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=implementation_evidence,
        note="Recorded fixture implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    initial_verify = verify(target, source_root=REPO_ROOT, strict=True)
    assert initial_verify["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    repaired = repair_handoff(target, source_root=REPO_ROOT)
    assert repaired["status"] == "repaired"
    assert closeout(target, source_root=REPO_ROOT, dry_run=True)["status"] == "passed"

    count = fixture["reproduction"]["pending_event_count"]
    events = [
        {
            "id": f"blog40-advisory-{index:03d}",
            "created_at": "2026-07-14T00:00:00Z",
            "updated_at": "2026-07-14T00:00:00Z",
            "tool": "Bash" if index % 2 == 0 else "apply_patch",
            "handler": "codex:Bash" if index % 2 == 0 else "codex:apply_patch",
            "evidence": f"fixture/path-{index}.txt",
            "task": {"id": "40", "slug": "blog-task40-replay"},
            "mode": fixture["reproduction"]["pending_event_mode"],
        }
        for index in range(count)
    ]
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-07-14T00:00:00Z",
                "events": events,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    pending_before = pending_path.read_bytes()

    strict = verify(target, source_root=REPO_ROOT, strict=True, dry_run=True)
    assert strict["status"] == "passed"
    pending_check = next(
        check for check in strict["checks"] if check["gate_id"] == "mutation.pending_tracking_empty"
    )
    assert pending_check["status"] == "pass"
    assert pending_check["details"]["classification"] == fixture["expected"]["classification"]
    assert pending_check["details"]["counts"]["total"] == count
    assert pending_path.read_bytes() == pending_before

    diagnosis = doctor(target, source_root=REPO_ROOT)
    assert diagnosis["current_state"] != "pending_tracking"
    guidance = next_action(target, source_root=REPO_ROOT)
    assert guidance["state"] != "pending_tracking"

    before_dry_run = snapshot_whole_tree(target)
    dry_run = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    after_dry_run = snapshot_whole_tree(target)
    before_dry_run.assert_matches(after_dry_run)
    assert dry_run["status"] == "passed"
    assert dry_run["pending_tracking"]["classification"] == "advisory_only"
    assert dry_run["pending_tracking"]["counts"]["total"] == count
    assert dry_run["pending_tracking"]["advisory_preserved"] is True
    assert dry_run["pending_tracking"]["required_unresolved"] is False
    assert len(dry_run["pending_tracking"]["sample"]) == 5
    assert dry_run["pending_tracking"]["sample_truncated"] is True
    assert not any(
        item["kind"] == "pending_tracking_event" for item in dry_run["repair_guidance"]["items"]
    )

    completed = closeout(target, source_root=REPO_ROOT, update_handoff=True)
    assert completed["status"] == "passed"
    assert completed["pending_tracking"]["classification"] == "advisory_only"
    assert completed["pending_tracking"]["counts"]["total"] == count
    assert pending_path.read_bytes() == pending_before
    assert json.loads((target / AEGIS_ENFORCEMENT_REL).read_text(encoding="utf-8"))["mode"] == (
        "advisory"
    )


def test_reconcile_reports_git_merged_task_that_taskmaster_has_not_marked_done(
    tmp_path: Path,
) -> None:
    target = tmp_path / "reconcile-merged-not-done"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 42, "title": "Cart Button", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-42-cart-button")
    commit_file(target, "feature.txt", "cart\n", "task 42")
    git(target, "switch", "main")
    git(target, "merge", "--no-ff", "feat/task-42-cart-button", "-m", "merge task 42")
    status_before = git(target, "status", "--short").stdout
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert report["read_only"] is True
    assert git(target, "status", "--short").stdout == status_before
    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["status"] == "drift"
    assert report["summary"]["errors"] == 1
    finding = report["findings"][0]
    assert finding["kind"] == "merged_but_not_done"
    assert finding["task_id"] == "42"
    assert finding["evidence"]["merge_truth"]["proof"] == "git_ancestor"
    assert "Aegis reconcile: DRIFT" in aegis_installer.format_reconcile_summary(report)


def test_reconcile_uses_github_merged_pr_to_handle_squash_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-squash-gh"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 43, "title": "Squashed Feature", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-43-squashed-feature")
    commit_file(target, "feature.txt", "squash\n", "task 43")
    git(target, "switch", "main")
    git(target, "merge", "--squash", "feat/task-43-squashed-feature")
    git(target, "commit", "-m", "squash task 43")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": True,
            "reason": "",
            "prs": [
                {
                    "number": 43,
                    "state": "MERGED",
                    "title": "Task 43 squashed feature",
                    "headRefName": "feat/task-43-squashed-feature",
                    "baseRefName": "main",
                    "mergedAt": "2026-06-02T10:00:00Z",
                    "url": "https://example.invalid/pr/43",
                    "isDraft": False,
                }
            ],
        },
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    finding = next(item for item in report["findings"] if item["kind"] == "merged_but_not_done")
    assert finding["evidence"]["merge_truth"]["proof"] == "github_pr_merged"
    task = next(item for item in report["tasks"] if item["task_id"] == "43")
    assert task["merge_truth"]["branches"][0]["proof"] == "git_non_ancestor"


def test_reconcile_keeps_squash_ambiguous_git_only_case_unknown(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-squash-offline"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 44, "title": "Offline Squash", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-44-offline-squash")
    commit_file(target, "feature.txt", "offline\n", "task 44")
    git(target, "switch", "main")
    git(target, "merge", "--squash", "feat/task-44-offline-squash")
    git(target, "commit", "-m", "squash task 44")
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["status"] == "clean"
    assert not [
        finding for finding in report["findings"] if finding["kind"] == "merged_but_not_done"
    ]
    task = next(item for item in report["tasks"] if item["task_id"] == "44")
    assert task["merge_truth"]["status"] == "unknown"
    assert task["merge_truth"]["proof"] == "git_only_non_ancestor_or_missing_base"


def test_reconcile_keeps_done_git_only_unknown_as_task_detail_not_finding(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-done-offline-unknown"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 441, "title": "Done Offline", "status": "done", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-441-stale-local-branch")
    commit_file(target, "feature.txt", "offline done\n", "task 441")
    git(target, "switch", "main")
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["status"] == "clean"
    assert not report["findings"]
    task = next(item for item in report["tasks"] if item["task_id"] == "441")
    assert task["merge_truth"]["status"] == "unknown"
    assert task["merge_truth"]["proof"] == "git_only_non_ancestor_or_missing_base"


def test_reconcile_reports_done_task_with_open_pr_as_not_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-done-open-pr"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 45, "title": "Open PR", "status": "done", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-45-open-pr")
    commit_file(target, "feature.txt", "open\n", "task 45")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": True,
            "reason": "",
            "prs": [
                {
                    "number": 45,
                    "state": "OPEN",
                    "title": "Task 45 open PR",
                    "headRefName": "feat/task-45-open-pr",
                    "baseRefName": "main",
                    "mergedAt": None,
                    "url": "https://example.invalid/pr/45",
                    "isDraft": False,
                }
            ],
        },
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    finding = next(item for item in report["findings"] if item["kind"] == "done_but_not_merged")
    assert finding["task_id"] == "45"
    assert finding["evidence"]["merge_truth"]["proof"] == "github_pr_open"


def test_reconcile_reports_abandoned_branches_stubs_and_multi_pr_ambiguity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-stubs"
    init_git_repo(target)
    write_taskmaster_tasks(
        target,
        [
            {"id": 46, "title": "In Progress", "status": "in-progress", "dependencies": []},
            {"id": 47, "title": "Ambiguous Epic", "status": "pending", "dependencies": []},
        ],
    )
    git(target, "switch", "-c", "feat/task-46-abandoned")
    commit_file(target, "task46.txt", "abandoned\n", "task 46")
    git(target, "switch", "main")
    git(target, "switch", "-c", "feat/task-999-local-stub")
    commit_file(target, "stub.txt", "stub\n", "task 999")
    git(target, "switch", "main")
    (target / ".aegis" / "state").mkdir(parents=True)
    (target / ".aegis" / "state" / "local-tasks.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tasks": [
                    {
                        "id": "1000",
                        "title": "Ad hoc local task",
                        "status": "in-progress",
                        "slug": "ad-hoc",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": True,
            "reason": "",
            "prs": [
                {
                    "number": 470,
                    "state": "OPEN",
                    "title": "Task 47 part A",
                    "headRefName": "feat/task-47-part-a",
                    "baseRefName": "main",
                    "mergedAt": None,
                    "url": "https://example.invalid/pr/470",
                    "isDraft": False,
                },
                {
                    "number": 471,
                    "state": "OPEN",
                    "title": "Task 47 part B",
                    "headRefName": "feat/task-47-part-b",
                    "baseRefName": "main",
                    "mergedAt": None,
                    "url": "https://example.invalid/pr/471",
                    "isDraft": False,
                },
            ],
        },
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)
    assert_reconcile_preserved_whole_tree(target, tree_before)
    kinds = {finding["kind"] for finding in report["findings"]}

    assert "abandoned_in_progress_branch" in kinds
    assert "stale_local_stub" in kinds
    assert "local_ad_hoc_stub" in kinds
    assert "multi_pr_epic_ambiguity" in kinds


def test_reconcile_preserves_whole_tree_with_malformed_taskmaster_state(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-malformed-taskmaster"
    init_git_repo(target)
    task_dir = target / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True)
    (task_dir / "tasks.json").write_text("{not json\n", encoding="utf-8")
    git(target, "switch", "-c", "feat/task-77-malformed-taskmaster")
    commit_file(target, "task77.txt", "malformed taskmaster\n", "task 77")
    git(target, "switch", "main")
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["read_only"] is True
    assert report["taskmaster"]["state"] == "invalid"
    assert report["taskmaster"]["present"] is True
    assert report["taskmaster"]["valid"] is False
    assert report["taskmaster"]["reason"] == "json_decode_error"
    assert {finding["kind"] for finding in report["findings"]} == {"taskmaster_invalid"}


def test_reconcile_preserves_whole_tree_when_github_metadata_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-github-unavailable"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 78, "title": "GitHub Unavailable", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-78-github-unavailable")
    commit_file(target, "feature.txt", "github unavailable\n", "task 78")
    git(target, "switch", "main")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": False, "reason": "gh unavailable", "prs": []},
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["read_only"] is True
    assert report["github"]["enabled"] is True
    assert report["github"]["available"] is False
    assert report["github"]["reason"] == "gh unavailable"
    task = next(item for item in report["tasks"] if item["task_id"] == "78")
    assert task["merge_truth"]["status"] == "unknown"


def test_public_init_installs_with_default_claude_adapter(tmp_path: Path) -> None:
    target = tmp_path / "public-init"
    target.mkdir()

    payload = initialize_project(target, source_root=REPO_ROOT)

    assert payload["status"] == "initialized"
    assert payload["agent_selection"] == {
        "source": "public_defaults",
        "primary_agent": "claude",
        "enabled_agents": ["claude"],
    }
    assert payload["install"]["status"] == "applied"
    assert payload["verification"]["status"] == "passed"
    assert payload["public_commands"]["start"] == 'aegis start "<task title>"'
    assert (target / AEGIS_MANIFEST_REL).exists()
    assert (target / ".claude" / "settings.json").exists()
    assert (target / AEGIS_VERIFY_REPORT_REL).exists()


def test_doctor_reports_installed_no_current_work_without_mutating(tmp_path: Path) -> None:
    target = tmp_path / "doctor-installed"
    target.mkdir()
    initialize_project(target, source_root=REPO_ROOT)
    repair_report = target / AEGIS_REPAIR_REPORT_REL

    payload = doctor(target, source_root=REPO_ROOT)

    assert payload["read_only"] is True
    assert payload["current_state"] == "installed_no_current_work"
    assert payload["status"] == "healthy"
    assert payload["summary"]["failed_required"] == 0
    assert payload["repair_plan"]["available"] is False
    assert not repair_report.exists()


def test_repair_preview_is_read_only_and_apply_restores_safe_managed_file(tmp_path: Path) -> None:
    target = tmp_path / "repair-missing-shim"
    target.mkdir()
    initialize_project(target, source_root=REPO_ROOT)
    shim = target / ".aegis" / "bin" / "aegis"
    shim.unlink()

    preview = repair(target, source_root=REPO_ROOT)

    assert preview["read_only"] is True
    assert preview["status"] == "preview"
    assert preview["repair_plan"]["safe"] >= 1
    assert any(
        action["kind"] == "restore_managed_file" and action["path"] == ".aegis/bin/aegis"
        for action in preview["repair_plan"]["actions"]
    )
    assert not shim.exists()
    assert not (target / AEGIS_REPAIR_REPORT_REL).exists()

    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert applied["read_only"] is False
    assert applied["status"] == "applied"
    assert shim.is_file()
    assert os.access(shim, os.X_OK)
    assert (target / AEGIS_REPAIR_REPORT_REL).is_file()
    assert applied["postflight"]["summary"]["failed_required"] == 0


def test_repair_recreates_current_symlinks_and_does_not_delete_stale_active_folders(
    tmp_path: Path,
) -> None:
    target = tmp_path / "repair-current-links"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="pointer-repair", title="Pointer Repair")
    stale = target / "docs/ai/work-tracking/active/20990101-task99-stale-ACTIVE"
    stale.mkdir(parents=True)
    (target / "sessions/current").unlink()
    (target / "plans/current").unlink()

    diagnosis = doctor(target, source_root=REPO_ROOT)
    preview = repair(target, source_root=REPO_ROOT)

    assert diagnosis["status"] == "repairable"
    assert any(action["kind"] == "recreate_symlink" for action in preview["repair_plan"]["actions"])
    assert any(check["id"] == "workflow.stale_active_folders" for check in diagnosis["checks"])
    assert stale.is_dir()

    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert applied["status"] == "applied"
    assert (target / "sessions/current").is_symlink()
    assert (target / "plans/current").is_symlink()
    assert stale.is_dir()


def test_repair_archives_stale_completed_observation_active_folder(
    tmp_path: Path,
) -> None:
    target = tmp_path / "repair-completed-observation-active"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kicked = kickoff(
        target,
        task_id="53",
        slug="dogfood-audit-followups",
        title="M4 dogfood iteration milestone",
    )
    stale_rel = "docs/ai/work-tracking/active/20990101-observe-polish-audit-ACTIVE"
    stale = target / stale_rel
    stale.mkdir(parents=True)
    (stale / "TRACKER.md").write_text("Observation tracker\n", encoding="utf-8")
    (stale / "reports" / "polish-audit").mkdir(parents=True)
    report = {
        "schema_version": "1.0.0",
        "status": "completed",
        "mode": "observation",
        "paths": {
            "work_tracking": stale_rel,
            "reports": f"{stale_rel}/reports/polish-audit",
        },
    }
    (target / AEGIS_OBSERVATION_REPORT_REL).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    diagnosis = doctor(target, source_root=REPO_ROOT)
    preview = repair(target, source_root=REPO_ROOT)

    assert any(
        action["kind"] == "archive_completed_observation_work_tracking"
        for action in preview["repair_plan"]["actions"]
    )
    assert any(check["id"] == "workflow.stale_active_folders" for check in diagnosis["checks"])

    applied = repair(target, source_root=REPO_ROOT, apply=True)
    archive_rel = (
        stale_rel.replace(
            "docs/ai/work-tracking/active/",
            "docs/ai/work-tracking/archive/",
        ).removesuffix("-ACTIVE")
        + "-COMPLETED"
    )
    active_folders = sorted(
        path.name
        for path in (target / "docs/ai/work-tracking/active").glob("*-ACTIVE")
        if path.is_dir()
    )
    updated_report = json.loads((target / AEGIS_OBSERVATION_REPORT_REL).read_text(encoding="utf-8"))

    assert applied["status"] == "applied"
    assert not stale.exists()
    assert (target / archive_rel).is_dir()
    assert active_folders == [Path(kicked["paths"]["work_tracking"]).name]
    assert updated_report["paths"]["work_tracking"] == archive_rel
    assert updated_report["archived_work_tracking"] == {"from": stale_rel, "to": archive_rel}


def test_repair_archives_orphaned_observation_active_folder_by_name(
    tmp_path: Path,
) -> None:
    target = tmp_path / "repair-orphaned-observation-active"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kicked = kickoff(
        target,
        task_id="53",
        slug="dogfood-audit-followups",
        title="M4 dogfood iteration milestone",
    )
    stale_rel = (
        "docs/ai/work-tracking/active/20260608-observe-read-only-hp-coach-polish-audit-ACTIVE"
    )
    stale = target / stale_rel
    stale.mkdir(parents=True)
    (stale / "TRACKER.md").write_text("Observation tracker\n", encoding="utf-8")
    report = {
        "schema_version": "1.0.0",
        "status": "completed",
        "mode": "observation",
        "paths": {
            "work_tracking": "docs/ai/work-tracking/archive/old-observation-COMPLETED",
            "reports": "docs/ai/work-tracking/archive/old-observation-COMPLETED/reports/audit",
        },
    }
    (target / AEGIS_OBSERVATION_REPORT_REL).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    preview = repair(target, source_root=REPO_ROOT)

    assert any(
        action["kind"] == "archive_completed_observation_work_tracking"
        and action["path"] == stale_rel
        for action in preview["repair_plan"]["actions"]
    )

    applied = repair(target, source_root=REPO_ROOT, apply=True)
    archive_rel = (
        stale_rel.replace(
            "docs/ai/work-tracking/active/",
            "docs/ai/work-tracking/archive/",
        ).removesuffix("-ACTIVE")
        + "-COMPLETED"
    )
    active_folders = sorted(
        path.name
        for path in (target / "docs/ai/work-tracking/active").glob("*-ACTIVE")
        if path.is_dir()
    )
    updated_report = json.loads((target / AEGIS_OBSERVATION_REPORT_REL).read_text(encoding="utf-8"))

    assert applied["status"] == "applied"
    assert not stale.exists()
    assert (target / archive_rel).is_dir()
    assert active_folders == [Path(kicked["paths"]["work_tracking"]).name]
    assert updated_report["paths"]["work_tracking"] == report["paths"]["work_tracking"]
    assert updated_report["archived_work_tracking"] == {"from": stale_rel, "to": archive_rel}


def test_repair_archives_closed_task_tracker_and_restores_mismatched_current_work(
    tmp_path: Path,
) -> None:
    target = tmp_path / "repair-closed-task-active"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kicked = kickoff(
        target,
        task_id="73",
        slug="p0-poisoned-resume-fallback",
        title="P0: Repair poisoned resume plus graceful drill fallback",
    )
    task73_rel = kicked["paths"]["work_tracking"]
    stale_rel = "docs/ai/work-tracking/active/20260609-task53-dogfood-audit-followups-ACTIVE"
    stale = target / stale_rel
    stale.mkdir(parents=True)
    (stale / "HANDOFF.md").write_text("# Stale #53 handoff\n", encoding="utf-8")
    (stale / "reports" / "dogfood-audit-followups").mkdir(parents=True)
    closeout_report = {
        "schema_version": "1.0.0",
        "status": "passed",
        "checked_at": "2026-06-09T12:55:49Z",
        "closed_at": "2026-06-09T12:55:49Z",
        "current_work": {
            "status": "completed",
            "task": {
                "id": "53",
                "slug": "dogfood-audit-followups",
                "status": "completed",
            },
            "paths": {
                "work_tracking": stale_rel,
                "reports": f"{stale_rel}/reports/dogfood-audit-followups",
            },
        },
    }
    (target / AEGIS_CLOSEOUT_REPORT_REL).write_text(
        json.dumps(closeout_report, indent=2) + "\n",
        encoding="utf-8",
    )
    current_path = target / AEGIS_CURRENT_WORK_REL
    current_work = json.loads(current_path.read_text(encoding="utf-8"))
    current_work["status"] = "completed"
    current_work["task"]["status"] = "completed"
    current_work["closeout_passed_at"] = closeout_report["closed_at"]
    current_work["closeout_report"] = AEGIS_CLOSEOUT_REPORT_REL
    current_path.write_text(json.dumps(current_work, indent=2) + "\n", encoding="utf-8")

    preview = repair(target, source_root=REPO_ROOT)
    action_kinds = {action["kind"] for action in preview["repair_plan"]["actions"]}

    assert "remove_mismatched_closeout_metadata" in action_kinds
    assert "archive_completed_task_work_tracking" in action_kinds
    assert "normalize_completed_closeout" not in action_kinds

    applied = repair(target, source_root=REPO_ROOT, apply=True)
    archive_rel = (
        stale_rel.replace(
            "docs/ai/work-tracking/active/",
            "docs/ai/work-tracking/archive/",
        ).removesuffix("-ACTIVE")
        + "-COMPLETED"
    )
    applied_kinds = {
        item["id"]: item["status"]
        for item in applied["applied"]
        if item["id"]
        in {
            "workflow.remove_mismatched_closeout_metadata",
            "workflow.archive_completed_task_work_tracking",
        }
    }
    active_folders = sorted(
        path.name
        for path in (target / "docs/ai/work-tracking/active").glob("*-ACTIVE")
        if path.is_dir()
    )
    repaired_work = json.loads(current_path.read_text(encoding="utf-8"))
    repaired_closeout = json.loads((target / AEGIS_CLOSEOUT_REPORT_REL).read_text(encoding="utf-8"))

    assert applied_kinds == {
        "workflow.remove_mismatched_closeout_metadata": "applied",
        "workflow.archive_completed_task_work_tracking": "applied",
    }
    assert not stale.exists()
    assert (target / archive_rel).is_dir()
    assert active_folders == [Path(task73_rel).name]
    assert repaired_work["status"] == "in-progress"
    assert repaired_work["task"]["status"] == "in-progress"
    assert repaired_work["paths"]["work_tracking"] == task73_rel
    assert "closeout_passed_at" not in repaired_work
    assert "closeout_report" not in repaired_work
    assert repaired_closeout["current_work"]["paths"]["work_tracking"] == archive_rel
    assert repaired_closeout["archived_work_tracking"] == {"from": stale_rel, "to": archive_rel}
    assert applied["postflight"]["summary"]["failed_required"] == 0


def test_repair_normalizes_malformed_current_plan_table(tmp_path: Path) -> None:
    target = tmp_path / "repair-plan-table"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="plan-table-repair", title="Plan Table Repair")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    plan_path = target / current_work["paths"]["plan"]
    plan_lines = plan_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(plan_lines):
        if line.startswith("| plan-step-scope |"):
            plan_lines[index] = line.replace(
                " | in-progress |",
                "; cmd`python - <<'PY'\nprint('scope | evidence')\nPY` | completed |",
            )
        if line.startswith("| plan-step-verify |"):
            plan_lines[index] = line.replace(
                " | pending |",
                "; cmd`pytest -q\nuv run | tee verification.txt` | completed |",
            )
    plan_path.write_text("\n".join(plan_lines).rstrip() + "\n", encoding="utf-8")

    diagnosis = doctor(target, source_root=REPO_ROOT)
    preview = repair(target, source_root=REPO_ROOT)

    assert diagnosis["status"] == "repairable"
    assert any(
        check["id"] == "workflow.plan_table" and check["status"] == "fail"
        for check in diagnosis["checks"]
    )
    assert any(
        action["kind"] == "normalize_plan_table" and action["path"] == current_work["paths"]["plan"]
        for action in preview["repair_plan"]["actions"]
    )
    assert "print('scope | evidence')" in plan_path.read_text(encoding="utf-8")

    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert applied["status"] == "applied"
    assert any(
        item["id"] == "workflow.normalize_plan_table" and item["status"] == "applied"
        for item in applied["applied"]
    )
    repaired_text = plan_path.read_text(encoding="utf-8")
    assert "scope &#124; evidence" in repaired_text
    assert "uv run &#124; tee verification.txt" in repaired_text
    assert "print('scope | evidence')" not in repaired_text
    rows = aegis_installer._parse_plan_rows(plan_path)
    assert rows["plan-step-scope"]["malformed"] is False
    assert rows["plan-step-scope"]["status"] == "completed"
    assert rows["plan-step-verify"]["malformed"] is False
    assert rows["plan-step-verify"]["status"] == "completed"
    assert doctor(target, source_root=REPO_ROOT)["status"] == "healthy"


def test_repair_apply_is_blocked_while_pending_tracking_exists(tmp_path: Path) -> None:
    target = tmp_path / "repair-pending"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="pending-repair", title="Pending Repair")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "id": "abc123def456",
                        "handler": "claude:Write",
                        "evidence": "src/main.ts",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diagnosis = doctor(target, source_root=REPO_ROOT)
    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert diagnosis["current_state"] == "pending_tracking"
    assert applied["status"] == "blocked"
    assert applied["applied"] == []
    assert pending_path.exists()
    assert not (target / AEGIS_REPAIR_REPORT_REL).exists()


def test_public_start_allocates_local_task_without_taskmaster_or_serena(tmp_path: Path) -> None:
    target = tmp_path / "local-start"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    next_before_start = next_action(target, source_root=REPO_ROOT)
    assert next_before_start["state"] == "client_reload_required"
    assert next_before_start["suggested_mcp_call"]["tool"] == "aegis.next"
    simulate_claude_reload(target)
    next_before_start = next_action(target, source_root=REPO_ROOT)
    # TM 190: no Taskmaster ledger -> no_taskmaster bootstrap state (still offers aegis start
    # for local tracked work, which this test then exercises).
    assert next_before_start["state"] == "no_taskmaster"
    assert next_before_start["suggested_mcp_call"]["tool"] == "aegis.start"
    assert next_before_start["suggested_mcp_call"]["arguments"]["apply"] is True

    bash_start_payload = {
        "tool_name": "Bash",
        "tool_input": {"command": './.aegis/bin/aegis start "Improve BrandMark accessibility"'},
    }
    mcp_start_payload = {
        "tool_name": "mcp__aegis__aegis_start",
        "tool_input": {
            "target_dir": target.as_posix(),
            "title": "Improve BrandMark accessibility",
            "apply": True,
        },
    }
    bash_start_gate = run_target_pretooluse(target, bash_start_payload)
    assert bash_start_gate.returncode == 0, bash_start_gate.stderr
    mcp_start_gate = run_target_pretooluse(target, mcp_start_payload)
    assert mcp_start_gate.returncode == 0, mcp_start_gate.stderr

    payload = start_local_work(
        target, title="Improve BrandMark accessibility", source_root=REPO_ROOT
    )

    assert payload["status"] == "started"
    assert payload["local_task"]["id"] == "1"
    assert payload["task"]["id"] == "1"
    assert payload["task"]["slug"] == "improve-brandmark-accessibility"
    assert payload["branch"]["current"] == "feat/task-1-improve-brandmark-accessibility"
    local_tasks = json.loads((target / AEGIS_LOCAL_TASKS_REL).read_text(encoding="utf-8"))
    assert local_tasks["next_id"] == 2
    assert local_tasks["tasks"][0]["source"] == "aegis-local"
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    assert current_work["task"]["source"] == "aegis-local"
    assert current_work["integrations"]["taskmaster"]["required"] is False
    assert current_work["integrations"]["taskmaster"]["detected"] is False
    assert current_work["integrations"]["serena"]["required"] is False
    assert current_work["integrations"]["serena"]["detected"] is False
    readiness = run_target_readiness(target)
    assert readiness.returncode == 0
    assert "READY | task=1" in readiness.stdout
    assert run_target_posttooluse(target, bash_start_payload).returncode == 0
    assert run_target_posttooluse(target, mcp_start_payload).returncode == 0
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()


def test_observation_mode_allows_pre_task_app_audit_without_task_branch(
    tmp_path: Path,
) -> None:
    target = tmp_path / "observe-taskmaster"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_taskmaster_tasks(
        target,
        [{"id": 18, "title": "Mock exam modes", "status": "pending"}],
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)

    before = next_action(target, source_root=REPO_ROOT)
    # TM 190: a single pending task with nothing started is the first_task_ready bootstrap state
    # (still surfaces observe start for a pre-task audit).
    assert before["state"] == "first_task_ready"
    assert any("observe start" in repair for repair in before["copyable_repairs"])

    observe_payload = {
        "tool_name": "Bash",
        "tool_input": {"command": './.aegis/bin/aegis observe start --target-dir . "Polish audit"'},
    }
    observe_gate = run_target_pretooluse(target, observe_payload)
    assert observe_gate.returncode == 0, observe_gate.stderr

    started = start_observation(target, title="Polish audit", source_root=REPO_ROOT)
    assert started["status"] == "started"
    assert started["mode"] == "observation"
    assert started["branch"]["current"] == "main"
    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    assert current_work["mode"] == "observation"
    assert current_work["branch"]["requires_task_id"] is False
    observation_work_rel = current_work["paths"]["work_tracking"]
    observation_archive_rel = (
        observation_work_rel.replace(
            "docs/ai/work-tracking/active/",
            "docs/ai/work-tracking/archive/",
        ).removesuffix("-ACTIVE")
        + "-COMPLETED"
    )

    readiness = run_target_readiness(target)
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert readiness.stdout.startswith("READY | task=obs-")

    dev_gate = run_target_pretooluse(
        target, {"tool_name": "Bash", "tool_input": {"command": "pnpm -C app dev"}}
    )
    assert dev_gate.returncode == 0, dev_gate.stderr
    browser_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__playwright__browser_navigate",
            "tool_input": {"url": "http://localhost:5173"},
        },
    )
    assert browser_gate.returncode == 0, browser_gate.stderr
    chrome_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__chrome-devtools__take_screenshot",
            "tool_input": {},
        },
    )
    assert chrome_gate.returncode == 0, chrome_gate.stderr

    curl_stdout_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "curl http://localhost:5173/health"}},
    )
    assert curl_stdout_gate.returncode == 0, curl_stdout_gate.stderr
    wget_stdout_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "wget -O- http://localhost:5173/health"}},
    )
    assert wget_stdout_gate.returncode == 0, wget_stdout_gate.stderr
    curl_output_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "curl -o .claude/settings.json http://localhost:5173/health"},
        },
    )
    assert curl_output_gate.returncode == 2
    assert "observation mode only permits observation tooling" in curl_output_gate.stderr
    wget_file_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "wget http://localhost:5173/health"}},
    )
    assert wget_file_gate.returncode == 2
    assert "observation mode only permits observation tooling" in wget_file_gate.stderr

    edit_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "app/src/routes/audit.tsx", "content": "x"},
        },
    )
    assert edit_gate.returncode == 2
    assert "observation mode only permits observation tooling" in edit_gate.stderr
    taskmaster_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": 'task-master add-task --title "Audit finding"'},
        },
    )
    assert taskmaster_gate.returncode == 2
    assert "observation mode only permits observation tooling" in taskmaster_gate.stderr
    rm_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "rm -f audit-home-mobile.png"}},
    )
    assert rm_gate.returncode == 2
    assert "observation mode only permits observation tooling" in rm_gate.stderr
    stop_collect_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": "./.aegis/bin/aegis observe stop --target-dir . --collect-artifacts"
            },
        },
    )
    assert stop_collect_gate.returncode == 0, stop_collect_gate.stderr

    post = run_target_posttooluse(
        target, {"tool_name": "Bash", "tool_input": {"command": "pnpm -C app dev"}}
    )
    assert post.returncode == 0, post.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    stopped = stop_observation(target, summary="Observed app shell", source_root=REPO_ROOT)
    assert stopped["status"] == "completed"
    assert stopped["unexpected_changes"] == []
    assert stopped["archived_work_tracking"] == {
        "from": observation_work_rel,
        "to": observation_archive_rel,
    }
    assert not (target / observation_work_rel).exists()
    assert (target / observation_archive_rel).is_dir()
    completed_current_work = json.loads(
        (target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8")
    )
    assert completed_current_work["paths"]["work_tracking"] == observation_archive_rel
    observation_report = json.loads(
        (target / AEGIS_OBSERVATION_REPORT_REL).read_text(encoding="utf-8")
    )
    assert observation_report["paths"]["work_tracking"] == observation_archive_rel
    diagnosis = doctor(target, source_root=REPO_ROOT)
    assert diagnosis["current_state"] == "observation_completed"
    assert diagnosis["status"] == "healthy"

    completed_next = next_action(target, source_root=REPO_ROOT)
    assert completed_next["state"] == "observation_completed"
    assert completed_next["suggested_mcp_call"]["tool"] == "aegis.kickoff"
    assert not any("observe stop" in repair for repair in completed_next["copyable_repairs"])

    completed_readiness = run_target_readiness(target)
    assert completed_readiness.returncode == 2
    assert "branch 'main' does not contain a task ID" in completed_readiness.stdout
    assert "observation current work is missing id" not in completed_readiness.stdout

    completed_taskmaster_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": 'task-master add-task --title "Audit finding"'},
        },
    )
    assert completed_taskmaster_gate.returncode == 2
    assert "Aegis readiness is BLOCKED" in completed_taskmaster_gate.stderr
    assert (
        "observation mode only permits observation tooling" not in completed_taskmaster_gate.stderr
    )

    idempotent_stop = stop_observation(
        target, summary="Observed app shell again", source_root=REPO_ROOT
    )
    assert idempotent_stop["status"] == "completed"
    assert idempotent_stop["idempotent"] is True
    assert idempotent_stop["already_completed"] is True

    kicked = kickoff(
        target,
        task_id="53",
        slug="dogfood-audit-followups",
        title="M4 dogfood iteration milestone",
    )
    active_folders = sorted(
        path.name
        for path in (target / "docs/ai/work-tracking/active").glob("*-ACTIVE")
        if path.is_dir()
    )
    assert active_folders == [Path(kicked["paths"]["work_tracking"]).name]


def test_observation_stop_blocks_unexpected_delta_and_allow_dirty_overrides(
    tmp_path: Path,
) -> None:
    target = tmp_path / "observe-dirty"
    init_git_repo(target)
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Dirty audit", source_root=REPO_ROOT)

    (target / "src" / "audit.ts").parent.mkdir(parents=True, exist_ok=True)
    (target / "src" / "audit.ts").write_text("export const audit = true;\n", encoding="utf-8")
    blocked = stop_observation(target, summary="Unexpected source file", source_root=REPO_ROOT)
    assert blocked["status"] == "blocked"
    assert "?? src/audit.ts" in blocked["unexpected_changes"]

    completed = stop_observation(
        target,
        summary="Accepted dirty audit",
        allow_dirty=True,
        source_root=REPO_ROOT,
    )
    assert completed["status"] == "completed"
    assert "?? src/audit.ts" in completed["unexpected_changes"]


def test_observation_stop_collects_known_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "observe-artifacts"
    init_git_repo(target)
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Artifact audit", source_root=REPO_ROOT)

    screenshot = target / "audit-home-mobile.png"
    screenshot.write_text("fake screenshot\n", encoding="utf-8")
    playwright_snapshot = target / ".playwright-mcp" / "page.yaml"
    playwright_snapshot.parent.mkdir(parents=True, exist_ok=True)
    playwright_snapshot.write_text("url: http://localhost:5173\n", encoding="utf-8")

    blocked = stop_observation(target, summary="Artifacts present", source_root=REPO_ROOT)
    assert blocked["status"] == "blocked"
    assert "?? audit-home-mobile.png" in blocked["unexpected_changes"]
    assert any(".playwright-mcp" in entry for entry in blocked["unexpected_changes"])
    assert blocked["cleanable_artifacts"] == [".playwright-mcp", "audit-home-mobile.png"]
    assert screenshot.exists()
    assert playwright_snapshot.exists()

    completed = stop_observation(
        target,
        summary="Artifacts collected",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )
    assert completed["status"] == "completed"
    assert completed["unexpected_changes"] == []
    assert completed["cleanable_artifacts"] == []
    assert {item["from"] for item in completed["collected_artifacts"]} == {
        ".playwright-mcp",
        "audit-home-mobile.png",
    }
    artifact_root = target / completed["artifact_root"]
    assert (artifact_root / "audit-home-mobile.png").is_file()
    assert (artifact_root / ".playwright-mcp" / "page.yaml").is_file()
    assert not screenshot.exists()
    assert not (target / ".playwright-mcp").exists()


def test_observation_stop_allows_generated_runtime_deltas_with_collected_artifacts(
    tmp_path: Path,
) -> None:
    target = tmp_path / "observe-runtime-artifacts"
    init_git_repo(target)
    (target / ".gitignore").write_text(
        "worker/.wrangler/\nworker/node_modules/.mf/\n",
        encoding="utf-8",
    )
    git(target, "add", ".gitignore")
    git(target, "commit", "-m", "ignore generated worker runtime")
    wrangler_db = target / "worker" / ".wrangler" / "state" / "v3" / "d1" / "db.sqlite"
    wrangler_db.parent.mkdir(parents=True, exist_ok=True)
    wrangler_db.write_text("before\n", encoding="utf-8")
    mf_config = target / "worker" / "node_modules" / ".mf" / "cf.json"
    mf_config.parent.mkdir(parents=True, exist_ok=True)
    mf_config.write_text('{"before":true}\n', encoding="utf-8")

    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Runtime audit", source_root=REPO_ROOT)

    screenshot = target / "audit-home-mobile.png"
    screenshot.write_text("fake screenshot\n", encoding="utf-8")
    playwright_snapshot = target / ".playwright-mcp" / "page.yaml"
    playwright_snapshot.parent.mkdir(parents=True, exist_ok=True)
    playwright_snapshot.write_text("url: http://localhost:5173\n", encoding="utf-8")
    wrangler_db.write_text("after\n", encoding="utf-8")
    mf_config.write_text('{"after":true}\n', encoding="utf-8")

    completed = stop_observation(
        target,
        summary="Artifacts plus generated runtime state",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )

    assert completed["status"] == "completed"
    assert completed["unexpected_changes"] == []
    assert {item["from"] for item in completed["collected_artifacts"]} == {
        ".playwright-mcp",
        "audit-home-mobile.png",
    }
    allowed_sample = completed["allowed_runtime_changes_summary"]["sample"]
    assert any("worker/.wrangler" in entry for entry in allowed_sample)
    assert any("worker/node_modules/.mf" in entry for entry in allowed_sample)
    assert completed["allowed_runtime_changes_summary"]["total"] >= 2
    detail = json.loads((target / completed["detail_ref"]).read_text(encoding="utf-8"))
    assert any("worker/.wrangler" in entry for entry in detail["allowed_runtime_changes"])
    artifact_root = target / completed["artifact_root"]
    assert (artifact_root / "audit-home-mobile.png").is_file()
    assert (artifact_root / ".playwright-mcp" / "page.yaml").is_file()
    assert wrangler_db.read_text(encoding="utf-8") == "after\n"
    assert mf_config.read_text(encoding="utf-8") == '{"after":true}\n'


def test_observation_stop_allows_fallback_artifact_root_for_legacy_state(
    tmp_path: Path,
) -> None:
    target = tmp_path / "observe-legacy-artifact-root"
    init_git_repo(target)
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    started = start_observation(target, title="Legacy artifact audit", source_root=REPO_ROOT)
    current_work_path = target / AEGIS_CURRENT_WORK_REL
    current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
    current_work["paths"].pop("observation_artifacts", None)
    current_work["observation"].pop("artifact_root", None)
    current_work_path.write_text(json.dumps(current_work, indent=2) + "\n", encoding="utf-8")

    screenshot = target / "audit-home-mobile.png"
    screenshot.write_text("fake screenshot\n", encoding="utf-8")
    completed = stop_observation(
        target,
        summary="Legacy artifacts collected",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )

    assert completed["status"] == "completed"
    assert completed["unexpected_changes"] == []
    assert completed["artifact_root"] == (
        f".aegis/reports/observations/{started['task']['id']}/artifacts"
    )
    assert completed["collected_artifacts"] == [
        {
            "from": "audit-home-mobile.png",
            "to": (
                ".aegis/reports/observations/"
                f"{started['task']['id']}/artifacts/audit-home-mobile.png"
            ),
        }
    ]


def test_observation_collect_artifacts_blocks_when_source_delta_exists(tmp_path: Path) -> None:
    target = tmp_path / "observe-artifacts-source-dirty"
    init_git_repo(target)
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Mixed dirty audit", source_root=REPO_ROOT)

    screenshot = target / "audit-question-desktop.png"
    screenshot.write_text("fake screenshot\n", encoding="utf-8")
    source_file = target / "src" / "audit.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const audit = true;\n", encoding="utf-8")

    blocked = stop_observation(
        target,
        summary="Unsafe source delta",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )
    assert blocked["status"] == "blocked"
    assert blocked["cleanable_artifacts"] == ["audit-question-desktop.png"]
    assert "?? src/audit.ts" in blocked["unexpected_changes"]
    assert screenshot.exists()
    assert source_file.exists()


def test_observation_collect_artifacts_preserves_preexisting_artifact_names(tmp_path: Path) -> None:
    target = tmp_path / "observe-preexisting-artifact"
    init_git_repo(target)
    preexisting = target / "audit-old-mobile.png"
    preexisting.write_text("preexisting\n", encoding="utf-8")
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Preexisting audit", source_root=REPO_ROOT)

    completed = stop_observation(
        target,
        summary="No new artifacts",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )
    assert completed["status"] == "completed"
    assert completed["collected_artifacts"] == []
    assert preexisting.read_text(encoding="utf-8") == "preexisting\n"


def test_observation_collect_artifacts_refuses_symlink_artifact(tmp_path: Path) -> None:
    target = tmp_path / "observe-symlink-artifact"
    init_git_repo(target)
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Symlink audit", source_root=REPO_ROOT)

    outside = tmp_path / "outside.png"
    outside.write_text("outside\n", encoding="utf-8")
    link = target / "audit-link-mobile.png"
    link.symlink_to(outside)

    blocked = stop_observation(
        target,
        summary="Symlink artifact",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )
    assert blocked["status"] == "blocked"
    assert blocked["cleanable_artifacts"] == []
    assert "?? audit-link-mobile.png" in blocked["unexpected_changes"]
    assert link.is_symlink()
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_observation_runtime_delta_requires_ignored_runtime_prefix(tmp_path: Path) -> None:
    target = tmp_path / "observe-runtime-source-dirty"
    init_git_repo(target)
    runtime_file = target / "worker" / ".wrangler" / "state.json"
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_file.write_text("before\n", encoding="utf-8")
    git(target, "add", "worker/.wrangler/state.json")
    git(target, "commit", "-m", "track worker runtime fixture")

    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Tracked runtime audit", source_root=REPO_ROOT)

    runtime_file.write_text("after\n", encoding="utf-8")
    blocked = stop_observation(
        target,
        summary="Tracked runtime-looking path changed",
        collect_artifacts=True,
        source_root=REPO_ROOT,
    )

    assert blocked["status"] == "blocked"
    assert " M worker/.wrangler/state.json" in blocked["unexpected_changes"]
    assert blocked["allowed_runtime_changes_summary"]["total"] == 0


def test_observation_stop_blocks_tracked_and_ignored_deltas(tmp_path: Path) -> None:
    target = tmp_path / "observe-ignored"
    init_git_repo(target)
    (target / ".gitignore").write_text(".ignored/\n", encoding="utf-8")
    git(target, "add", ".gitignore")
    git(target, "commit", "-m", "ignore observation cache")
    ignored_file = target / ".ignored" / "cache.txt"
    ignored_file.parent.mkdir(parents=True, exist_ok=True)
    ignored_file.write_text("before\n", encoding="utf-8")

    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Ignored audit", source_root=REPO_ROOT)

    (target / "README.md").write_text("# target\nchanged\n", encoding="utf-8")
    ignored_file.write_text("after\n", encoding="utf-8")
    blocked = stop_observation(target, summary="Unexpected edits", source_root=REPO_ROOT)

    assert blocked["status"] == "blocked"
    assert " M README.md" in blocked["unexpected_changes"]
    assert any(
        entry.startswith("changed status-visible path: .ignored")
        for entry in blocked["unexpected_changes"]
    )


def test_start_local_work_replay_is_noop_and_different_work_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "local-start-replay"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)

    first = start_local_work(target, title="Improve BrandMark accessibility", source_root=REPO_ROOT)
    replay = start_local_work(
        target, title="Improve BrandMark accessibility", source_root=REPO_ROOT
    )

    assert replay["status"] == "already_started"
    assert replay["idempotent"] is True
    assert replay["task"]["id"] == first["task"]["id"]
    assert replay["paths"] == first["paths"]
    local_tasks = json.loads((target / AEGIS_LOCAL_TASKS_REL).read_text(encoding="utf-8"))
    assert local_tasks["next_id"] == 2
    assert len(local_tasks["tasks"]) == 1

    with pytest.raises(AegisError, match="current work is already in progress"):
        start_local_work(target, title="Add checkout screen", source_root=REPO_ROOT)


def test_plan_install_is_dry_run_and_schema_valid(tmp_path: Path) -> None:
    target = tmp_path / "empty-repo"
    target.mkdir()

    payload = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )

    validate_schema("install-plan.schema.json", payload)
    assert payload["mode"] == "dry_run"
    assert payload["apply_confirmed"] is False
    assert payload["summary"]["creates"] > 0
    assert payload["summary"]["manual_reviews"] == 0
    assert not (target / ".aegis").exists()


def test_install_verify_and_second_plan_are_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "empty-repo"
    target.mkdir()

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert report["status"] == "applied"
    assert (target / AEGIS_MANIFEST_REL).exists()
    assert (target / ".aegis" / "contract.md").exists()
    assert (target / "AGENTS.md").exists()
    assert (target / "CLAUDE.md").exists()
    assert (target / ".claude" / "settings.json").exists()
    assert (target / ".claude" / "scripts" / "gate_lib.py").exists()
    assert (target / ".claude" / "scripts" / "readiness.sh").exists()
    assert (target / "schemas" / "aegis" / "foundation-manifest.schema.json").exists()

    manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))
    validate_schema("foundation-manifest.schema.json", manifest)
    assert manifest["primary_agent"] == "claude"
    assert manifest["agents"]["claude"]["enabled"] is True
    managed_records = {
        record["path"]: record for record in manifest["managed_files"] if isinstance(record, dict)
    }
    assert managed_records[".claude/scripts/gate_lib.py"]["checksum"] == (
        aegis_installer._content_checksum((target / ".claude/scripts/gate_lib.py").read_bytes())
    )
    assert {gate["id"] for gate in manifest["gates"] if gate["required"]} >= {
        "claude.readiness",
        "claude.pretooluse",
        "claude.posttooluse_tracking",
        "claude.stop_tracking",
        "claude.bash_command",
        "claude.protected_path",
    }

    verification = verify(target, source_root=REPO_ROOT)
    assert verification["status"] == "passed"
    assert verification["mode"] == "standard"
    assert verification["summary"]["failed_required"] == 0
    assert (target / ".aegis" / "reports" / "verification-report.json").exists()

    second_plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    assert second_plan["summary"]["creates"] == 0
    assert second_plan["summary"]["manual_reviews"] == 0
    assert second_plan["summary"]["conflicts"] == 0
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}


def test_codex_install_merges_passive_hooks_and_uninstall_preserves_project_hooks(
    tmp_path: Path,
) -> None:
    target = tmp_path / "codex-hook-merge"
    (target / ".codex").mkdir(parents=True)
    project_command = "python3 tools/project_hook.py"
    project_hooks = {
        "projectMetadata": {"owner": "target-repo"},
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "^Read$",
                    "hooks": [{"type": "command", "command": project_command, "async": True}],
                }
            ],
            "Stop": [
                {
                    "hooks": [{"type": "command", "command": "echo project-stop"}],
                }
            ],
        },
    }
    hooks_path = target / aegis_installer.CODEX_HOOKS_REL
    hooks_path.write_text(json.dumps(project_hooks), encoding="utf-8")

    preview = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
    )
    hook_operation = next(
        operation
        for operation in preview["operations"]
        if operation["path"] == aegis_installer.CODEX_HOOKS_REL
    )
    assert hook_operation["classification"] == "modify"
    assert hook_operation["safe_to_apply"] is True

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    assert report["status"] == "applied"
    assert report["client_reload"]["agents"] == ["codex"]
    assert "/hooks" in report["client_reload"]["instructions"]
    installed_hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    assert installed_hooks["projectMetadata"] == {"owner": "target-repo"}
    commands = configured_hook_commands(installed_hooks)
    assert project_command in commands
    assert set(aegis_installer.CODEX_MANAGED_HOOK_COMMANDS) <= set(commands)
    assert commands.count(aegis_installer.CODEX_SESSION_START_COMMAND) == 1
    assert commands.count(aegis_installer.CODEX_POSTTOOLUSE_COMMAND) == 1
    assert commands.count(aegis_installer.CODEX_LEDGER_RECORD_COMMAND) == 1
    assert commands.count(aegis_installer.CODEX_SUBAGENT_START_COMMAND) == 1
    assert commands.count(aegis_installer.CODEX_SUBAGENT_STOP_COMMAND) == 1
    managed_handlers = [
        handler
        for groups in installed_hooks["hooks"].values()
        if isinstance(groups, list)
        for group in groups
        if isinstance(group, dict) and isinstance(group.get("hooks"), list)
        for handler in group["hooks"]
        if isinstance(handler, dict)
        and handler.get("command") in aegis_installer.CODEX_MANAGED_HOOK_COMMANDS
    ]
    assert managed_handlers
    assert all("async" not in handler for handler in managed_handlers)

    manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))
    assert aegis_installer.CODEX_HOOKS_REL in manifest["agents"]["codex"]["managed_files"]
    required_gate_ids = {gate["id"] for gate in manifest["gates"] if gate["required"]}
    assert set(aegis_installer.CODEX_GATE_IDS) - {"codex.hook_trust"} <= required_gate_ids
    hook_trust_gate = next(gate for gate in manifest["gates"] if gate["id"] == "codex.hook_trust")
    assert hook_trust_gate["required"] is False
    assert hook_trust_gate["settings_path"] == aegis_installer.CODEX_HOOKS_REL
    assert hook_trust_gate["review_command"] == (aegis_installer.CODEX_HOOK_TRUST_REVIEW_COMMAND)
    assert hook_trust_gate["hash_scope"] == aegis_installer.CODEX_HOOK_TRUST_HASH_SCOPE
    assert hook_trust_gate["bypass_allowed"] is False
    verification = verify(target, source_root=REPO_ROOT)
    assert verification["summary"]["failed_required"] == 0

    second = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
    )
    assert second["summary"]["modifies"] == 0
    assert second["summary"]["manual_reviews"] == 0

    removed = uninstall(target, source_root=REPO_ROOT, apply=True)
    assert removed["status"] == "applied"
    preserved = json.loads(hooks_path.read_text(encoding="utf-8"))
    preserved_commands = configured_hook_commands(preserved)
    assert project_command in preserved_commands
    assert "echo project-stop" in preserved_commands
    assert not set(aegis_installer.CODEX_MANAGED_HOOK_COMMANDS) & set(preserved_commands)


def test_codex_install_refuses_invalid_project_hooks_without_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "invalid-codex-hooks"
    hooks_path = target / aegis_installer.CODEX_HOOKS_REL
    hooks_path.parent.mkdir(parents=True)
    original = b'{"hooks":'
    hooks_path.write_bytes(original)

    preview = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
    )
    operation = next(
        item for item in preview["operations"] if item["path"] == aegis_installer.CODEX_HOOKS_REL
    )
    assert operation["classification"] == "manual-review"
    assert operation["safe_to_apply"] is False
    refused = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    assert refused["status"] == "refused"
    assert hooks_path.read_bytes() == original


def test_codex_sessionstart_clears_own_reload_marker_and_records_context(tmp_path: Path) -> None:
    target = tmp_path / "codex-sessionstart"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    marker = target / AEGIS_CLIENT_RELOAD_REL
    assert report["client_reload"]["agents"] == ["codex"]
    assert marker.is_file()
    assert (
        next_action(target, source_root=REPO_ROOT, invoking_agent="codex")["state"]
        == "client_reload_required"
    )

    result = run_target_codex_sessionstart(target)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()
    ledger_paths = list((target / ".test-xdg-state").rglob("ledger.db"))
    assert len(ledger_paths) == 1
    with sqlite3.connect(ledger_paths[0]) as connection:
        row = connection.execute(
            "SELECT event_type, agent_type, repository_identity, worktree_root, head "
            "FROM events WHERE event_type = 'session_begin' ORDER BY ts DESC, event_id DESC LIMIT 1"
        ).fetchone()
    assert row is not None
    assert row[0] == "session_begin"
    assert row[1] == "codex-session"
    assert row[2]
    assert row[3] == target.resolve().as_posix()


def test_installed_codex_hooks_capture_linked_worktree_and_child_lifecycle(
    tmp_path: Path,
) -> None:
    target = tmp_path / "codex-hook-repo"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (target / "README.md").write_text("# hook fixture\n", encoding="utf-8")
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    subprocess.run(
        [
            "git",
            "add",
            "README.md",
            ".aegis/bin/aegis",
            ".aegis/runtime.env",
            aegis_installer.CODEX_HOOKS_REL,
            *aegis_installer.CODEX_SHARED_RUNTIME_FILES,
        ],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "seed installed hooks",
        ],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sibling = tmp_path / "codex-hook-child"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "feat/task-2-child", str(sibling)],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sibling_two = tmp_path / "codex-hook-child-two"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "feat/task-3-child", str(sibling_two)],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    state_home = tmp_path / "shared-state"
    hook_payload = json.loads(
        (target / aegis_installer.CODEX_HOOKS_REL).read_text(encoding="utf-8")
    )

    def command_for(event: str) -> str:
        groups = hook_payload["hooks"][event]
        assert isinstance(groups, list) and groups
        handlers = groups[-1]["hooks"]
        if event == "PostToolUse":
            return next(
                handler["command"]
                for handler in handlers
                if handler.get("command") == aegis_installer.CODEX_LEDGER_RECORD_COMMAND
            )
        return handlers[0]["command"]

    def run_hook(
        root: Path, event: str, payload: dict[str, Any]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command_for(event),
            cwd=root,
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            executable="/bin/bash",
            env={
                **os.environ,
                "CODEX_THREAD_ID": "parent-session",
                "XDG_STATE_HOME": state_home.as_posix(),
            },
            check=False,
        )

    main_post = {
        "session_id": "parent-session",
        "turn_id": "turn-main",
        "cwd": target.as_posix(),
        "hook_event_name": "PostToolUse",
        "model": "gpt-5-codex",
        "tool_name": "Bash",
        "tool_use_id": "call-main",
        "tool_input": {"command": "git status --short"},
        "tool_response": {"metadata": {"exit_code": 0}, "output": ""},
    }
    child_post = {
        "session_id": "parent-session",
        "turn_id": "turn-child",
        "cwd": sibling.as_posix(),
        "hook_event_name": "PostToolUse",
        "model": "gpt-5-codex",
        "agent_id": "child-agent-1",
        "agent_type": "worker",
        "tool_name": "apply_patch",
        "tool_use_id": "call-child",
        "tool_input": {"command": "*** Begin Patch\n*** Update File: README.md\n*** End Patch"},
        "tool_response": {"metadata": {"exit_code": 0}, "output": "Done!"},
    }
    child_base = {
        "session_id": "parent-session",
        "turn_id": "turn-child",
        "cwd": sibling.as_posix(),
        "model": "gpt-5-codex",
        "agent_id": "child-agent-1",
        "agent_type": "worker",
    }
    second_child_failure = {
        "session_id": "parent-session",
        "turn_id": "turn-child-two",
        "cwd": sibling_two.as_posix(),
        "hook_event_name": "PostToolUse",
        "model": "gpt-5-codex",
        "agent_id": "child-agent-2",
        "agent_type": "worker",
        "tool_name": "Bash",
        "tool_use_id": "call-child-two",
        "tool_input": {"command": "false"},
        "tool_response": {"metadata": {"exit_code": 1}, "output": "failed"},
    }
    started = run_hook(target, "PostToolUse", main_post)
    with ThreadPoolExecutor(max_workers=2) as executor:
        patched_future = executor.submit(run_hook, sibling, "PostToolUse", child_post)
        failed_future = executor.submit(
            run_hook,
            sibling_two,
            "PostToolUse",
            second_child_failure,
        )
        patched = patched_future.result(timeout=30)
        failed = failed_future.result(timeout=30)
    child_started = run_hook(
        sibling,
        "SubagentStart",
        {**child_base, "hook_event_name": "SubagentStart"},
    )
    child_stopped = run_hook(
        sibling,
        "SubagentStop",
        {
            **child_base,
            "hook_event_name": "SubagentStop",
            "agent_transcript_path": "/tmp/child.jsonl",
            "last_assistant_message": "done",
        },
    )
    for result in (started, patched, failed, child_started, child_stopped):
        assert result.returncode == 0, result.stderr
    assert json.loads(child_stopped.stdout) == {}
    assert not (sibling / ".aegis" / "state").exists()
    assert not (sibling_two / ".aegis" / "state").exists()

    ledger_paths = list(state_home.rglob("ledger.db"))
    assert len(ledger_paths) == 1
    with sqlite3.connect(ledger_paths[0]) as connection:
        rows_before_teardown = connection.execute(
            "SELECT event_type, branch, repository_identity, worktree_root, head, "
            "agent_id, agent_type, parent_agent_id FROM events ORDER BY seq"
        ).fetchall()
    assert len(rows_before_teardown) == 6
    assert {row[1] for row in rows_before_teardown} >= {
        "main",
        "feat/task-2-child",
        "feat/task-3-child",
    }
    assert len({row[2] for row in rows_before_teardown}) == 1
    assert {row[3] for row in rows_before_teardown} >= {
        target.resolve().as_posix(),
        sibling.resolve().as_posix(),
        sibling_two.resolve().as_posix(),
    }
    assert all(row[4] for row in rows_before_teardown)
    assert all(row[5] for row in rows_before_teardown)
    assert all(row[6] for row in rows_before_teardown)
    assert all(
        row[7] == "session:parent-session" for row in rows_before_teardown if row[1] != "main"
    )
    root_event = next(row for row in rows_before_teardown if row[1] == "main")
    assert root_event[7] is None
    failure = next(row for row in rows_before_teardown if row[0] == "tool_failure")
    assert failure[1] == "feat/task-3-child"
    assert failure[5] == "child-agent-2"
    assert failure[6] == "worker"
    lifecycle = [row for row in rows_before_teardown if row[0].startswith("subagent_")]
    assert [row[0] for row in lifecycle] == ["subagent_begin", "subagent_end"]
    assert all(row[5] == "child-agent-1" for row in lifecycle)
    assert all(row[6] == "worker" for row in lifecycle)
    assert all(row[7] == "session:parent-session" for row in lifecycle)

    subprocess.run(
        ["git", "worktree", "remove", str(sibling)],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "worktree", "remove", str(sibling_two)],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    with sqlite3.connect(ledger_paths[0]) as connection:
        rows_after_teardown = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert rows_after_teardown == len(rows_before_teardown)


def test_install_uses_runtime_dispatchers_and_update_without_reinstall(tmp_path: Path) -> None:
    target = tmp_path / "runtime-update-target"
    target.mkdir()
    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"

    pretooluse = (target / ".claude" / "scripts" / "pretooluse-gate.sh").read_text(encoding="utf-8")
    readiness = (target / ".claude" / "scripts" / "readiness.sh").read_text(encoding="utf-8")
    assert 'exec "$AEGIS_BIN" hook pretooluse "$@"' in pretooluse
    assert 'exec "$AEGIS_BIN" hook readiness "$@"' in readiness
    assert (target / AEGIS_RUNTIME_ENV_REL).read_text(encoding="utf-8") == (
        "# Aegis runtime pointer. Managed by aegis runtime update.\n"
        f"AEGIS_SOURCE_ROOT={REPO_ROOT.resolve().as_posix()}\n"
    )

    manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))
    validate_schema("foundation-manifest.schema.json", manifest)
    assert manifest["runtime"]["source_root"] == REPO_ROOT.resolve().as_posix()
    assert manifest["runtime"]["pointer"] == AEGIS_RUNTIME_ENV_REL
    assert {item["path"] for item in manifest["managed_files"]} >= {AEGIS_RUNTIME_ENV_REL}

    bootstrap_before = {
        rel: (target / rel).read_text(encoding="utf-8")
        for rel in (
            ".aegis/bin/aegis",
            ".claude/settings.json",
            ".claude/scripts/pretooluse-gate.sh",
            ".claude/scripts/readiness.sh",
        )
    }
    preview = runtime_update(target, source_root=REPO_ROOT, apply=False)
    assert preview["status"] == "preview"
    assert preview["reinstall_required"] is False
    assert bootstrap_before == {
        rel: (target / rel).read_text(encoding="utf-8") for rel in bootstrap_before
    }

    applied = runtime_update(target, source_root=REPO_ROOT, apply=True)
    assert applied["status"] == "applied"
    assert applied["reinstall_required"] is False
    assert bootstrap_before == {
        rel: (target / rel).read_text(encoding="utf-8") for rel in bootstrap_before
    }
    runtime = runtime_status(target, source_root=REPO_ROOT)
    assert runtime["status"] == "installed"
    assert runtime["runtime_env_present"] is True
    assert runtime["active_source_root"] == REPO_ROOT.resolve().as_posix()
    assert runtime["active_source_valid"] is True

    second_plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}


def test_install_upgrades_existing_manifest_owned_bootstrap_files(tmp_path: Path) -> None:
    target = tmp_path / "managed-upgrade-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    stale_paths = [
        ".aegis/bin/aegis",
        ".claude/scripts/pretooluse-gate.sh",
        ".claude/scripts/gate_lib.py",
        "schemas/aegis/foundation-manifest.schema.json",
    ]
    for rel_path in stale_paths:
        write_managed_baseline(target, rel_path, b"# old Aegis-managed bootstrap content\n")

    plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    operations = {operation["path"]: operation for operation in plan["operations"]}

    assert plan["summary"]["manual_reviews"] == 0
    for rel_path in stale_paths:
        assert operations[rel_path]["classification"] == "modify"
        assert operations[rel_path]["safe_to_apply"] is True
        assert operations[rel_path]["managed"] is True

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"
    assert 'exec "$AEGIS_BIN" hook pretooluse "$@"' in (
        target / ".claude" / "scripts" / "pretooluse-gate.sh"
    ).read_text(encoding="utf-8")


def test_install_refuses_to_overwrite_customized_bootstrap_files(tmp_path: Path) -> None:
    target = tmp_path / "customized-upgrade-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    customized_path = ".claude/scripts/pretooluse-gate.sh"
    (target / customized_path).write_text("# user customized hook\n", encoding="utf-8")
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["customized_files"] = [{"path": customized_path, "kind": "adapter"}]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    operations = {operation["path"]: operation for operation in plan["operations"]}

    assert operations[customized_path]["classification"] == "manual-review"
    assert operations[customized_path]["safe_to_apply"] is False
    assert plan["summary"]["manual_reviews"] == 1


def test_project_update_dry_run_reports_pristine_stale_managed_asset_without_mutation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "project-update-dry-run-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    stale_rel = ".claude/scripts/brief_lib.py"
    stale_path = target / stale_rel
    write_managed_baseline(target, stale_rel, b"# stale installed managed asset\n")

    report = project_update(target, source_root=REPO_ROOT, apply=False)
    operations = {
        operation["path"]: operation for operation in report["install"]["plan"]["operations"]
    }

    assert report["status"] == "preview"
    assert report["mode"] == "dry_run"
    assert report["runtime"]["plan"]["status"] == "preview"
    assert operations[".claude/scripts/brief_lib.py"]["classification"] == "modify"
    assert operations[".claude/scripts/brief_lib.py"]["managed"] is True
    assert report["product_file_safety"]["safe"] is True
    evidence = report["workflow_state_evidence"]
    assert evidence["status"] == "present"
    assert "workflow.current_work" in evidence["gate_ids"]
    assert evidence["failed_required"] >= 1
    assert report["capsule"]["status"] == "preview"
    assert (target / AEGIS_UPDATE_REPORT_REL).exists() is False
    assert stale_path.read_text(encoding="utf-8") == "# stale installed managed asset\n"


def test_project_update_dry_run_refuses_locally_diverged_managed_asset(
    tmp_path: Path,
) -> None:
    target = tmp_path / "project-update-diverged-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    diverged_rel = ".claude/scripts/brief_lib.py"
    diverged_path = target / diverged_rel
    diverged_path.write_text("# locally hardened managed asset\n", encoding="utf-8")

    report = project_update(target, source_root=REPO_ROOT, apply=False)
    operations = {
        operation["path"]: operation for operation in report["install"]["plan"]["operations"]
    }

    assert report["status"] == "refused"
    assert operations[diverged_rel]["classification"] == "manual-review"
    assert operations[diverged_rel]["safe_to_apply"] is False
    assert operations[diverged_rel]["managed"] is True
    assert "diverged from its manifest checksum" in operations[diverged_rel]["reason"]
    assert report["product_file_safety"]["safe"] is False
    assert report["product_file_safety"]["manual_review_paths"] == [diverged_rel]
    assert (target / AEGIS_UPDATE_REPORT_REL).exists() is False
    assert diverged_path.read_text(encoding="utf-8") == "# locally hardened managed asset\n"


def test_project_update_workflow_state_evidence_filters_runtime_failures() -> None:
    evidence = aegis_installer._update_workflow_state_evidence(
        {
            "checks": [
                {
                    "gate_id": "runtime.workflow_templates",
                    "category": "runtime",
                    "required": True,
                    "status": "fail",
                    "message": "runtime missing",
                },
                {
                    "gate_id": "workflow.reports",
                    "category": "workflow",
                    "required": True,
                    "status": "fail",
                    "message": "path missing",
                },
                {
                    "gate_id": "mutation.pending_tracking_empty",
                    "category": "mutation",
                    "required": True,
                    "status": "fail",
                    "message": "pending",
                },
            ]
        }
    )

    assert evidence["status"] == "present"
    assert evidence["gate_ids"] == ["workflow.reports", "mutation.pending_tracking_empty"]
    assert evidence["failed_required"] == 2


def test_project_update_apply_refreshes_assets_and_compiles_capsule(tmp_path: Path) -> None:
    target = tmp_path / "project-update-apply-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    stale_rel = ".claude/scripts/brief_lib.py"
    stale_path = target / stale_rel
    write_managed_baseline(target, stale_rel, b"# stale installed managed asset\n")

    report = project_update(target, source_root=REPO_ROOT, apply=True)
    persisted = json.loads((target / AEGIS_UPDATE_REPORT_REL).read_text(encoding="utf-8"))

    assert report["status"] == "applied"
    assert persisted["status"] == "applied"
    assert report["install"]["applied"]["status"] == "applied"
    assert stale_path.read_text(encoding="utf-8") == (REPO_ROOT / stale_rel).read_text(
        encoding="utf-8"
    )
    assert report["capsule"]["compiled"] is True
    assert report["capsule"]["check"]["ok"] is True
    assert (target / ".aegis" / "capsule" / "current.json").is_file()
    assert (target / ".aegis" / "capsule" / "current.md").is_file()
    assert "failed_required" in report["verification"]["summary"]
    assert persisted["verification"]["summary"] == report["verification"]["summary"]
    assert report["workflow_state_evidence"]["status"] == "present"
    assert "workflow.current_work" in report["workflow_state_evidence"]["gate_ids"]
    assert persisted["workflow_state_evidence"] == report["workflow_state_evidence"]

    second_preview = project_update(target, source_root=REPO_ROOT, apply=False)
    assert second_preview["status"] == "preview"
    assert second_preview["install"]["summary"]["modifies"] == 0
    assert second_preview["install"]["summary"]["manual_reviews"] == 0


def test_legacy_manifest_recovers_source_backed_checksum_from_recorded_commit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "legacy-baseline-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    guard_record = next(
        record
        for record in manifest["managed_files"]
        if isinstance(record, dict) and record.get("path") == "scripts/codex-guard"
    )
    guard_record.pop("checksum")
    manifest["runtime"]["source_root"] = REPO_ROOT.as_posix()
    manifest["runtime"]["source_commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    checksum = aegis_installer._legacy_managed_checksum(manifest, REPO_ROOT, "scripts/codex-guard")

    expected = subprocess.run(
        [
            "git",
            "show",
            f"{manifest['runtime']['source_commit']}:scripts/codex-guard",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert checksum == aegis_installer._content_checksum(expected)


def test_project_update_apply_keeps_pre_runtime_legacy_baseline(
    monkeypatch, tmp_path: Path
) -> None:
    target = tmp_path / "legacy-project-update-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    stale_rel = ".claude/scripts/brief_lib.py"
    stale_content = b"# pristine legacy managed asset\n"
    (target / stale_rel).write_bytes(stale_content)
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(
        item
        for item in manifest["managed_files"]
        if isinstance(item, dict) and item.get("path") == stale_rel
    )
    record.pop("checksum")
    legacy_commit = "1" * 40
    manifest["runtime"]["source_commit"] = legacy_commit
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    observed_commits: list[str | None] = []

    def fake_legacy_checksum(installed_manifest, _source_root, path):
        if path != stale_rel:
            return None
        runtime = installed_manifest.get("runtime", {})
        observed_commits.append(runtime.get("source_commit"))
        return aegis_installer._content_checksum(stale_content)

    monkeypatch.setattr(aegis_installer, "_legacy_managed_checksum", fake_legacy_checksum)

    report = project_update(target, source_root=REPO_ROOT, apply=True)

    assert report["status"] == "applied"
    assert observed_commits and set(observed_commits) == {legacy_commit}
    assert (target / stale_rel).read_bytes() == (REPO_ROOT / stale_rel).read_bytes()


def test_project_update_refuses_manual_review_install_plan(tmp_path: Path) -> None:
    target = tmp_path / "project-update-refuse-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    customized_path = ".claude/scripts/brief_lib.py"
    (target / customized_path).write_text("# user customized brief lib\n", encoding="utf-8")
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["customized_files"] = [{"path": customized_path, "kind": "adapter"}]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = project_update(target, source_root=REPO_ROOT, apply=True)

    assert report["status"] == "refused"
    assert customized_path in report["product_file_safety"]["manual_review_paths"]
    assert (target / customized_path).read_text(encoding="utf-8") == "# user customized brief lib\n"
    assert not (target / AEGIS_UPDATE_REPORT_REL).exists()


def test_next_action_guides_not_installed_and_installed_states(tmp_path: Path) -> None:
    target = tmp_path / "guided-repo"
    target.mkdir()

    initial = next_action(target, source_root=REPO_ROOT)
    assert initial["read_only"] is True
    assert initial["phase"] == "bootstrap"
    assert initial["state"] == "not_installed"
    assert initial["suggested_mcp_call"]["tool"] == "aegis.init"
    assert initial["suggested_mcp_call"]["arguments"]["apply"] is True
    assert initial["details"]["must_initialize_before_source_edits"] is True
    assert "source edits" in initial["details"]["forbidden_until_init"]
    assert "Taskmaster mutations" in initial["details"]["forbidden_until_init"]
    assert "aegis.inspect" in initial["details"]["allowed_until_init"]

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    installed = next_action(target, source_root=REPO_ROOT)
    assert installed["phase"] == "bootstrap"
    assert installed["state"] == "client_reload_required"
    assert installed["suggested_mcp_call"]["tool"] == "aegis.next"

    simulate_claude_reload(target)
    installed = next_action(target, source_root=REPO_ROOT)
    assert installed["phase"] == "start"
    # TM 190: a fresh install with no Taskmaster ledger is now the no_taskmaster bootstrap state
    # (offers both local tracked work and the task-master init/PRD path).
    assert installed["state"] == "no_taskmaster"
    assert installed["suggested_mcp_call"]["tool"] == "aegis.start"
    assert installed["suggested_mcp_call"]["arguments"]["apply"] is True


def test_next_action_defers_task_selection_to_taskmaster_when_tasks_json_is_present(
    tmp_path: Path,
) -> None:
    target = tmp_path / "guided-taskmaster-repo"
    target.mkdir()
    write_taskmaster_tasks(
        target,
        [
            {
                "id": 6,
                "title": "Heuristic would pick this first",
                "description": "Aegis must not present this as the next task.",
                "status": "pending",
                "priority": "medium",
                "dependencies": [],
                "subtasks": [],
            },
            {
                "id": 31,
                "title": "Prerequisite",
                "status": "done",
                "dependencies": [],
                "subtasks": [],
            },
            {
                "id": 32,
                "title": "Taskmaster CLI may choose this instead",
                "description": "Only Taskmaster is allowed to decide that.",
                "status": "pending",
                "priority": "high",
                "dependencies": [31],
                "subtasks": [],
            },
        ],
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)

    guided = next_action(target, source_root=REPO_ROOT)

    assert guided["phase"] == "start"
    assert guided["state"] == "installed_taskmaster_present"
    assert "Taskmaster" in guided["next_required_action"]
    assert guided["suggested_mcp_call"] is None
    assert "task-master next" in guided["suggested_cli"]
    assert "--task <id>" in guided["suggested_cli"]
    assert "--task 6" not in guided["suggested_cli"]
    assert "--task 32" not in guided["suggested_cli"]
    repairs = "\n".join(guided["copyable_repairs"])
    assert "task-master next" in repairs
    assert "task-master show <id>" in repairs
    assert "aegis kickoff --target-dir . --task <id>" in repairs
    assert "aegis start '<task title>'" not in repairs
    taskmaster = guided["details"]["taskmaster"]
    assert taskmaster["source"] == ".taskmaster/tasks/tasks.json"
    assert taskmaster["state"] == "valid"
    assert taskmaster["present"] is True
    assert taskmaster["valid"] is True
    assert taskmaster["task_count"] == 3
    assert taskmaster["task_selection_authority"] == "taskmaster"
    assert taskmaster["aegis_task_selection"] == "suppressed"
    assert taskmaster["kickoff_requires_explicit_taskmaster_id"] is True
    assert taskmaster["local_fallback_allowed"] is False
    assert "task" not in taskmaster
    assert guided["details"]["taskmaster"]["ordering"] == [
        "task-master next/show",
        "aegis.kickoff",
        "native source edit",
        "aegis.verify",
        "aegis.closeout",
        "aegis.doctor",
        "task-master set-status --status=done",
    ]
    claude_entry = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "task-master next" in claude_entry
    assert "task-master show <id>" in claude_entry
    assert "Taskmaster done only after Aegis closeout and doctor pass" not in claude_entry
    assert ".aegis/contract.md` is authoritative" in claude_entry
    strict_contract = (target / ".aegis" / "contract.md").read_text(encoding="utf-8")
    assert "Taskmaster done only after Aegis closeout and doctor pass" in strict_contract

    for report in (
        inspect_project(target, source_root=REPO_ROOT),
        status(target, source_root=REPO_ROOT),
        doctor(target, source_root=REPO_ROOT),
    ):
        guidance = (
            report["workflow_guidance"] if "workflow_guidance" in report else report["next_action"]
        )
        assert guidance["state"] == "installed_taskmaster_present"
        assert guidance["details"]["taskmaster"]["aegis_task_selection"] == "suppressed"
        assert "task" not in guidance["details"]["taskmaster"]
    assert "task-master generate" not in claude_entry
    assert "task-master generate" in strict_contract
    claude_settings = json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allowed = claude_settings["permissions"]["allow"]
    assert "Bash(task-master *)" in allowed


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ("{not json\n", "json_decode_error"),
        ([], "non_object_payload"),
        ({}, "missing_task_container"),
        # TM 190: an empty ledger ({"tasks": []}) is no longer "invalid" — it is the
        # taskmaster_empty bootstrap state (covered by test_next_action_fresh_project_bootstrap_states).
        ({"master": {"tasks": {}}}, "malformed_task_container"),
        ({"master": {"tasks": ["not-an-object"]}}, "malformed_task"),
        (
            {"master": {"tasks": [{"id": "abc", "title": "Bad", "status": "pending"}]}},
            "invalid_task_id",
        ),
        (
            {"master": {"tasks": [{"id": 42, "title": "Bad", "status": 7}]}},
            "invalid_task_status",
        ),
        (
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Bad",
                            "status": "pending",
                            "dependencies": "1",
                        }
                    ]
                }
            },
            "invalid_task_dependencies",
        ),
        (
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Bad",
                            "status": "pending",
                            "dependencies": ["x"],
                        }
                    ]
                }
            },
            "invalid_task_dependency",
        ),
    ],
)
def test_taskmaster_present_invalid_blocks_task_selection_across_surfaces(
    tmp_path: Path, payload: object | str, reason: str
) -> None:
    target = tmp_path / f"invalid-taskmaster-{reason}"
    init_git_repo(target)
    write_taskmaster_payload(target, payload)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)

    guided = next_action(target, source_root=REPO_ROOT)

    assert guided["phase"] == "start"
    assert guided["state"] == "installed_taskmaster_invalid"
    assert guided["suggested_mcp_call"] is None
    assert "aegis start" not in guided["suggested_cli"]
    assert "aegis kickoff" not in guided["suggested_cli"]
    assert "taskmaster.tasks_json_valid" in guided["missing_gates"]
    taskmaster = guided["details"]["taskmaster"]
    assert taskmaster["source"] == ".taskmaster/tasks/tasks.json"
    assert taskmaster["state"] == "invalid"
    assert taskmaster["present"] is True
    assert taskmaster["valid"] is False
    assert taskmaster["reason"] == reason
    assert taskmaster["task_selection_authority"] == "taskmaster"
    assert taskmaster["aegis_task_selection"] == "suppressed"
    assert taskmaster["local_fallback_allowed"] is False
    assert "task" not in taskmaster
    repairs = "\n".join(guided["copyable_repairs"])
    assert "taskmaster health" in repairs
    assert "task-master validate-dependencies" in repairs

    for report in (
        inspect_project(target, source_root=REPO_ROOT),
        status(target, source_root=REPO_ROOT),
        doctor(target, source_root=REPO_ROOT),
    ):
        guidance = (
            report["workflow_guidance"] if "workflow_guidance" in report else report["next_action"]
        )
        assert guidance["state"] == "installed_taskmaster_invalid"
        assert guidance["details"]["taskmaster"]["reason"] == reason
        assert "task" not in guidance["details"]["taskmaster"]

    with pytest.raises(AegisError, match="Taskmaster task state is present but invalid"):
        start_local_work(target, title="Local fallback must not happen", source_root=REPO_ROOT)

    tree_before = snapshot_whole_tree(target)
    reconcile_report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert reconcile_report["read_only"] is True
    assert reconcile_report["taskmaster"]["state"] == "invalid"
    assert reconcile_report["taskmaster"]["present"] is True
    assert reconcile_report["taskmaster"]["valid"] is False
    assert reconcile_report["taskmaster"]["reason"] == reason
    assert reconcile_report["taskmaster"]["available"] is False
    assert reconcile_report["summary"]["findings"] == 1
    assert reconcile_report["findings"][0]["kind"] == "taskmaster_invalid"
    assert reconcile_report["findings"][0]["evidence"]["reason"] == reason
    assert not (target / AEGIS_LOCAL_TASKS_REL).exists()
    assert not (target / AEGIS_CURRENT_WORK_REL).exists()


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root can read chmod 000 files, so unreadable-file behavior is not observable",
)
def test_taskmaster_present_unreadable_blocks_task_selection(tmp_path: Path) -> None:
    target = tmp_path / "unreadable-taskmaster"
    init_git_repo(target)
    write_taskmaster_tasks(
        target,
        [{"id": 42, "title": "Unreadable", "status": "pending", "dependencies": []}],
    )
    tasks_path = target / ".taskmaster" / "tasks" / "tasks.json"
    tasks_path.chmod(0)
    try:
        install(
            target,
            source_root=REPO_ROOT,
            primary_agent="claude",
            agents=["claude"],
            apply=True,
        )
        simulate_claude_reload(target)

        guided = next_action(target, source_root=REPO_ROOT)

        assert guided["state"] == "installed_taskmaster_invalid"
        assert guided["details"]["taskmaster"]["reason"] == "unreadable"
        assert "task" not in guided["details"]["taskmaster"]
    finally:
        tasks_path.chmod(0o644)


def test_install_report_flags_claude_reload_when_adapter_hooks_change(tmp_path: Path) -> None:
    target = tmp_path / "claude-reload-required"
    target.mkdir()

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert install_report["status"] == "applied"
    reload_guidance = install_report["client_reload"]
    assert reload_guidance["required"] is True
    assert reload_guidance["agent"] == "claude"
    assert ".claude/settings.json" in reload_guidance["changed_paths"]
    assert any(path.startswith(".claude/scripts/") for path in reload_guidance["changed_paths"])
    assert "restart Claude" in reload_guidance["instructions"]
    assert (target / AEGIS_CLIENT_RELOAD_REL).is_file()

    second = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert second["status"] == "applied"
    assert second["client_reload"]["required"] is True
    assert second["client_reload"]["pending_marker"] is True
    assert second["client_reload"]["changed_paths"] == reload_guidance["changed_paths"]

    hook_probe = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_next",
            "tool_input": {"target_dir": target.as_posix()},
        },
    )
    assert hook_probe.returncode == 0, hook_probe.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()

    third = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert third["status"] == "applied"
    assert third["client_reload"]["required"] is False
    assert third["client_reload"]["changed_paths"] == []


def test_installed_pretooluse_blocks_unclassifiable_payload(tmp_path: Path) -> None:
    target = tmp_path / "unclassifiable-pretooluse"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    malformed = run_target_pretooluse_raw(target, '{"tool_name": "Write",')
    missing_tool_name = run_target_pretooluse_raw(
        target, '{"tool_input": {"file_path": "src/main.ts"}}'
    )

    assert malformed.returncode == 2
    assert "could not be parsed or classified safely" in malformed.stderr
    assert "invalid JSON" in malformed.stderr
    assert missing_tool_name.returncode == 2
    assert "missing required field 'tool_name'" in missing_tool_name.stderr
    assert (target / AEGIS_CLIENT_RELOAD_REL).is_file()


def test_installed_pretooluse_short_circuits_read_only_before_readiness(tmp_path: Path) -> None:
    target = tmp_path / "read-only-without-readiness"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    (target / ".claude" / "scripts" / "readiness.sh").unlink()

    read_only = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git status --short"},
        },
    )
    mutating = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "npm run build"},
        },
    )

    assert read_only.returncode == 0, read_only.stderr
    assert mutating.returncode == 2
    assert "readiness is BLOCKED" in mutating.stderr


def test_installed_pretooluse_blocks_direct_workflow_edits_but_allows_aegis_handlers(
    tmp_path: Path,
) -> None:
    target = tmp_path / "workflow-surface-protection"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="protect-workflow-surfaces",
        title="Protect Workflow Surfaces",
        source_root=REPO_ROOT,
    )

    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    handoff_rel = f"{current_work['paths']['work_tracking']}/HANDOFF.md"
    findings_rel = f"{current_work['paths']['work_tracking']}/FINDINGS.md"

    direct_write = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": handoff_rel}},
    )
    bash_redirect = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "printf forged > sessions/current"}},
    )
    mcp_direct = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__serena__create_text_file",
            "tool_input": {"relative_path": handoff_rel},
        },
    )
    aegis_cli_log = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    f"./.aegis/bin/aegis log --target-dir . --handler test --evidence {findings_rel} "
                    "--note 'structured evidence'"
                )
            },
        },
    )
    aegis_mcp_log = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_log",
            "tool_input": {
                "target_dir": target.as_posix(),
                "path": findings_rel,
                "note": "structured evidence",
            },
        },
    )

    assert direct_write.returncode == 2
    assert "Workflow-owned path" in direct_write.stderr
    assert handoff_rel in direct_write.stderr
    assert bash_redirect.returncode == 2
    assert "redirection targets workflow-owned path sessions/current" in bash_redirect.stderr
    assert mcp_direct.returncode == 2
    assert "Workflow-owned path" in mcp_direct.stderr
    assert aegis_cli_log.returncode == 0, aegis_cli_log.stderr
    assert aegis_mcp_log.returncode == 0, aegis_mcp_log.stderr


def test_start_and_kickoff_are_blocked_until_claude_reload_hook_runs(tmp_path: Path) -> None:
    target = tmp_path / "reload-barrier"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert install_report["client_reload"]["required"] is True
    assert (target / AEGIS_CLIENT_RELOAD_REL).is_file()
    guided = next_action(target, source_root=REPO_ROOT)
    assert guided["state"] == "client_reload_required"
    assert guided["suggested_mcp_call"]["tool"] == "aegis.next"

    with pytest.raises(AegisError, match="restart Claude"):
        start_local_work(target, title="Improve BrandMark accessibility", source_root=REPO_ROOT)
    with pytest.raises(AegisError, match="restart Claude"):
        kickoff(
            target,
            task_id="42",
            slug="add-to-cart-button",
            title="Add visible Add to cart button",
            source_root=REPO_ROOT,
        )

    hook_probe = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_next",
            "tool_input": {"target_dir": target.as_posix()},
        },
    )
    assert hook_probe.returncode == 0, hook_probe.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()

    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="add-to-cart-button",
        title="Add visible Add to cart button",
        source_root=REPO_ROOT,
    )

    assert kickoff_report["status"] == "started"
    assert kickoff_report["task"]["id"] == "42"


def test_invoking_agent_detection_is_explicit_and_conservative() -> None:
    assert aegis_installer.invoking_agent_from_environment({}) is None
    assert (
        aegis_installer.invoking_agent_from_environment({"CODEX_THREAD_ID": "thread-123"})
        == "codex"
    )
    assert aegis_installer.invoking_agent_from_environment({"CODEX_CI": "1"}) == "codex"
    assert (
        aegis_installer.invoking_agent_from_environment(
            {
                "CODEX_THREAD_ID": "thread-123",
                "CLAUDE_PROJECT_DIR": "/tmp/project",
            }
        )
        == "claude"
    )
    assert (
        aegis_installer.invoking_agent_from_environment(
            {
                "AEGIS_INVOKING_AGENT": "gemini",
                "CLAUDE_PROJECT_DIR": "/tmp/project",
            }
        )
        == "gemini"
    )


def test_multi_agent_reload_markers_clear_independently_before_codex_observation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "multi-agent-codex-start"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
        apply=True,
    )

    marker = target / AEGIS_CLIENT_RELOAD_REL
    assert marker.is_file()
    assert json.loads(marker.read_text(encoding="utf-8"))["agents"] == ["claude", "codex"]
    assert next_action(target, source_root=REPO_ROOT)["state"] == "client_reload_required"
    assert (
        next_action(target, source_root=REPO_ROOT, invoking_agent="claude")["state"]
        == "client_reload_required"
    )
    assert (
        next_action(target, source_root=REPO_ROOT, invoking_agent="codex")["state"]
        == "client_reload_required"
    )

    simulate_codex_reload(target)
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["agents"] == ["claude"]

    assert (
        next_action(target, source_root=REPO_ROOT, invoking_agent="codex")["state"]
        == "no_taskmaster"
    )

    simulate_codex_reload(target)
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["agents"] == ["claude"]
    assert marker_payload["changed_paths_by_agent"].keys() == {"claude"}

    codex_guidance = next_action(
        target,
        source_root=REPO_ROOT,
        invoking_agent="codex",
    )
    assert codex_guidance["state"] == "no_taskmaster"
    pending_reload = codex_guidance["adapter_reload_pending"]
    assert pending_reload["status"] == "required_for_other_agent"
    assert pending_reload["agent"] == "claude"
    assert pending_reload["invoking_agent"] == "codex"
    assert pending_reload["blocks_invoking_agent"] is False
    assert pending_reload["marker_path"] == AEGIS_CLIENT_RELOAD_REL
    assert pending_reload["changed_paths"]
    assert pending_reload["clearance"]["method"] == "installed_agent_pretooluse_hook"
    assert codex_guidance["details"]["pending_adapter_reload"]["agent"] == "claude"
    codex_status = status(
        target,
        source_root=REPO_ROOT,
        invoking_agent="codex",
    )
    assert codex_status["workflow_guidance"]["state"] == "no_taskmaster"
    assert codex_status["workflow_guidance"]["adapter_reload_pending"]["agent"] == "claude"

    with pytest.raises(AegisError, match="restart Claude"):
        start_observation(
            target,
            title="Blocked Claude observation",
            source_root=REPO_ROOT,
            invoking_agent="claude",
        )

    started = start_observation(
        target,
        title="Codex observation",
        source_root=REPO_ROOT,
        invoking_agent="codex",
    )
    assert started["status"] == "started"
    assert marker.is_file()
    active_codex_guidance = next_action(
        target,
        source_root=REPO_ROOT,
        invoking_agent="codex",
    )
    assert active_codex_guidance["state"] == "observation_active"
    assert active_codex_guidance["adapter_reload_pending"]["agent"] == "claude"
    assert (
        active_codex_guidance["continuation_brief"]["current_task_authority"]
        == "observation-session"
    )
    assert (
        next_action(target, source_root=REPO_ROOT, invoking_agent="claude")["state"]
        == "client_reload_required"
    )

    simulate_claude_reload(target)
    assert not marker.exists()


def test_codex_primary_guidance_uses_explicit_agent_logs_and_normalized_task_slug(
    tmp_path: Path,
) -> None:
    target = tmp_path / "codex-guided-workflow"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (target / "src").mkdir()
    (target / "src" / "main.ts").write_text("export const ready = true;\n", encoding="utf-8")
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    simulate_codex_reload(target)

    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="task-42-add-visible-add-to-cart-button",
        title="Add visible Add to cart button",
        source_root=REPO_ROOT,
    )

    assert kickoff_report["task"]["slug"] == "add-visible-add-to-cart-button"
    assert kickoff_report["branch"]["current"] == "feat/task-42-add-visible-add-to-cart-button"
    assert kickoff_report["next_action"]["suggested_mcp"]["arguments"]["handler"] == "codex:scope"

    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    scope_required = next_action(target, source_root=REPO_ROOT)
    assert scope_required["suggested_mcp_call"]["arguments"]["handler"] == "codex:scope"

    scope_logged = log_work(
        target,
        handler="codex:scope",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Confirmed Codex scope before implementation",
        event_class="scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    after_scope_args = scope_logged["next_action"]["suggested_mcp"]["arguments"]
    assert after_scope_args["handler"] == "codex:implementation"
    assert "pending_event_id" not in after_scope_args
    assert scope_logged["next_action"]["details"]["pending_tracking_expected"] is False

    implementation_logged = log_work(
        target,
        handler="codex:implementation",
        evidence="src/main.ts",
        note="Recorded Codex implementation evidence",
        event_class="implementation",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    after_implementation_args = implementation_logged["next_action"]["suggested_mcp"]["arguments"]
    assert after_implementation_args["handler"] == "codex:verification"
    assert after_implementation_args["evidence"].endswith("/task-verification.md")
    assert "pending_event_id" not in after_implementation_args

    verify_required = next_action(target, source_root=REPO_ROOT)
    assert verify_required["suggested_mcp_call"]["arguments"]["handler"] == "codex:verification"
    assert "pending_event_id" not in verify_required["suggested_mcp_call"]["arguments"]
    assert verify_required["details"]["pending_tracking_expected"] is False

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)
    strict_args = strict_report["next_action"]["suggested_mcp"]["arguments"]
    assert strict_args["handler"] == "codex:verification"
    assert strict_args["evidence"] == AEGIS_VERIFY_REPORT_REL
    assert "pending_event_id" not in strict_args
    assert strict_report["next_action"]["details"]["pending_tracking_expected"] is False


def test_start_local_work_refuses_to_bypass_present_taskmaster(tmp_path: Path) -> None:
    target = tmp_path / "taskmaster-start-refusal"
    target.mkdir()
    taskmaster_tasks = target / ".taskmaster" / "tasks"
    taskmaster_tasks.mkdir(parents=True)
    (taskmaster_tasks / "tasks.json").write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Add visible Add to cart button",
                            "status": "pending",
                            "dependencies": [],
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)

    with pytest.raises(AegisError, match="Taskmaster is present"):
        start_local_work(target, title="Add visible Add to cart button", source_root=REPO_ROOT)

    assert not (target / AEGIS_LOCAL_TASKS_REL).exists()
    assert not (target / AEGIS_CURRENT_WORK_REL).exists()


@pytest.mark.parametrize(
    ("is_draft", "expected_action", "expected_command"),
    [
        (True, "mark_ready_for_review", "gh pr ready"),
        (False, "ask_before_merge", "gh pr checks 133"),
    ],
)
def test_post_closeout_delivery_guidance_classifies_passed_pr_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    is_draft: bool,
    expected_action: str,
    expected_command: str,
) -> None:
    branch = "feat/task-73-p0-poisoned-resume-fallback"
    current_work = {"branch": {"current": branch}, "paths": {}}
    base_pr = {
        "number": 133,
        "state": "OPEN",
        "title": "Fix stale drill resume recovery",
        "headRefName": branch,
        "baseRefName": "main",
        "mergedAt": None,
        "url": "https://example.invalid/pr/133",
        "isDraft": is_draft,
    }
    detailed_pr = {
        **base_pr,
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [
            {
                "__typename": "CheckRun",
                "name": "app · typecheck · lint · test · build · e2e",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "detailsUrl": "https://example.invalid/checks/1",
            }
        ],
    }

    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: branch)
    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        lambda *_args: subprocess.CompletedProcess(
            args=["git", "rev-parse"],
            returncode=0,
            stdout=f"origin/{branch}\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": [base_pr]},
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_view",
        lambda _target, _number: {"available": True, "reason": "", "pr": detailed_pr},
    )

    delivery = aegis_installer._post_closeout_delivery_guidance(tmp_path, current_work)

    assert delivery["state"] == "delivery_pending"
    assert delivery["next_safe_action"] == expected_action
    assert delivery["suggested_cli"] == expected_command
    assert delivery["details"]["checks"]["state"] == "passed"
    assert delivery["details"]["merge_requires_explicit_user_approval"] is True
    assert not any("pr merge" in command for command in delivery["copyable_repairs"])


def test_post_closeout_delivery_guidance_defers_green_pr_to_evidence_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch = "feat/task-247-routine-change"
    current_work = {"branch": {"current": branch}, "paths": {}}
    policy = json.loads((REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8"))
    (tmp_path / "aegis.delivery-policy.json").write_text(
        json.dumps(policy) + "\n",
        encoding="utf-8",
    )
    policy_schema = tmp_path / "schemas" / "aegis" / "delivery-policy.schema.json"
    policy_schema.parent.mkdir(parents=True)
    shutil.copy2(SCHEMA_ROOT / "delivery-policy.schema.json", policy_schema)
    base_pr = {
        "number": 247,
        "state": "OPEN",
        "headRefName": branch,
        "baseRefName": "main",
        "mergedAt": None,
        "isDraft": False,
    }
    detailed_pr = {
        **base_pr,
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [
            {
                "__typename": "CheckRun",
                "name": "CI",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            }
        ],
    }

    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: branch)
    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        lambda *_args: subprocess.CompletedProcess(
            args=["git", "rev-parse"],
            returncode=0,
            stdout=f"origin/{branch}\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": [base_pr]},
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_view",
        lambda _target, _number: {"available": True, "reason": "", "pr": detailed_pr},
    )

    delivery = aegis_installer._post_closeout_delivery_guidance(tmp_path, current_work)

    assert delivery["state"] == "delivery_pending"
    assert delivery["next_safe_action"] == "await_evidence_gated_merge"
    assert "no per-PR owner approval is required" in delivery["next_required_action"]
    assert delivery["details"]["merge_requires_explicit_user_approval"] is False
    assert delivery["details"]["delivery_policy"]["policy_id"] == policy["policy_id"]
    assert not any("pr merge" in command for command in delivery["copyable_repairs"])


@pytest.mark.parametrize(
    ("policy_state", "expected_mode", "expected_valid", "expected_active"),
    [
        ("absent", "attended", True, False),
        ("invalid", "attended", False, False),
        ("schema-invalid", "attended", False, False),
        ("revoked", "attended", True, False),
        ("active", "evidence-gated", True, True),
    ],
)
def test_status_surfaces_fail_closed_delivery_policy_state(
    tmp_path: Path,
    policy_state: str,
    expected_mode: str,
    expected_valid: bool,
    expected_active: bool,
) -> None:
    target = tmp_path / policy_state
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="none",
        agents=[],
        apply=True,
    )
    policy_path = target / "aegis.delivery-policy.json"
    if policy_state == "invalid":
        policy_path.write_text("{not-json}\n", encoding="utf-8")
    elif policy_state in {"schema-invalid", "revoked", "active"}:
        policy = json.loads((REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8"))
        if policy_state == "revoked":
            policy["authority"]["status"] = "revoked"
        elif policy_state == "schema-invalid":
            policy["unknown"] = True
        policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")

    report = status(target, source_root=REPO_ROOT)
    delivery_policy = report["delivery_policy"]

    assert delivery_policy["mode"] == expected_mode
    assert delivery_policy["valid"] is expected_valid
    assert delivery_policy["active"] is expected_active
    assert delivery_policy["requires_per_pr_approval"] is (expected_mode == "attended")
    assert set(delivery_policy["routine_authority"]) == set(
        aegis_installer.AEGIS_ROUTINE_AUTHORITY_FIELDS
    )
    assert all(delivery_policy["routine_authority"].values()) is (expected_mode == "evidence-gated")
    assert report["workflow_guidance"]["delivery_policy"] == delivery_policy


def test_post_closeout_delivery_guidance_recognizes_blog_task67_on_synchronized_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_blog_completed_delivery_fixture()["completed_main"]
    pull_request = fixture["pull_request"]

    monkeypatch.setattr(
        aegis_installer,
        "_current_branch",
        lambda _target: fixture["current_branch"],
    )

    def fake_git(_target: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if args == (
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
        ):
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="origin/main\n", stderr=""
            )
        if args == (
            "merge-base",
            "--is-ancestor",
            pull_request["mergeCommit"]["oid"],
            "HEAD",
        ):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
        if args == ("rev-list", "--left-right", "--count", "HEAD...@{u}"):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="0\t0\n", stderr="")
        raise AssertionError(f"unexpected git invocation: {args!r}")

    monkeypatch.setattr(aegis_installer, "_run_target_git", fake_git)
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": [pull_request]},
    )

    delivery = aegis_installer._post_closeout_delivery_guidance(
        tmp_path,
        fixture["current_work"],
    )

    assert delivery["state"] == "merged_complete"
    assert delivery["next_safe_action"] == "merged_complete"
    assert delivery["details"]["current_branch"] == "main"
    assert delivery["details"]["recorded_branch"] == pull_request["headRefName"]
    assert delivery["details"]["delivery_proof"] == {
        "ahead": 0,
        "base_branch": "main",
        "behind": 0,
        "current_branch": "main",
        "merge_commit": pull_request["mergeCommit"]["oid"],
        "merge_commit_in_head": True,
        "status": "synchronized",
        "upstream": "origin/main",
    }


def test_next_action_replays_blog_task67_as_complete_on_synchronized_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_blog_completed_delivery_fixture()["completed_main"]
    pull_request = fixture["pull_request"]
    target = tmp_path / "blog-task67"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    (target / AEGIS_CLIENT_RELOAD_REL).unlink(missing_ok=True)
    current_work_path = target / AEGIS_CURRENT_WORK_REL
    current_work_path.parent.mkdir(parents=True, exist_ok=True)
    current_work_path.write_text(
        json.dumps(fixture["current_work"], indent=2) + "\n",
        encoding="utf-8",
    )
    closeout_path = target / AEGIS_CLOSEOUT_REPORT_REL
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(fixture["closeout_report"], indent=2) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: "main")

    def fake_git(_target: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if args == (
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
        ):
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="origin/main\n", stderr=""
            )
        if args == (
            "merge-base",
            "--is-ancestor",
            pull_request["mergeCommit"]["oid"],
            "HEAD",
        ):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
        if args == ("rev-list", "--left-right", "--count", "HEAD...@{u}"):
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="0\t0\n", stderr="")
        raise AssertionError(f"unexpected git invocation: {args!r}")

    monkeypatch.setattr(aegis_installer, "_run_target_git", fake_git)
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": [pull_request]},
    )

    guidance = next_action(target, source_root=REPO_ROOT)

    assert guidance["phase"] == "complete"
    assert guidance["state"] == "closeout_passed"
    assert guidance["next_required_action"] == "no workflow action required"
    assert guidance["missing_gates"] == []


@pytest.mark.parametrize(
    ("merge_commit", "ancestor_returncode", "sync_output", "expected_reason"),
    [
        (None, 0, "0\t0\n", "missing_merge_commit"),
        ("81511aa10bfa13191f95bd15b80d4d889ce2e0e8", 1, "0\t0\n", "merge_commit_not_in_head"),
        ("81511aa10bfa13191f95bd15b80d4d889ce2e0e8", 0, "0\t1\n", "upstream_not_synchronized"),
    ],
)
def test_post_closeout_delivery_guidance_fails_closed_without_complete_merged_main_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    merge_commit: str | None,
    ancestor_returncode: int,
    sync_output: str,
    expected_reason: str,
) -> None:
    fixture = load_blog_completed_delivery_fixture()["completed_main"]
    pull_request = json.loads(json.dumps(fixture["pull_request"]))
    if merge_commit is None:
        pull_request.pop("mergeCommit", None)
    else:
        pull_request["mergeCommit"] = {"oid": merge_commit}

    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: "main")

    def fake_git(_target: Path, *args: str) -> subprocess.CompletedProcess[str]:
        if args == (
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
        ):
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="origin/main\n", stderr=""
            )
        if args[:2] == ("merge-base", "--is-ancestor"):
            return subprocess.CompletedProcess(
                args=args,
                returncode=ancestor_returncode,
                stdout="",
                stderr="",
            )
        if args == ("rev-list", "--left-right", "--count", "HEAD...@{u}"):
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout=sync_output, stderr=""
            )
        raise AssertionError(f"unexpected git invocation: {args!r}")

    monkeypatch.setattr(aegis_installer, "_run_target_git", fake_git)
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": [pull_request]},
    )

    delivery = aegis_installer._post_closeout_delivery_guidance(
        tmp_path,
        fixture["current_work"],
    )

    assert delivery["state"] == "delivery_unknown"
    assert delivery["next_safe_action"] == "inspect_git_state"
    assert delivery["details"]["delivery_proof"]["status"] == "unproven"
    assert delivery["details"]["delivery_proof"]["reason"] == expected_reason


def test_post_closeout_delivery_guidance_fails_closed_when_github_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_blog_completed_delivery_fixture()["completed_main"]
    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: "main")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": False,
            "reason": "gh authentication failed",
            "prs": [],
        },
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        lambda *_args: pytest.fail("git proof must not run without matching GitHub truth"),
    )

    delivery = aegis_installer._post_closeout_delivery_guidance(
        tmp_path,
        fixture["current_work"],
    )

    assert delivery["state"] == "delivery_unknown"
    assert delivery["details"]["delivery_proof"] == {
        "status": "unproven",
        "reason": "github_unavailable",
        "github_reason": "gh authentication failed",
    }


def test_closeout_passed_binds_report_to_current_work_identity(tmp_path: Path) -> None:
    fixture = load_blog_completed_delivery_fixture()
    completed = fixture["completed_main"]
    current_task = fixture["stale_report_new_task"]["current_work"]
    report_path = tmp_path / AEGIS_CLOSEOUT_REPORT_REL
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(completed["closeout_report"], indent=2) + "\n",
        encoding="utf-8",
    )

    assert aegis_installer._closeout_passed(tmp_path, completed["current_work"]) is True
    assert aegis_installer._closeout_passed(tmp_path, current_task) is False

    own_closeout = json.loads(json.dumps(current_task))
    own_closeout["status"] = "completed"
    own_closeout["closeout_passed_at"] = "2026-07-12T01:00:00Z"
    assert aegis_installer._closeout_passed(tmp_path, own_closeout) is False

    report_path.unlink()
    assert aegis_installer._closeout_passed(tmp_path, own_closeout) is True


def test_next_action_does_not_use_stale_task67_closeout_for_active_task38(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_blog_completed_delivery_fixture()
    target = tmp_path / "blog-task38"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    (target / AEGIS_CLIENT_RELOAD_REL).unlink(missing_ok=True)
    current_work_path = target / AEGIS_CURRENT_WORK_REL
    current_work_path.parent.mkdir(parents=True, exist_ok=True)
    current_work_path.write_text(
        json.dumps(fixture["stale_report_new_task"]["current_work"], indent=2) + "\n",
        encoding="utf-8",
    )
    closeout_path = target / AEGIS_CLOSEOUT_REPORT_REL
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(fixture["completed_main"]["closeout_report"], indent=2) + "\n",
        encoding="utf-8",
    )

    def fail_if_called(*_args: object, **_kwargs: object) -> dict[str, Any]:
        pytest.fail("stale Task 67 report armed post-closeout delivery for active Task 38")

    monkeypatch.setattr(aegis_installer, "_post_closeout_delivery_guidance", fail_if_called)

    guidance = next_action(target, source_root=REPO_ROOT)

    assert guidance["phase"] not in {"deliver", "complete"}
    assert guidance["state"] != "delivery_unknown"


def test_delivery_snapshot_normalizes_machine_observed_draft_pr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch = "feat/task-234-witness-delivery-projection"
    base_pr = {
        "number": 256,
        "state": "OPEN",
        "title": "Project witness and delivery boundaries",
        "headRefName": branch,
        "headRefOid": "abc1234",
        "baseRefName": "main",
        "mergedAt": None,
        "closedAt": None,
        "url": "https://example.invalid/pr/256",
        "isDraft": True,
    }
    detailed_pr = {
        **base_pr,
        "mergeStateStatus": "CLEAN",
        "statusCheckRollup": [
            {
                "name": "CI",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "detailsUrl": "https://example.invalid/check/1",
            }
        ],
    }
    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: branch)
    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        lambda *_args: subprocess.CompletedProcess(
            args=["git", "rev-parse"],
            returncode=0,
            stdout=f"origin/{branch}\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": [base_pr]},
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_view",
        lambda _target, _number: {"available": True, "reason": "", "pr": detailed_pr},
    )

    snapshot = aegis_installer.delivery_snapshot(tmp_path)

    assert snapshot["available"] is True
    assert snapshot["recordable"] is True
    assert snapshot["action"] == "pr_draft"
    assert snapshot["branch"] == branch
    assert snapshot["head_commit"] == "abc1234"
    assert snapshot["checks"]["state"] == "passed"


def test_delivery_snapshot_records_pushed_branch_without_pr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch = "feat/task-234-witness-delivery-projection"
    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: branch)
    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        lambda *_args: subprocess.CompletedProcess(
            args=["git", "rev-parse"],
            returncode=0,
            stdout=f"origin/{branch}\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": []},
    )
    monkeypatch.setattr(
        aegis_installer,
        "_git_commit_for_ref",
        lambda _target, _ref: "def5678",
    )

    snapshot = aegis_installer.delivery_snapshot(tmp_path)

    assert snapshot["available"] is True
    assert snapshot["recordable"] is True
    assert snapshot["action"] == "branch_pushed"
    assert snapshot["pr"] is None
    assert snapshot["head_commit"] == "def5678"


def test_delivery_snapshot_refuses_unavailable_github_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch = "feat/task-234-witness-delivery-projection"
    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: branch)
    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        lambda *_args: subprocess.CompletedProcess(
            args=["git", "rev-parse"],
            returncode=1,
            stdout="",
            stderr="no upstream",
        ),
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": False, "reason": "gh authentication failed", "prs": []},
    )

    snapshot = aegis_installer.delivery_snapshot(tmp_path)

    assert snapshot["available"] is False
    assert snapshot["recordable"] is False
    assert snapshot["reason"] == "gh authentication failed"


def test_delivery_snapshot_exact_pr_supports_post_merge_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    merged_pr = {
        "number": 256,
        "state": "MERGED",
        "title": "Project witness and delivery boundaries",
        "headRefName": "feat/task-234-witness-delivery-projection",
        "headRefOid": "abc1234",
        "baseRefName": "main",
        "mergedAt": "2026-07-09T20:00:00Z",
        "closedAt": "2026-07-09T20:00:00Z",
        "url": "https://example.invalid/pr/256",
        "isDraft": False,
        "mergeStateStatus": "UNKNOWN",
        "statusCheckRollup": [],
    }
    monkeypatch.setattr(aegis_installer, "_current_branch", lambda _target: "main")

    def fake_git(*args):
        ref = str(args[-1])
        upstream = (
            "origin/feat/task-234-witness-delivery-projection"
            if "task-234" in ref
            else "origin/main"
        )
        return subprocess.CompletedProcess(
            args=["git", "rev-parse"], returncode=0, stdout=f"{upstream}\n", stderr=""
        )

    monkeypatch.setattr(
        aegis_installer,
        "_run_target_git",
        fake_git,
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_view",
        lambda _target, _number: {"available": True, "reason": "", "pr": merged_pr},
    )

    snapshot = aegis_installer.delivery_snapshot(tmp_path, pr_number=256)

    assert snapshot["available"] is True
    assert snapshot["action"] == "pr_merged"
    assert snapshot["branch"] == "feat/task-234-witness-delivery-projection"
    assert snapshot["head_commit"] == "abc1234"
    assert snapshot["upstream"] == "origin/feat/task-234-witness-delivery-projection"


def test_installed_gate_allows_taskmaster_completion_after_closeout(tmp_path: Path) -> None:
    target = tmp_path / "post-closeout-taskmaster"
    target.mkdir()
    taskmaster_tasks = target / ".taskmaster" / "tasks"
    taskmaster_tasks.mkdir(parents=True)
    (taskmaster_tasks / "tasks.json").write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Add visible Add to cart button",
                            "status": "pending",
                            "dependencies": [],
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="add-visible-add-to-cart-button",
        title="Add visible Add to cart button",
        source_root=REPO_ROOT,
    )
    current_work_path = target / AEGIS_CURRENT_WORK_REL
    current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
    current_work["status"] = "completed"
    current_work["closeout_passed_at"] = "2026-05-30T15:48:41Z"
    current_work["task"]["status"] = "completed"
    current_work_path.write_text(json.dumps(current_work, indent=2) + "\n", encoding="utf-8")
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=target,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()

    guidance = next_action(target, source_root=REPO_ROOT)
    assert guidance["phase"] == "deliver"
    assert guidance["state"] == "delivery_pending"
    assert guidance["details"]["delivery"]["next_safe_action"] == "push_branch"
    assert guidance["suggested_cli"] == f"git push -u origin {branch}"

    done_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=42 --status=done"},
        },
    )
    assert done_gate.returncode == 0, done_gate.stderr
    done_posttool = run_target_posttooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=42 --status=done"},
        },
    )
    assert done_posttool.returncode == 0, done_posttool.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    push_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": f"git push -u origin {branch} 2>&1 | tail -15"},
        },
    )
    assert push_gate.returncode == 0, push_gate.stderr

    head_push_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --set-upstream origin HEAD"},
        },
    )
    assert head_push_gate.returncode == 0, head_push_gate.stderr

    pr_create_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    f"gh pr create --draft --base main --head {branch} "
                    "--title 'Task 42' --body 'Closeout passed'"
                )
            },
        },
    )
    assert pr_create_gate.returncode == 0, pr_create_gate.stderr

    pr_ready_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "gh pr ready"},
        },
    )
    assert pr_ready_gate.returncode == 0, pr_ready_gate.stderr

    pr_merge_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "gh pr merge --squash --delete-branch"},
        },
    )
    assert pr_merge_gate.returncode == 0, pr_merge_gate.stderr

    force_push_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": f"git push --force origin {branch}"},
        },
    )
    assert force_push_gate.returncode == 2
    assert "Non-overridable violation" in force_push_gate.stderr
    assert "force-pushing is prohibited" in force_push_gate.stderr
    assert "NOT override-eligible" in force_push_gate.stderr

    wrong_branch_push_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git push -u origin feat/task-99-other"},
        },
    )
    assert wrong_branch_push_gate.returncode == 2
    assert "readiness is BLOCKED" in wrong_branch_push_gate.stderr

    wrong_branch_pr_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "gh pr create --draft --head feat/task-99-other"},
        },
    )
    assert wrong_branch_pr_gate.returncode == 2
    assert "readiness is BLOCKED" in wrong_branch_pr_gate.stderr

    numbered_pr_merge_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "gh pr merge 99 --squash"},
        },
    )
    assert numbered_pr_merge_gate.returncode == 2
    assert "readiness is BLOCKED" in numbered_pr_merge_gate.stderr

    admin_pr_merge_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "gh pr merge --squash --admin"},
        },
    )
    assert admin_pr_merge_gate.returncode == 2
    assert "readiness is BLOCKED" in admin_pr_merge_gate.stderr

    substitution_pr_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"gh pr create --draft --head {branch} --title $(touch owned)"
            },
        },
    )
    assert substitution_pr_gate.returncode == 2
    assert "readiness is BLOCKED" in substitution_pr_gate.stderr

    redirected_pr_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": f"gh pr create --draft --head {branch} > pr.txt"},
        },
    )
    assert redirected_pr_gate.returncode == 2
    assert "readiness is BLOCKED" in redirected_pr_gate.stderr

    generate_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "test -f scripts/codex-task; task-master generate"},
        },
    )
    assert generate_gate.returncode == 0, generate_gate.stderr

    wrong_task_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=99 --status=done"},
        },
    )
    assert wrong_task_gate.returncode == 2
    assert "readiness is BLOCKED" in wrong_task_gate.stderr

    source_edit_gate = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.ts"}},
    )
    assert source_edit_gate.returncode == 2
    assert "readiness is BLOCKED" in source_edit_gate.stderr


def test_public_init_requires_claude_reload_before_start_as_next_action(tmp_path: Path) -> None:
    target = tmp_path / "public-init-guided-repo"
    target.mkdir()

    initialized = initialize_project(target, source_root=REPO_ROOT)

    assert initialized["status"] == "initialized"
    assert initialized["install"]["client_reload"]["required"] is True
    assert initialized["next_action"]["action"] == "restart_claude_before_mutation"
    assert "restart Claude" in initialized["next_action"]["message"]
    assert initialized["next_action"]["suggested_mcp"]["tool"] == "aegis.next"
    assert initialized["next_action"]["details"]["client_reload_required"] is True
    assert ".claude/settings.json" in initialized["next_action"]["details"]["changed_paths"]
    assert (
        initialized["next_action"]["details"]["post_reload"]
        == "Run aegis.next, then start/kickoff tracked work before source edits."
    )


def test_next_action_guides_active_workflow_states(tmp_path: Path) -> None:
    target = tmp_path / "guided-workflow"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="guided-task",
        title="Guided Task",
        goals=["Exercise next action guidance"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )

    scope_required = next_action(target, source_root=REPO_ROOT)
    assert scope_required["phase"] == "scope"
    assert scope_required["state"] == "scope_required"
    assert scope_required["suggested_mcp_call"]["tool"] == "aegis.log"
    assert scope_required["suggested_mcp_call"]["arguments"]["plan_step"] == "auto"

    scope_logged = log_work(
        target,
        handler="claude:scope",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope_logged["status"] == "logged"

    implement_required = next_action(target, source_root=REPO_ROOT)
    assert implement_required["phase"] == "implement"
    assert implement_required["state"] == "implementation_required"
    assert "native" in implement_required["architecture_notes"].lower()

    pending_payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": f"{current_work['paths']['reports']}/evidence.txt"},
    }
    evidence_file = target / current_work["paths"]["reports"] / "evidence.txt"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text("implementation evidence\n", encoding="utf-8")
    run_target_posttooluse(target, pending_payload)

    pending_required = next_action(target, source_root=REPO_ROOT)
    assert pending_required["phase"] == "track"
    assert pending_required["state"] == "pending_tracking"
    assert pending_required["suggested_mcp_call"]["arguments"]["pending_event_id"] == "current"

    implementation_logged = log_work(
        target,
        pending_event_id="current",
        note="Recorded implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert implementation_logged["status"] == "logged"

    verify_required = next_action(target, source_root=REPO_ROOT)
    assert verify_required["phase"] == "verify"
    assert verify_required["state"] == "task_verification_required"

    verification_rel = f"{current_work['paths']['reports']}/task-verification.md"
    (target / verification_rel).write_text("verification passed\n", encoding="utf-8")
    log_work(
        target,
        handler="claude:verify",
        evidence=verification_rel,
        note="Recorded task verification evidence",
        event_class="verification",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    strict_required = next_action(target, source_root=REPO_ROOT)
    assert strict_required["state"] == "strict_verification_required"
    assert strict_required["suggested_mcp_call"]["tool"] == "aegis.verify"


def test_log_work_plan_step_auto_infers_scope_implementation_and_verify(tmp_path: Path) -> None:
    target = tmp_path / "auto-plan-step"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="auto-step",
        title="Auto Step",
        goals=["Exercise deterministic plan step inference"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )

    scope = log_work(
        target,
        handler="claude:scope",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="auto",
        plan_status="completed",
    )
    assert scope["plan"]["step"] == "plan-step-scope"
    assert scope["plan"]["inferred"] is True
    assert scope["plan"]["inference_reason"] == "event_class=scope"

    evidence_rel = f"{current_work['paths']['reports']}/implementation.txt"
    evidence_path = target / evidence_rel
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("implementation evidence\n", encoding="utf-8")
    run_target_posttooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": evidence_rel}},
    )
    implementation = log_work(
        target,
        pending_event_id="current",
        note="Recorded implementation evidence",
        plan_step="auto",
        plan_status="completed",
    )
    assert implementation["plan"]["step"] == "plan-step-implement"
    assert implementation["plan"]["inferred"] is True
    assert implementation["plan"]["inference_reason"] == "event_class=implementation"

    verification_report = verify(target, source_root=REPO_ROOT, strict=True)
    assert verification_report["status"] == "passed"
    strict_log = log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="auto",
        plan_status="completed",
    )
    assert strict_log["plan"]["step"] == "plan-step-verify"
    assert strict_log["plan"]["inferred"] is True
    assert strict_log["plan"]["strict_verification_evidence"] is True


def test_log_work_plan_step_auto_does_not_infer_implementation_from_handler_text(
    tmp_path: Path,
) -> None:
    target = tmp_path / "auto-plan-step-no-handler-substring"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="auto-step-neutral",
        title="Auto Step Neutral",
    )

    with pytest.raises(AegisError, match="plan-step auto could not infer"):
        log_work(
            target,
            handler="bash:jq-edit-output",
            evidence="docs/ai/work-tracking/active/example/reports/read-output.json",
            note="Read reconcile output without mutating source",
            plan_step="auto",
            plan_status="completed",
        )


def test_log_work_replay_does_not_duplicate_swhe_entries(tmp_path: Path) -> None:
    target = tmp_path / "log-replay"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="log-replay", title="Log Replay")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    evidence_rel = f"{current_work['paths']['work_tracking']}/FINDINGS.md"

    first = log_work(
        target,
        handler="claude:scope",
        evidence=evidence_rel,
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="auto",
        plan_status="completed",
    )
    replay = log_work(
        target,
        handler="claude:scope",
        evidence=evidence_rel,
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="auto",
        plan_status="completed",
    )

    assert first["status"] == "logged"
    assert replay["status"] == "already_logged"
    assert replay["idempotent"] is True
    swhe = f"[S:{first['entry']['s']}|W:{first['entry']['w']}|H:claude:scope|E:{evidence_rel}]"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(
        encoding="utf-8"
    )
    assert session_text.count(swhe) == 1
    assert tracker_text.count(swhe) == 1


def test_log_work_replay_can_backfill_missing_surfaces_without_duplicate_core_entries(
    tmp_path: Path,
) -> None:
    target = tmp_path / "log-replay-backfill"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="log-backfill", title="Log Backfill")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    evidence_rel = f"{current_work['paths']['reports']}/implementation.txt"
    (target / evidence_rel).parent.mkdir(parents=True, exist_ok=True)
    (target / evidence_rel).write_text("implementation\n", encoding="utf-8")

    first = log_work(
        target,
        handler="claude:Write",
        evidence=evidence_rel,
        note="Recorded implementation evidence",
        surfaces=["implementation"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    replay = log_work(
        target,
        handler="claude:Write",
        evidence=evidence_rel,
        note="Recorded implementation evidence",
        surfaces=["changelog"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )

    assert first["status"] == "logged"
    assert replay["status"] == "logged"
    assert replay["replay_completed_missing_surfaces"] is True
    assert replay["paths"]["surfaces"] == {
        "changelog": f"{current_work['paths']['work_tracking']}/CHANGELOG.md"
    }
    swhe = f"[S:{first['entry']['s']}|W:{first['entry']['w']}|H:claude:Write|E:{evidence_rel}]"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(
        encoding="utf-8"
    )
    implementation_text = (
        target / current_work["paths"]["work_tracking"] / "IMPLEMENTATION.md"
    ).read_text(encoding="utf-8")
    changelog_text = (target / current_work["paths"]["work_tracking"] / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    assert session_text.count(swhe) == 1
    assert tracker_text.count(swhe) == 1
    assert implementation_text.count(swhe) == 1
    assert changelog_text.count(swhe) == 1


def test_log_work_plan_step_auto_rejects_ambiguous_inference(tmp_path: Path) -> None:
    target = tmp_path / "ambiguous-auto-plan-step"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="ambiguous-auto",
        title="Ambiguous Auto",
        goals=["Exercise ambiguous plan step inference"],
    )
    with pytest.raises(AegisError, match="plan-step auto is ambiguous"):
        log_work(
            target,
            handler="claude:scope",
            evidence=AEGIS_VERIFY_REPORT_REL,
            note="Attempted ambiguous auto plan step",
            plan_step="auto",
        )


def test_kickoff_creates_native_ready_state_without_taskmaster_or_serena(tmp_path: Path) -> None:
    target = tmp_path / "portable-repo"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"
    assert not (target / ".taskmaster").exists()
    assert not (target / ".serena").exists()

    blocked = run_target_readiness(target)
    assert blocked.returncode == 2
    assert "branch 'main' does not contain a task ID" in blocked.stdout

    blocked_verify = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "aegis verify --target-dir ."}},
    )
    assert blocked_verify.returncode == 2
    assert "Aegis readiness is BLOCKED" in blocked_verify.stderr

    blocked_mcp_verify = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_verify",
            "tool_input": {"target_dir": target.as_posix(), "strict": True},
        },
    )
    assert blocked_mcp_verify.returncode == 2
    assert "Aegis readiness is BLOCKED" in blocked_mcp_verify.stderr

    bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": './.aegis/bin/aegis kickoff --task 1 --slug portable-smoke --title "Portable Smoke"'
            },
        },
    )
    assert bootstrap.returncode == 0, bootstrap.stderr

    start_bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": './.aegis/bin/aegis start "Portable Smoke"'},
        },
    )
    assert start_bootstrap.returncode == 0, start_bootstrap.stderr

    mcp_start_bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_start",
            "tool_input": {
                "target_dir": target.as_posix(),
                "title": "Portable Smoke",
                "apply": True,
            },
        },
    )
    assert mcp_start_bootstrap.returncode == 0, mcp_start_bootstrap.stderr

    kickoff_report = kickoff(
        target,
        task_id="1",
        slug="portable-smoke",
        title="Portable Smoke",
        goals=["Prove Aegis can reach READY without Taskmaster or Serena"],
    )
    assert kickoff_report["status"] == "started"
    assert kickoff_report["branch"]["current"] == "feat/task-1-portable-smoke"

    ready = run_target_readiness(target)
    assert ready.returncode == 0, ready.stdout + ready.stderr
    assert ready.stdout.strip().startswith("READY | task=1")
    assert (
        "Aegis current work Task 1 is in-progress"
        in subprocess.run(
            ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--root", str(target)],
            cwd=target,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).stdout
    )

    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    assert current_work["task"]["id"] == "1"
    assert current_work["integrations"]["taskmaster"] == {"detected": False, "required": False}
    assert current_work["integrations"]["serena"] == {"detected": False, "required": False}
    assert (target / "sessions" / "current").is_symlink()
    assert (target / "plans" / "current").is_symlink()
    assert (target / ".aegis" / "bin" / "aegis").is_file()
    assert os.access(target / ".aegis" / "bin" / "aegis", os.X_OK)
    assert (target / current_work["paths"]["work_tracking"] / "TRACKER.md").is_file()

    evidence_path = "src/allowed-evidence.txt"
    allowed = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": evidence_path},
        },
    )
    assert allowed.returncode == 0, allowed.stderr

    (target / evidence_path).parent.mkdir(parents=True, exist_ok=True)
    (target / evidence_path).write_text("allowed evidence\n", encoding="utf-8")
    tracked = run_target_posttooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": evidence_path}},
    )
    assert tracked.returncode == 0, tracked.stderr
    pending_payload = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    pending_event = pending_payload["events"][0]
    assert pending_event["evidence_location"]["path"] == evidence_path
    assert pending_event["evidence_location"]["display"] == f"{evidence_path}:1"
    pending_next = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/blocked-before-log.txt"},
        },
    )
    assert pending_next.returncode == 2
    assert "pending S:W:H:E tracking must be logged" in pending_next.stderr

    with pytest.raises(AegisError, match="does not match any pending S:W:H:E tracking event"):
        log_work(
            target,
            handler="claude-installer-test",
            evidence="src/wrong-evidence.txt",
            note="Tried to log the wrong evidence",
        )
    assert (target / AEGIS_PENDING_TRACKING_REL).is_file()

    logged = log_work(
        target,
        handler="claude-installer-test",
        evidence=evidence_path,
        note="Recorded installer test evidence",
        plan_step="plan-step-implement",
        plan_status="in-progress",
    )
    assert logged["status"] == "logged"
    assert logged["pending"]["cleared"] == 1
    assert logged["entry"]["evidence_location"]["display"] == f"{evidence_path}:1"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(
        encoding="utf-8"
    )
    plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
    implementation_text = (
        target / current_work["paths"]["work_tracking"] / "IMPLEMENTATION.md"
    ).read_text(encoding="utf-8")
    changelog_text = (target / current_work["paths"]["work_tracking"] / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    handoff_text = (target / current_work["paths"]["work_tracking"] / "HANDOFF.md").read_text(
        encoding="utf-8"
    )
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in session_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in tracker_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in implementation_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in changelog_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in handoff_text
    assert (
        "| plan-step-implement | Make only task-scoped changes and record implementation notes |"
        in plan_text
    )
    assert f"; {evidence_path} | in-progress |" in plan_text
    assert logged["paths"]["surfaces"] == {
        "implementation": f"{current_work['paths']['work_tracking']}/IMPLEMENTATION.md",
        "changelog": f"{current_work['paths']['work_tracking']}/CHANGELOG.md",
        "handoff": f"{current_work['paths']['work_tracking']}/HANDOFF.md",
    }
    assert logged["plan"] == {
        "updated": True,
        "step": "plan-step-implement",
        "status": "in-progress",
        "evidence": evidence_path,
        "inferred": False,
        "inference_reason": None,
        "strict_verification_evidence": False,
    }

    generic_logged = log_work(
        target,
        handler="claude-note",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Recorded generic workflow note without changing plan state",
        surfaces=["findings"],
    )
    assert generic_logged["status"] == "logged"
    assert generic_logged["plan"] == {
        "updated": False,
        "step": None,
        "status": None,
        "evidence": f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        "inferred": False,
        "inference_reason": None,
        "strict_verification_evidence": False,
    }

    verify_loop_payload = {
        "tool_name": "Bash",
        "tool_input": {
            "command": (
                f"grep -q '{evidence_path}' sessions/current 2>/dev/null && "
                f"grep -q '{evidence_path}' plans/current 2>/dev/null"
            )
        },
    }
    read_only_verify = run_target_pretooluse(target, verify_loop_payload)
    assert read_only_verify.returncode == 0, read_only_verify.stderr
    tracked_verify = run_target_posttooluse(target, verify_loop_payload)
    assert tracked_verify.returncode == 0, tracked_verify.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    protected = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "CODEX.md"}},
    )
    assert protected.returncode == 2
    assert "Protected path(s):" in protected.stderr


def test_blocked_branch_deadlock_allows_pending_log_and_uninstall_recovery(tmp_path: Path) -> None:
    target = tmp_path / "blocked-branch-recovery"
    init_git_repo(target)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="blocked-recovery",
        title="Blocked Recovery",
        goals=["Exercise recovery from non-task branch deadlock"],
        source_root=REPO_ROOT,
    )

    git(target, "switch", "-c", "chore/taskmaster-ledger-reconciliation")
    post = run_target_posttooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git switch -c chore/taskmaster-ledger-reconciliation"},
        },
    )
    assert post.returncode == 0, post.stderr
    assert (target / AEGIS_PENDING_TRACKING_REL).is_file()

    blocked = run_target_readiness(target)
    assert blocked.returncode == 2
    assert (
        "branch 'chore/taskmaster-ledger-reconciliation' does not contain a task ID"
        in blocked.stdout
    )

    ordinary_write = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "touch source.txt"}},
    )
    assert ordinary_write.returncode == 2
    assert "Aegis readiness is BLOCKED" in ordinary_write.stderr

    blocked_verify = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "./.aegis/bin/aegis verify --target-dir ."},
        },
    )
    assert blocked_verify.returncode == 2
    assert "Aegis readiness is BLOCKED" in blocked_verify.stderr

    pending_log = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    "./.aegis/bin/aegis log --target-dir . --pending-id current "
                    "--note 'Recorded non-task-branch recovery event' "
                    "--plan-step plan-step-emergency --plan-status completed"
                )
            },
        },
    )
    assert pending_log.returncode == 0, pending_log.stderr
    log_work(
        target,
        pending_event_id="current",
        note="Recorded non-task-branch recovery event",
        plan_step="plan-step-emergency",
        plan_status="completed",
    )
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()
    assert run_target_stop_gate(target).returncode == 0

    uninstall_preview = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "./.aegis/bin/aegis uninstall --target-dir ."},
        },
    )
    assert uninstall_preview.returncode == 0, uninstall_preview.stderr

    uninstall_apply = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "./.aegis/bin/aegis uninstall --target-dir . --apply"},
        },
    )
    assert uninstall_apply.returncode == 0, uninstall_apply.stderr
    report = uninstall(target, source_root=REPO_ROOT, apply=True)
    assert report["status"] == "applied"
    assert not (target / ".aegis").exists()
    assert not (target / ".claude" / "settings.json").exists()
    assert (target / ".claude" / "scripts" / "pretooluse-gate.sh").is_file()
    assert run_target_stop_gate(target).returncode == 0


def test_log_work_uses_event_aware_default_surfaces(tmp_path: Path) -> None:
    target = tmp_path / "event-aware-log-surfaces"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    started = kickoff(target, task_id="42", slug="surface-defaults", title="Surface Defaults")
    assert started["next_action"]["action"] == "log_scope_before_edit"
    assert started["next_action"]["suggested_mcp"]["tool"] == "aegis.log"
    assert started["next_action"]["suggested_mcp"]["arguments"]["plan_step"] == "auto"
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    current_work["branch"] = {
        "action": "created_branch",
        "before": "main",
        "created": True,
        "current": "feat/task-42-handoff-repair",
    }
    (target / ".aegis" / "state" / "current-work.json").write_text(
        json.dumps(current_work, indent=2) + "\n", encoding="utf-8"
    )
    work_rel = current_work["paths"]["work_tracking"]
    reports_rel = current_work["paths"]["reports"]
    implementation_evidence = f"{reports_rel}/implementation.txt"
    (target / implementation_evidence).write_text("implementation\n", encoding="utf-8")

    scope = log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed event-aware logging scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope["entry"]["event_class"] == "scope"
    assert set(scope["paths"]["surfaces"]) == {"findings", "decisions", "handoff"}
    assert scope["next_action"]["action"] == "make_task_scoped_source_change"

    implementation = log_work(
        target,
        handler="claude:Write",
        evidence=implementation_evidence,
        note="Captured implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert implementation["entry"]["event_class"] == "implementation"
    assert set(implementation["paths"]["surfaces"]) == {"implementation", "changelog", "handoff"}
    assert implementation["next_action"]["action"] == "run_task_specific_verification"

    verification = log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert verification["entry"]["event_class"] == "verification"
    assert set(verification["paths"]["surfaces"]) == {"implementation", "changelog", "handoff"}
    assert verification["next_action"]["action"] == "run_closeout"

    explicit = log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/DECISIONS.md",
        note="Recorded explicit surface override",
        surfaces=["decisions"],
    )
    assert explicit["entry"]["event_class"] == "scope"
    assert set(explicit["paths"]["surfaces"]) == {"decisions"}


def test_log_work_sanitizes_multiline_plan_table_evidence(tmp_path: Path) -> None:
    target = tmp_path / "multiline-plan-evidence"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="multiline-plan", title="Multiline Plan")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    plan_path = target / current_work["paths"]["plan"]

    scope_evidence = "cmd`python - <<'PY'\nprint('scope | evidence')\nPY`"
    scope = log_work(
        target,
        handler="claude:scope",
        evidence=scope_evidence,
        note="Recorded multiline scope evidence",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope["plan"]["evidence"] == scope_evidence
    plan_text = plan_path.read_text(encoding="utf-8")
    scope_row = next(
        line for line in plan_text.splitlines() if line.startswith("| plan-step-scope |")
    )
    assert scope_row.count("|") == 5
    assert "scope &#124; evidence" in scope_row
    assert "print('scope | evidence')" not in scope_row
    rows = aegis_installer._parse_plan_rows(plan_path)
    assert rows["plan-step-scope"]["malformed"] is False
    assert rows["plan-step-scope"]["status"] == "completed"

    verify_evidence = "cmd`pytest -q\nuv run | tee verification.txt`"
    verification = log_work(
        target,
        handler="aegis:verify",
        evidence=verify_evidence,
        note="Recorded multiline verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert verification["status"] == "logged"
    assert verification["plan"]["evidence"] == verify_evidence
    plan_text = plan_path.read_text(encoding="utf-8")
    verify_row = next(
        line for line in plan_text.splitlines() if line.startswith("| plan-step-verify |")
    )
    assert verify_row.count("|") == 5
    assert "uv run &#124; tee verification.txt" in verify_row
    rows = aegis_installer._parse_plan_rows(plan_path)
    assert rows["plan-step-verify"]["malformed"] is False
    assert rows["plan-step-verify"]["status"] == "completed"


def test_log_work_keeps_pending_tracking_when_plan_table_update_fails(tmp_path: Path) -> None:
    target = tmp_path / "log-plan-failure-keeps-pending"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="atomic-log", title="Atomic Log")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    plan_path = target / current_work["paths"]["plan"]
    plan_lines = plan_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(plan_lines):
        if line.startswith("| plan-step-implement |"):
            plan_lines[index] = line.replace("changed files", "src/a.ts | src/b.ts")
    plan_path.write_text("\n".join(plan_lines).rstrip() + "\n", encoding="utf-8")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "events": [
                    {
                        "id": "keepme123",
                        "handler": "claude:Write",
                        "evidence": "src/a.ts",
                        "task": {"id": "42", "slug": "atomic-log"},
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AegisError, match="plan row for plan-step-implement is malformed"):
        log_work(
            target,
            pending_event_id="keepme123",
            note="Tried to log implementation evidence into a malformed plan row",
            plan_step="plan-step-implement",
            plan_status="completed",
        )

    pending_payload = json.loads(pending_path.read_text(encoding="utf-8"))
    assert [event["id"] for event in pending_payload["events"]] == ["keepme123"]


def test_log_work_consumes_pending_event_by_id(tmp_path: Path) -> None:
    target = tmp_path / "pending-id-log"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="pending-id", title="Pending Id")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    evidence_rel = f"{current_work['paths']['reports']}/pending-id.txt"
    (target / evidence_rel).write_text("pending\n", encoding="utf-8")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-05-23T12:00:00Z",
                "events": [
                    {
                        "id": "abc123def456",
                        "created_at": "2026-05-23T12:00:00Z",
                        "updated_at": "2026-05-23T12:00:00Z",
                        "tool": "Write",
                        "handler": "claude:Write",
                        "evidence": evidence_rel,
                        "evidence_location": {
                            "path": evidence_rel,
                            "line_start": 1,
                            "line_end": 1,
                            "line_count": 1,
                            "source": "write_file_snapshot",
                            "confidence": "file_snapshot",
                            "display": f"{evidence_rel}:1",
                        },
                        "task": {"id": "42", "slug": "pending-id"},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(AegisError, match="valid ids: abc123def456"):
        log_work(target, pending_event_id="missing", note="Tried missing pending id")

    logged = log_work(
        target,
        pending_event_id="abc123def456",
        note="Logged pending event by id",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert logged["entry"]["h"] == "claude:Write"
    assert logged["entry"]["e"] == evidence_rel
    assert logged["entry"]["evidence_location"]["display"] == f"{evidence_rel}:1"
    assert logged["pending"]["cleared"] == 1
    assert logged["pending"]["pending_event_id"] == "abc123def456"
    assert not pending_path.exists()


def test_mcp_verify_pending_event_uses_strict_report_evidence(tmp_path: Path) -> None:
    target = tmp_path / "mcp-verify-pending"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="mcp-verify", title="MCP Verify")
    (target / AEGIS_VERIFY_REPORT_REL).parent.mkdir(parents=True, exist_ok=True)
    (target / AEGIS_VERIFY_REPORT_REL).write_text("{}\n", encoding="utf-8")

    tracked = run_target_posttooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_verify",
            "tool_input": {
                "target_dir": target.as_posix(),
                "strict": True,
                "acknowledge_report_write": True,
            },
        },
    )

    assert tracked.returncode == 0, tracked.stderr
    pending_payload = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    event = pending_payload["events"][0]
    assert event["handler"] == "aegis:verify"
    assert event["evidence"] == AEGIS_VERIFY_REPORT_REL
    assert event["evidence_location"]["path"] == AEGIS_VERIFY_REPORT_REL


def test_read_only_aegis_mcp_tools_do_not_create_pending_tracking(tmp_path: Path) -> None:
    target = tmp_path / "mcp-read-only-pending"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="mcp-read-only", title="MCP Read Only")

    for tool_name in (
        "mcp__aegis__aegis_inspect",
        "mcp__aegis__aegis_status",
        "mcp__aegis__aegis_next",
        "mcp__aegis__aegis_doctor",
        "mcp__aegis__aegis_repair",
        "mcp__aegis__aegis_plan_install",
        "mcp__aegis__aegis_closeout_ready",
        "mcp__aegis__aegis_handoff_repair",
        "mcp__aegis__aegis_list_profiles",
        "mcp__aegis__aegis_explain_profile",
    ):
        payload = {"tool_name": tool_name, "tool_input": {"target_dir": target.as_posix()}}
        pretool = run_target_pretooluse(target, payload)
        assert pretool.returncode == 0, pretool.stderr
        posttool = run_target_posttooluse(target, payload)
        assert posttool.returncode == 0, posttool.stderr
        assert not (target / AEGIS_PENDING_TRACKING_REL).exists(), tool_name


def test_read_only_aegis_cli_does_not_create_pending_tracking(tmp_path: Path) -> None:
    target = tmp_path / "cli-read-only-pending"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="cli-read-only", title="CLI Read Only")

    payload = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "./.aegis/bin/aegis reconcile --target-dir . --preview-candidates"
        },
    }

    pretool = run_target_pretooluse(target, payload)
    assert pretool.returncode == 0, pretool.stderr
    posttool = run_target_posttooluse(target, payload)
    assert posttool.returncode == 0, posttool.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()


def test_installed_pretooluse_blocks_aegis_read_only_target_dir_outside_project(
    tmp_path: Path,
) -> None:
    target = tmp_path / "confined-target"
    target.mkdir()
    outside = tmp_path / "outside-project"
    outside.mkdir()
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)

    cli_payload = {
        "tool_name": "Bash",
        "tool_input": {"command": f"./.aegis/bin/aegis status --target-dir {outside.as_posix()}"},
    }
    mcp_payload = {
        "tool_name": "mcp__aegis__aegis_status",
        "tool_input": {"target_dir": outside.as_posix()},
    }

    cli_result = run_target_pretooluse(target, cli_payload)
    mcp_result = run_target_pretooluse(target, mcp_payload)

    assert cli_result.returncode == 2
    assert "target_dir escapes governed project root" in cli_result.stderr
    assert mcp_result.returncode == 2
    assert "target_dir escapes governed project root" in mcp_result.stderr


def test_closeout_reports_missing_evidence_repair_guidance(tmp_path: Path) -> None:
    target = tmp_path / "closeout-repair-guidance"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="repair-guidance", title="Repair Guidance")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    implementation_evidence = f"{current_work['paths']['reports']}/implementation.txt"
    (target / implementation_evidence).write_text("implementation\n", encoding="utf-8")

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed repair guidance scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=implementation_evidence,
        note="Captured implementation evidence with an intentionally missing changelog reference",
        surfaces=["implementation", "handoff"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence with an intentionally missing changelog reference",
        surfaces=["implementation", "handoff"],
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    failed = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)

    assert failed["status"] == "failed"
    assert failed["dry_run"] is True
    assert failed["report_written"] is False
    assert failed["next_action"]["action"] == "repair_closeout_gates_before_retry"
    assert failed["next_action"]["suggested_mcp"]["tool"] == "aegis.closeout_ready"
    repair_items = failed["repair_guidance"]["items"]
    changelog_repairs = [
        item
        for item in repair_items
        if item["kind"] == "missing_evidence_reference"
        and item["surface"] == "changelog"
        and item["evidence"] == implementation_evidence
    ]
    assert changelog_repairs
    assert "--surface changelog" in changelog_repairs[0]["command"]
    assert implementation_evidence in changelog_repairs[0]["command"]

    passed = closeout(target, source_root=REPO_ROOT, update_handoff=True)
    assert passed["status"] == "passed"
    assert any(
        item["surface"] == "changelog" and item["evidence"] == implementation_evidence
        for item in passed["populate"]["updated_surfaces"]
    )
    changelog = (target / passed["archived_work_tracking"]["to"] / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    assert implementation_evidence in changelog


def test_closeout_evidence_tokenizer_preserves_table_escaped_compound_commands() -> None:
    raw_evidence = (
        "cmd`git diff -- app/src &#124; grep -E '^\\+' &#124; tail -25`; "
        'cmd`python3 -c "import sys,json; data=json.load(sys.stdin); '
        "print(data.get('status'))\"`; "
        "reports/verification.txt"
    )

    assert aegis_installer._split_evidence_tokens(raw_evidence) == [
        "cmd`git diff -- app/src | grep -E '^\\+' | tail -25`",
        "cmd`python3 -c \"import sys,json; data=json.load(sys.stdin); print(data.get('status'))\"`",
        "reports/verification.txt",
    ]


def test_handoff_repair_converges_with_compound_bash_closeout_evidence(tmp_path: Path) -> None:
    target = tmp_path / "compound-bash-closeout"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="compound-bash", title="Compound Bash")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    implementation_evidence = (
        "cmd`git diff -- app/src/components/session/SessionPlayer.tsx 2>&1 "
        "| grep -E '^\\+' | tail -25`"
    )
    verification_evidence = (
        "cmd`./.aegis/bin/aegis verify --target-dir . --strict 2>&1 | "
        'python3 -c "import sys,json; data=json.load(sys.stdin); '
        "print(data.get('status'))\"`"
    )

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed compound Bash closeout scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Bash",
        evidence=implementation_evidence,
        note="Recorded compound Bash implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Bash",
        evidence=verification_evidence,
        note="Recorded compound Bash verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
    assert "&#124;" in plan_text
    assert "| grep" not in plan_text

    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    repaired = repair_handoff(target, source_root=REPO_ROOT)

    assert repaired["status"] == "repaired"
    assert repaired["closeout_ready_after"]["status"] == "passed"
    # TM 218: compound `cmd`...`` command tokens are ADVISORY, not required evidence —
    # requiring their verbatim multi-line string in every surface is brittle and becomes
    # unrecoverable once the originating pending event is consumed. So they are demoted out
    # of the required evidence set; closeout still converges on the real artifact
    # (the strict-verify report), which IS required.
    assert repaired["evidence"]["implementation"] == []
    assert verification_evidence not in repaired["evidence"]["verification"]
    closeout_ready = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert closeout_ready["status"] == "passed"
    assert implementation_evidence not in closeout_ready["evidence_matrix"]
    assert verification_evidence not in closeout_ready["evidence_matrix"]
    # The real artifact path stays required and present.
    strict_verify_rel = aegis_installer._normalize_evidence(target, AEGIS_VERIFY_REPORT_REL)
    assert strict_verify_rel in closeout_ready["evidence_matrix"]


def test_is_closeout_required_evidence_demotes_command_tokens() -> None:
    # TM 218: command / free-text narration tokens are advisory (non-required); durable
    # artifact paths and bare SHAs stay required.
    demoted = [
        'cmd`git commit -m "feat: x"`',
        "note`free-text observation`",
        'git commit -m "feat: x"',  # prefix-stripped command (whitespace + quotes, not a path)
        "git diff -- app/src | grep -E '^\\+' | tail -25",  # compound, shell metacharacters
    ]
    required = [
        "app/src/components/session/SessionPlayer.tsx",
        AEGIS_VERIFY_REPORT_REL,
        "docs/ai/work-tracking/active/foo/reports/impl-note.md",
        "be569cd",  # bare SHA: no whitespace/metachars, stays required
        "./relative/path.py",
    ]
    for token in demoted:
        assert aegis_installer._is_closeout_required_evidence(token) is False, token
    for token in required:
        assert aegis_installer._is_closeout_required_evidence(token) is True, token


def test_closeout_recovers_when_command_evidence_absent_from_progress_surfaces(
    tmp_path: Path,
) -> None:
    # HP-Coach 2026-06-13: a committed, strict-verify-green task whose implementation
    # evidence is a command token NOT present on session/tracker/implementation/changelog
    # (its originating pending event was consumed during the pre-216 churn era). Before TM
    # 218 this stranded closeout permanently on the four evidence gates; after demotion the
    # advisory command token no longer gates, and closeout converges on the real artifact.
    target = tmp_path / "command-evidence-recovery"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="80", slug="recovery", title="Recovery")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed recovery scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    # Implementation evidence is a command token, logged ONLY to handoff — it never reaches
    # session/tracker/implementation/changelog, exactly the lost-pending-event state.
    log_work(
        target,
        handler="claude:Bash",
        evidence='cmd`git commit -m "feat: recovery"`',
        note="Recorded the implementation commit command",
        surfaces=["handoff"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    result = closeout(target, source_root=REPO_ROOT, update_handoff=True)
    assert result["status"] == "passed", result.get("failed_required") or result
    # The command token is advisory — absent from the required matrix; the artifact is required.
    assert 'cmd`git commit -m "feat: recovery"`' not in result["evidence_matrix"]
    strict_verify_rel = aegis_installer._normalize_evidence(target, AEGIS_VERIFY_REPORT_REL)
    assert strict_verify_rel in result["evidence_matrix"]


def test_compound_bash_mutation_still_records_pending_tracking(tmp_path: Path) -> None:
    target = tmp_path / "compound-bash-tracking"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="compound-track", title="Compound Track")
    command = (
        'python3 -c "from pathlib import Path; '
        "Path('proof.txt').write_text('x', encoding='utf-8')\" | cat"
    )

    posttool = run_target_posttooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": command}},
    )

    assert posttool.returncode == 0, posttool.stdout + posttool.stderr
    pending = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    assert len(pending["events"]) == 1
    assert pending["events"][0]["handler"] == "bash:python3"
    assert pending["events"][0]["evidence"] == f"cmd`{command}`"


def test_kickoff_ready_state_does_not_depend_on_optional_stale_taskmaster(tmp_path: Path) -> None:
    target = tmp_path / "portable-repo-with-stale-taskmaster"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"
    simulate_claude_reload(target)

    kickoff_report = kickoff(
        target,
        task_id="1",
        slug="portable-smoke",
        title="Portable Smoke",
    )
    assert kickoff_report["status"] == "started"
    (target / ".taskmaster" / "tasks").mkdir(parents=True)
    (target / ".taskmaster" / "tasks" / "tasks.json").write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 1,
                            "title": "Portable Smoke",
                            "status": "done",
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    ready = run_target_readiness(target)

    assert ready.returncode == 0, ready.stdout + ready.stderr
    assert ready.stdout.strip().startswith("READY | task=1")
    full = subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--root", str(target)],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert full.returncode == 0, full.stdout + full.stderr
    assert "Aegis current work Task 1 is in-progress" in full.stdout
    assert "Taskmaster Task 1 is optional with status 'done'" in full.stdout


def test_strict_verify_requires_current_work_and_validates_runtime_surfaces(tmp_path: Path) -> None:
    target = tmp_path / "strict-repo"
    target.mkdir()
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    before_kickoff = verify(target, source_root=REPO_ROOT, strict=True)
    assert before_kickoff["mode"] == "strict"
    assert before_kickoff["status"] == "failed"
    assert any(
        check["gate_id"] == "workflow.current_work" and check["status"] == "fail"
        for check in before_kickoff["checks"]
    )

    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    simulate_claude_reload(target)

    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="strict-verify",
        title="Strict Verify",
        goals=["Prove strict verification validates an installed workflow runtime"],
    )
    assert kickoff_report["status"] == "started"

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)

    assert strict_report["mode"] == "strict"
    assert strict_report["status"] == "passed"
    check_ids = {check["gate_id"] for check in strict_report["checks"]}
    assert {
        "manifest.managed_files",
        "runtime.local_cli_shim",
        "runtime.workflow_templates",
        "workflow.current_work",
        "workflow.branch_task_alignment",
        "workflow.tracking_surfaces",
        "mutation.pending_tracking_empty",
        "claude.required_files",
        "claude.hooks_registered",
        "protection.codex_owned_paths",
        "integrations.taskmaster_optional",
        "integrations.serena_optional",
    }.issubset(check_ids)
    assert strict_report["summary"]["failed_required"] == 0
    assert strict_report["next_action"]["action"] == "log_strict_verification_before_closeout"
    assert strict_report["next_action"]["suggested_mcp"]["tool"] == "aegis.log"
    assert (
        strict_report["next_action"]["suggested_mcp"]["arguments"]["pending_event_id"] == "current"
    )


def test_strict_verify_uses_tracked_codex_hook_trust_without_install_report(
    tmp_path: Path,
) -> None:
    target = tmp_path / "clean-checkout-codex-trust"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    simulate_codex_reload(target)
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="70",
        slug="clean-checkout-codex-trust",
        title="Clean Checkout Codex Trust",
        goals=["Prove strict verification uses tracked hook-trust policy"],
    )
    (target / aegis_installer.AEGIS_INSTALL_REPORT_REL).unlink()

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)
    trust_check = next(
        check
        for check in strict_report["checks"]
        if check["gate_id"] == "codex.hook_trust_guidance"
    )
    assert trust_check["status"] == "pass"
    assert trust_check["details"]["source"] == "manifest_gate"
    assert trust_check["details"]["client_trust_asserted"] is False
    assert trust_check["details"]["supplemental_install_evidence"] == {
        "install_report_present": False,
        "install_report_parsed": False,
        "hook_trust_guidance_present": False,
        "matches_tracked_contract": False,
        "client_trust_asserted": False,
    }
    assert strict_report["summary"]["failed_required"] == 0

    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    trust_gate = next(gate for gate in manifest["gates"] if gate["id"] == "codex.hook_trust")
    trust_gate["unsupported_reason"] = "Review hooks manually."
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    tampered_report = verify(target, source_root=REPO_ROOT, strict=True)
    tampered_trust_check = next(
        check
        for check in tampered_report["checks"]
        if check["gate_id"] == "codex.hook_trust_guidance"
    )
    assert tampered_trust_check["status"] == "fail"
    assert tampered_trust_check["details"]["source"] is None


def test_strict_verify_treats_install_report_hook_trust_as_supplemental(
    tmp_path: Path,
) -> None:
    target = tmp_path / "install-report-supplemental"
    init_git_repo(target)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    simulate_codex_reload(target)
    kickoff(
        target,
        task_id="71",
        slug="install-report-supplemental",
        title="Install Report Supplemental",
    )

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)
    trust_check = next(
        check
        for check in strict_report["checks"]
        if check["gate_id"] == "codex.hook_trust_guidance"
    )

    assert strict_report["summary"]["failed_required"] == 0
    assert trust_check["status"] == "pass"
    assert trust_check["details"]["source"] == "manifest_gate"
    assert trust_check["details"]["client_trust_asserted"] is False
    assert trust_check["details"]["supplemental_install_evidence"] == {
        "install_report_present": True,
        "install_report_parsed": True,
        "hook_trust_guidance_present": True,
        "matches_tracked_contract": True,
        "client_trust_asserted": False,
    }


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("__missing_gate__", None),
        ("review_command", None),
        ("review_command", {"command": "/hooks"}),
        ("bypass_allowed", True),
        ("settings_path", ".codex/untrusted-hooks.json"),
        ("review_command", "/hooks --trust-all"),
        ("hash_scope", "settings_file"),
    ],
)
def test_tracked_codex_hook_trust_contract_fails_closed(
    tmp_path: Path,
    field: str,
    invalid_value: object,
) -> None:
    target = tmp_path / "invalid-tracked-guidance"
    init_git_repo(target)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if field == "__missing_gate__":
        manifest["gates"] = [
            gate for gate in manifest["gates"] if gate.get("id") != "codex.hook_trust"
        ]
    else:
        trust_gate = next(gate for gate in manifest["gates"] if gate["id"] == "codex.hook_trust")
        if invalid_value is None:
            trust_gate.pop(field)
        else:
            trust_gate[field] = invalid_value

    schema = json.loads(
        (SCHEMA_ROOT / "foundation-manifest.schema.json").read_text(encoding="utf-8")
    )
    assert list(Draft202012Validator(schema).iter_errors(manifest))
    trust_check = next(
        check
        for check in aegis_installer._strict_codex_checks(target, manifest)
        if check["gate_id"] == "codex.hook_trust_guidance"
    )
    assert trust_check["status"] == "fail"
    assert trust_check["required"] is True
    assert trust_check["details"]["source"] is None
    assert trust_check["details"]["client_trust_asserted"] is False


def test_stale_install_report_cannot_override_invalid_tracked_hook_trust(
    tmp_path: Path,
) -> None:
    target = tmp_path / "stale-install-report"
    init_git_repo(target)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    trust_gate = next(gate for gate in manifest["gates"] if gate["id"] == "codex.hook_trust")
    trust_gate["bypass_allowed"] = True
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)
    trust_check = next(
        check
        for check in strict_report["checks"]
        if check["gate_id"] == "codex.hook_trust_guidance"
    )

    assert trust_check["status"] == "fail"
    assert trust_check["details"]["source"] is None
    assert trust_check["details"]["supplemental_install_evidence"] == {
        "install_report_present": True,
        "install_report_parsed": True,
        "hook_trust_guidance_present": True,
        "matches_tracked_contract": True,
        "client_trust_asserted": False,
    }
    assert strict_report["summary"]["failed_required"] > 0


def test_clean_secondary_worktree_passes_strict_verify_and_closeout_dry_run(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    init_git_repo(primary)
    (primary / ".gitignore").write_text(
        ".aegis/reports/\n.aegis/state/\n.aegis/capsule/\n",
        encoding="utf-8",
    )
    install(
        primary,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )
    git(primary, "add", "-A")
    git(primary, "commit", "-m", "install tracked Aegis runtime")
    git(
        primary,
        "worktree",
        "add",
        "-b",
        "feat/task-72-clean-hook-trust-worktree",
        secondary.as_posix(),
    )

    assert not (secondary / aegis_installer.AEGIS_INSTALL_REPORT_REL).exists()
    kickoff(
        secondary,
        task_id="72",
        slug="clean-hook-trust-worktree",
        title="Clean Hook Trust Worktree",
        goals=["Prove clean-worktree strict verification and closeout portability"],
    )
    current_work = json.loads((secondary / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    work_rel = current_work["paths"]["work_tracking"]
    report_rel = f"{current_work['paths']['reports']}/portability-evidence.txt"
    evidence_path = secondary / report_rel
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("clean secondary worktree portability evidence\n", encoding="utf-8")

    assert (
        log_work(
            secondary,
            handler="codex:scope",
            evidence=f"{work_rel}/FINDINGS.md",
            note="Confirmed clean-worktree portability scope",
            surfaces=["findings", "decisions"],
            plan_step="plan-step-scope",
            plan_status="completed",
        )["status"]
        == "logged"
    )
    assert (
        log_work(
            secondary,
            handler="codex:apply_patch",
            evidence=report_rel,
            note="Recorded clean-worktree portability implementation evidence",
            plan_step="plan-step-implement",
            plan_status="completed",
        )["status"]
        == "logged"
    )
    assert (
        log_work(
            secondary,
            handler="verify:inspection",
            evidence="cmd`test -f portability-evidence.txt`",
            note="Verified clean-worktree portability evidence",
            plan_step="plan-step-verify",
            plan_status="completed",
        )["status"]
        == "logged"
    )

    strict = verify(secondary, source_root=REPO_ROOT, strict=True)
    trust_check = next(
        check for check in strict["checks"] if check["gate_id"] == "codex.hook_trust_guidance"
    )
    assert strict["status"] == "passed"
    assert strict["summary"]["failed_required"] == 0
    assert trust_check["status"] == "pass"
    assert trust_check["details"]["source"] == "manifest_gate"
    assert (
        trust_check["details"]["supplemental_install_evidence"]["install_report_present"] is False
    )
    assert (
        log_work(
            secondary,
            handler="aegis:verify",
            evidence=AEGIS_VERIFY_REPORT_REL,
            note="Recorded strict clean-worktree verification evidence",
            plan_step="plan-step-verify",
            plan_status="completed",
        )["status"]
        == "logged"
    )

    repaired = repair_handoff(secondary, source_root=REPO_ROOT)
    assert repaired["status"] == "repaired"
    manifest_before = (secondary / AEGIS_MANIFEST_REL).read_bytes()
    handoff_path = secondary / work_rel / "HANDOFF.md"
    handoff_before = handoff_path.read_bytes()
    dry_run = closeout(
        secondary,
        source_root=REPO_ROOT,
        update_handoff=True,
        dry_run=True,
    )

    assert dry_run["status"] == "passed"
    assert dry_run["summary"]["failed_required"] == 0
    assert dry_run["dry_run"] is True
    assert dry_run["report_written"] is False
    assert dry_run["state_updated"] is False
    assert not (secondary / AEGIS_CLOSEOUT_REPORT_REL).exists()
    assert (secondary / AEGIS_MANIFEST_REL).read_bytes() == manifest_before
    assert handoff_path.read_bytes() == handoff_before
    assert not (secondary / aegis_installer.AEGIS_INSTALL_REPORT_REL).exists()


def test_tracked_codex_hook_trust_guidance_rejects_missing_or_duplicate_gate() -> None:
    gates = aegis_installer._gates(["codex"])
    trust_gate = next(gate for gate in gates if gate["id"] == "codex.hook_trust")
    manifest = {"gates": gates}

    assert aegis_installer._tracked_codex_hook_trust_guidance(manifest)["source"] == (
        "manifest_gate"
    )

    missing_gate_manifest = {"gates": [gate for gate in gates if gate["id"] != "codex.hook_trust"]}
    assert aegis_installer._tracked_codex_hook_trust_guidance(missing_gate_manifest) == {}

    duplicate_gate_manifest = {"gates": [*gates, dict(trust_gate)]}
    assert aegis_installer._tracked_codex_hook_trust_guidance(duplicate_gate_manifest) == {}


def test_local_cli_shim_resolves_packaged_asset_source_root(tmp_path: Path) -> None:
    target = tmp_path / "packaged-shim-repo"
    target.mkdir()
    package_asset_root = REPO_ROOT / "aegis_foundation" / "assets"

    install_report = install(
        target,
        source_root=package_asset_root,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    env = {**os.environ, "PATH": "/usr/bin:/bin"}
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [str(target / ".aegis" / "bin" / "aegis"), "status", "--target-dir", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["installed"] is True
    assert payload["status"] == "current"


def test_closeout_requires_semantic_handoff_and_passes_with_update(tmp_path: Path) -> None:
    target = tmp_path / "closeout-repo"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"
    simulate_claude_reload(target)

    kickoff(
        target,
        task_id="42",
        slug="closeout-gate",
        title="Closeout Gate",
        goals=["Prove closeout validates semantic workflow completion"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    report_rel = f"{current_work['paths']['reports']}/closeout-evidence.txt"
    (target / report_rel).write_text("closeout evidence\n", encoding="utf-8")

    scope = log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed closeout gate scope",
        surfaces=["findings", "decisions"],
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope["status"] == "logged"
    implementation = log_work(
        target,
        handler="claude:Write",
        evidence=report_rel,
        note="Recorded closeout implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert implementation["status"] == "logged"
    verification = log_work(
        target,
        handler="verify:inspection",
        evidence="cmd`test -f closeout-evidence.txt`",
        note="Verified closeout evidence exists",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert verification["status"] == "logged"

    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    strict_log = log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert strict_log["status"] == "logged"

    manifest_before_dry_run = (target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    handoff_path = target / work_rel / "HANDOFF.md"
    handoff_before_dry_run = handoff_path.read_text(encoding="utf-8")
    handoff_before_dry_run = handoff_before_dry_run.replace(
        "\n## Progress Log",
        "\n## Current Issues/Blockers\n"
        "- Operator-authored blocker context must remain intact.\n\n"
        "## Progress Log",
    )
    handoff_path.write_text(handoff_before_dry_run, encoding="utf-8")
    dry_failed = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert dry_failed["status"] == "failed"
    assert dry_failed["dry_run"] is True
    assert dry_failed["report_written"] is False
    assert dry_failed["state_updated"] is False
    assert dry_failed["handoff"]["updated"] is False
    assert dry_failed["handoff"]["would_update"] is True
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()
    assert (target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8") == manifest_before_dry_run
    assert handoff_path.read_text(encoding="utf-8") == handoff_before_dry_run
    concise_failed = run_cli(
        [
            "aegis",
            "closeout",
            "--target-dir",
            str(target),
            "--dry-run",
            "--update-handoff",
        ]
    )
    assert concise_failed.returncode == 1
    assert "Aegis closeout readiness: FAILED" in concise_failed.stdout
    assert "failed_required:" in concise_failed.stdout
    assert "failed_gates:" in concise_failed.stdout
    assert "closeout.handoff.current_state" in concise_failed.stdout
    assert not concise_failed.stdout.lstrip().startswith("{")
    json_failed = run_cli(
        [
            "aegis",
            "closeout",
            "--target-dir",
            str(target),
            "--dry-run",
            "--update-handoff",
            "--json",
        ]
    )
    assert json_failed.returncode == 1
    assert json.loads(json_failed.stdout)["status"] == "failed"

    passed = closeout(target, source_root=REPO_ROOT)
    assert passed["status"] == "passed"
    assert passed["next_action"]["action"] == "run_post_closeout_doctor"
    assert passed["next_action"]["suggested_mcp"]["tool"] == "aegis.doctor"
    assert passed["summary"]["failed_required"] == 0
    assert passed["handoff"]["updated"] is True
    assert passed["git"]["legacy_manual_only"] == ["gac"]
    assert 'git commit -m "<type(scope): summary>"' in passed["git"]["guidance"]
    concise_passed = aegis_installer.format_closeout_summary(passed)
    assert "Aegis closeout: PASSED" in concise_passed
    assert "closeout_report: .aegis/reports/closeout-report.json (written)" in concise_passed
    assert (target / AEGIS_CLOSEOUT_REPORT_REL).is_file()
    closeout_report = json.loads((target / AEGIS_CLOSEOUT_REPORT_REL).read_text(encoding="utf-8"))
    archive_rel = (
        work_rel.replace(
            "docs/ai/work-tracking/active/",
            "docs/ai/work-tracking/archive/",
        ).removesuffix("-ACTIVE")
        + "-COMPLETED"
    )
    assert closeout_report["report_written"] is True
    assert closeout_report["state_updated"] is True
    assert closeout_report["archived_work_tracking"] == {"from": work_rel, "to": archive_rel}
    assert closeout_report["current_work"]["paths"]["work_tracking"] == archive_rel
    assert not (target / work_rel).exists()
    assert (target / archive_rel).is_dir()
    refreshed_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    assert refreshed_work["status"] == "completed"
    assert refreshed_work["task"]["status"] == "completed"
    assert refreshed_work["closeout_report"] == AEGIS_CLOSEOUT_REPORT_REL
    assert refreshed_work["paths"]["work_tracking"] == archive_rel
    archived_handoff = (target / archive_rel / "HANDOFF.md").read_text(encoding="utf-8")
    assert "Operator-authored blocker context must remain intact." in archived_handoff
    degraded_event = {
        "id": "degraded123",
        "created_at": "2026-06-01T17:00:00Z",
        "gate": "pretooluse",
        "mode": "degraded_allow",
        "action_class": "non_destructive",
        "tool": "Bash",
        "reason": "RuntimeError: synthetic gate failure",
        "raw_preview": '{"tool_name":"Bash"}',
        "previous_event_hash": "",
        "event_hash": "synthetic",
    }
    (target / AEGIS_DEGRADED_EVENTS_REL).write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-06-01T17:00:00Z",
                "events": [degraded_event],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    degraded_doctor = doctor(target, source_root=REPO_ROOT)
    assert degraded_doctor["status"] == "degraded"
    degraded_check = next(
        check
        for check in degraded_doctor["checks"]
        if check["id"] == "runtime.degraded_events_acknowledged"
    )
    assert degraded_check["status"] == "fail"
    degraded_closeout = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert degraded_closeout["status"] == "failed"
    assert "closeout.degraded_events_acknowledged" in [
        check["gate_id"] for check in degraded_closeout["checks"] if check["status"] == "fail"
    ]
    degraded_event["acknowledged_at"] = "2026-06-01T17:05:00Z"
    (target / AEGIS_DEGRADED_EVENTS_REL).write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-06-01T17:05:00Z",
                "events": [degraded_event],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    acknowledged_doctor = doctor(target, source_root=REPO_ROOT)
    assert acknowledged_doctor["status"] == "healthy"
    idempotent_dry_run = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert idempotent_dry_run["status"] == "passed"
    assert idempotent_dry_run["readiness"]["status"] == "passed"
    assert idempotent_dry_run["readiness"]["stdout"] == "READY from completed closeout state"
    assert idempotent_dry_run["next_action"]["action"] == "task_complete"
    handoff = (target / archive_rel / "HANDOFF.md").read_text(encoding="utf-8")
    assert AEGIS_CLOSEOUT_REPORT_REL in handoff
    assert AEGIS_VERIFY_REPORT_REL in handoff
    assert report_rel in handoff


def test_closeout_populates_path_lost_plan_evidence_before_final_closeout(
    tmp_path: Path,
) -> None:
    target = tmp_path / "path-lost-populate"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="path-lost", title="Path Lost")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    session_rel = current_work["paths"]["session"]
    work_rel = current_work["paths"]["work_tracking"]
    report_rel = f"{current_work['paths']['reports']}/path-lost-evidence.txt"
    (target / report_rel).write_text("path lost evidence\n", encoding="utf-8")

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed path-lost scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=report_rel,
        note="Recorded path-lost implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    for path in (target / session_rel, target / work_rel / "TRACKER.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text(
            "\n".join(line for line in lines if report_rel not in line).rstrip() + "\n",
            encoding="utf-8",
        )
    session_before = (target / session_rel).read_text(encoding="utf-8")
    tracker_before = (target / work_rel / "TRACKER.md").read_text(encoding="utf-8")
    assert report_rel not in session_before
    assert report_rel not in tracker_before
    assert report_rel in (target / work_rel / "IMPLEMENTATION.md").read_text(encoding="utf-8")
    assert report_rel in (target / work_rel / "CHANGELOG.md").read_text(encoding="utf-8")

    dry_run = closeout(target, source_root=REPO_ROOT, dry_run=True)
    assert dry_run["status"] == "failed"
    assert {
        check["gate_id"]
        for check in dry_run["checks"]
        if check["required"] and check["status"] == "fail"
    } >= {"closeout.evidence.session", "closeout.evidence.tracker"}
    assert any(
        item["surface"] == "session" and item["evidence"] == report_rel
        for item in dry_run["populate"]["would_update_surfaces"]
    )
    assert (target / session_rel).read_text(encoding="utf-8") == session_before
    assert (target / work_rel / "TRACKER.md").read_text(encoding="utf-8") == tracker_before

    passed = closeout(target, source_root=REPO_ROOT)
    assert passed["status"] == "passed"
    assert any(
        item["surface"] == "session" and item["evidence"] == report_rel
        for item in passed["populate"]["updated_surfaces"]
    )
    assert any(
        item["surface"] == "tracker" and item["evidence"] == report_rel
        for item in passed["populate"]["updated_surfaces"]
    )
    archive_rel = passed["archived_work_tracking"]["to"]
    assert report_rel in (target / session_rel).read_text(encoding="utf-8")
    assert report_rel in (target / archive_rel / "TRACKER.md").read_text(encoding="utf-8")


def test_closeout_populate_does_not_mask_pending_tracking_or_strict_verify(
    tmp_path: Path,
) -> None:
    target = tmp_path / "populate-negative"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="populate-negative", title="Populate Negative")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed populate-negative scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-06-13T12:00:00Z",
                "events": [
                    {
                        "id": "pending-pop",
                        "created_at": "2026-06-13T12:00:00Z",
                        "updated_at": "2026-06-13T12:00:00Z",
                        "tool": "Edit",
                        "handler": "claude:Edit",
                        "evidence": "src/example.py",
                        "task": {"id": "42", "slug": "populate-negative"},
                        "mode": "strict",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = closeout(target, source_root=REPO_ROOT)

    assert result["status"] == "failed"
    failing = {
        check["gate_id"]
        for check in result["checks"]
        if check["required"] and check["status"] == "fail"
    }
    assert "closeout.pending_tracking" in failing
    assert "closeout.strict_verify" in failing
    assert "closeout.handoff.implementation_evidence" not in failing
    assert "closeout.handoff.verification_evidence" not in failing
    assert result["populate"]["enabled"] is False
    assert result["pending_tracking"]["classification"] == "required_only"
    assert result["pending_tracking"]["required_unresolved"] is True
    assert json.loads(pending_path.read_text(encoding="utf-8"))["events"][0]["id"] == "pending-pop"


def test_handoff_repair_fixes_placeholder_handoff_before_closeout(tmp_path: Path) -> None:
    target = tmp_path / "handoff-repair-repo"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"
    simulate_claude_reload(target)

    kickoff(
        target,
        task_id="42",
        slug="handoff-repair",
        title="Handoff Repair",
        goals=["Repair placeholder handoff before final closeout"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    report_rel = f"{current_work['paths']['reports']}/handoff-repair-evidence.txt"
    (target / report_rel).write_text("handoff repair evidence\n", encoding="utf-8")

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed handoff repair scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=report_rel,
        note="Recorded handoff repair implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    log_work(
        target,
        handler="verify:inspection",
        evidence="cmd`test -f handoff-repair-evidence.txt`",
        note="Verified handoff repair evidence exists",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    handoff_path = target / work_rel / "HANDOFF.md"
    handoff_before = handoff_path.read_text(encoding="utf-8")
    assert "has been kicked off through Aegis" in handoff_before
    assert closeout(target, source_root=REPO_ROOT, dry_run=True)["status"] == "failed"

    dry_run = repair_handoff(target, source_root=REPO_ROOT, dry_run=True)
    assert dry_run["status"] == "planned"
    assert dry_run["dry_run"] is True
    assert dry_run["handoff"]["would_update"] is True
    assert (
        "closeout.handoff.current_state"
        in dry_run["closeout_ready_before"]["failed_required_gates"]
    )
    assert "## Implementation Evidence" in dry_run["preview"]
    assert handoff_path.read_text(encoding="utf-8") == handoff_before
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()

    repaired = repair_handoff(target, source_root=REPO_ROOT)
    assert repaired["status"] == "repaired"
    assert repaired["report_written"] is False
    assert repaired["state_updated"] is False
    assert repaired["handoff"]["updated"] is True
    assert repaired["closeout_ready_after"]["status"] == "passed"
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()

    handoff = handoff_path.read_text(encoding="utf-8")
    semantic_handoff = handoff.split("## Progress Log", 1)[0]
    assert "## Implementation Evidence" in semantic_handoff
    assert "## Verification Evidence" in semantic_handoff
    assert "## Strict Verification Evidence" in semantic_handoff
    assert "Branch: `feat/task-42-handoff-repair`." in semantic_handoff
    assert "'action': 'created_branch'" not in semantic_handoff
    assert report_rel in semantic_handoff
    assert AEGIS_VERIFY_REPORT_REL in semantic_handoff
    assert "## Progress Log" in handoff
    assert "Handoff initialized by Aegis kickoff" in handoff

    closeout_ready = closeout(target, source_root=REPO_ROOT, dry_run=True)
    assert closeout_ready["status"] == "passed"
    assert closeout_ready["report_written"] is False
    assert closeout_ready["state_updated"] is False


def test_strict_verify_fails_when_workflow_template_is_missing(tmp_path: Path) -> None:
    target = tmp_path / "strict-missing-template"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="strict-verify",
        title="Strict Verify",
    )

    (target / ".aegis" / "templates" / "workflow" / "session.md").unlink()

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)

    assert strict_report["mode"] == "strict"
    assert strict_report["status"] == "failed"
    assert any(
        check["gate_id"] == "runtime.workflow_templates" and check["status"] == "fail"
        for check in strict_report["checks"]
    )


def _write_fake_wheel(path: Path, *, omit: str | None = None) -> None:
    members = [
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
        "aegis_foundation-0.1.0.dist-info/entry_points.txt",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for member in members:
            if omit and member.endswith(omit):
                continue
            archive.writestr(member, "x\n")


def _write_fake_sdist(path: Path) -> None:
    members = [
        "aegis_foundation-0.1.0/aegis_foundation/cli.py",
        "aegis_foundation-0.1.0/aegis_mcp/server.py",
        "aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh",
        "aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/posttooluse-tracking.sh",
        "aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/tracking-stop-gate.sh",
        "aegis_foundation-0.1.0/aegis_foundation/assets/scripts/_aegis_installer.py",
        "aegis_foundation-0.1.0/aegis_foundation/assets/scripts/codex-task",
        "aegis_foundation-0.1.0/aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json",
        "aegis_foundation-0.1.0/aegis_foundation/assets/templates/aegis/workflow/session.md",
        "aegis_foundation-0.1.0/aegis_foundation/assets/templates/aegis/workflow/tracker.md",
        "aegis_foundation-0.1.0/pyproject.toml",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as archive:
        for member in members:
            data = b"x\n"
            info = tarfile.TarInfo(member)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_release_certification_inspects_artifacts_and_writes_report(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dist = tmp_path / "dist"
    source.mkdir()
    _write_fake_wheel(dist / "aegis_foundation-0.1.0-py3-none-any.whl")
    _write_fake_sdist(dist / "aegis_foundation-0.1.0.tar.gz")

    report = certify_release_candidate(
        source,
        dist_dir=dist,
        report_file=AEGIS_RELEASE_CERT_REPORT_REL,
        build=False,
        run_smoke=False,
    )

    assert report["status"] == "passed"
    assert report["build"]["status"] == "skipped"
    assert report["smokes"]["clean_cli"]["status"] == "skipped"
    assert report["smokes"]["mcp_server_config"]["status"] == "skipped"
    assert report["smokes"]["mcp_stdio"]["status"] == "covered_by_focused_pytest"
    assert {artifact["kind"] for artifact in report["artifacts"]} == {"wheel", "sdist"}
    assert all(len(artifact["sha256"]) == 64 for artifact in report["artifacts"])
    assert (source / AEGIS_RELEASE_CERT_REPORT_REL).is_file()


def test_release_certification_fails_on_missing_required_artifact_member(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dist = tmp_path / "dist"
    source.mkdir()
    _write_fake_wheel(
        dist / "aegis_foundation-0.1.0-py3-none-any.whl",
        omit="pretooluse-gate.sh",
    )
    _write_fake_sdist(dist / "aegis_foundation-0.1.0.tar.gz")

    report = certify_release_candidate(
        source,
        dist_dir=dist,
        report_file=AEGIS_RELEASE_CERT_REPORT_REL,
        build=False,
        run_smoke=False,
    )

    assert report["status"] == "failed"
    assert any(failure["stage"] == "artifact_inspection" for failure in report["failures"])
    wheel = next(artifact for artifact in report["artifacts"] if artifact["kind"] == "wheel")
    assert (
        "aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh"
        in wheel["missing_required_suffixes"]
    )


def test_release_certification_runs_clean_smoke_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    dist = tmp_path / "dist"
    source.mkdir()
    wheel_path = dist / "aegis_foundation-0.1.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path)
    _write_fake_sdist(dist / "aegis_foundation-0.1.0.tar.gz")
    called: list[str] = []

    def fake_clean_smoke(wheel: Path) -> dict:
        called.append(wheel.name)
        return {
            "status": "passed",
            "steps": [
                {
                    "name": "aegis_verify_strict",
                    "status": "passed",
                }
            ],
        }

    monkeypatch.setattr(aegis_installer, "_certify_clean_cli_smoke", fake_clean_smoke)
    monkeypatch.setattr(
        aegis_installer,
        "_certify_mcp_server_config_smoke",
        lambda wheel: {"status": "passed", "checks": [], "wheel": wheel.name},
    )

    report = certify_release_candidate(
        source,
        dist_dir=dist,
        report_file=AEGIS_RELEASE_CERT_REPORT_REL,
        build=False,
        run_smoke=True,
    )

    assert called == [wheel_path.name]
    assert report["status"] == "passed"
    assert report["smokes"]["clean_cli"]["status"] == "passed"
    assert report["smokes"]["mcp_server_config"]["status"] == "passed"
    assert report["smokes"]["clean_cli"]["steps"][0]["name"] == "aegis_verify_strict"


def test_release_certification_full_clean_smoke_when_enabled(tmp_path: Path) -> None:
    if os.environ.get("AEGIS_RUN_CERTIFICATION_SMOKE") != "1":
        pytest.skip(
            "Set AEGIS_RUN_CERTIFICATION_SMOKE=1 to run the full release certification smoke."
        )
    if shutil.which("uv") is None or shutil.which("uvx") is None:
        pytest.skip("uv and uvx are required for the full release certification smoke.")

    report = certify_release_candidate(
        REPO_ROOT,
        dist_dir=tmp_path / "dist",
        report_file=tmp_path / "certification-report.json",
        build=True,
        run_smoke=True,
    )

    assert report["status"] == "passed"
    assert report["build"]["status"] == "passed"
    assert report["smokes"]["clean_cli"]["status"] == "passed"
    assert report["smokes"]["mcp_server_config"]["status"] == "passed"
    assert any(
        step["name"] == "aegis_verify_strict" and step["status"] == "passed"
        for step in report["smokes"]["clean_cli"]["steps"]
    )


def test_install_merges_existing_claude_entrypoint_without_losing_project_context(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing-claude-project"
    target.mkdir()
    claude = target / "CLAUDE.md"
    claude.write_text("# Existing Claude instructions\n", encoding="utf-8")

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert report["status"] == "applied"
    text = claude.read_text(encoding="utf-8")
    assert aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN in text
    assert aegis_installer.AEGIS_CLAUDE_BLOCK_END in text
    assert_mode_aware_entrypoint(
        managed_entrypoint_content(
            text,
            aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN,
            aegis_installer.AEGIS_CLAUDE_BLOCK_END,
        )
    )
    assert "## Existing Project Instructions" in text
    assert text.split("## Existing Project Instructions\n\n", 1)[1] == (
        "# Existing Claude instructions\n"
    )
    claude_operation = next(
        operation for operation in report["plan"]["operations"] if operation["path"] == "CLAUDE.md"
    )
    assert claude_operation["classification"] == "modify"
    assert claude_operation["safe_to_apply"] is True
    assert (target / AEGIS_MANIFEST_REL).exists()


def test_install_replaces_exact_recorded_markerless_claude_runtime(
    tmp_path: Path,
) -> None:
    target = tmp_path / "legacy-markerless-claude-runtime"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    legacy_runtime = (
        b"# Claude Runtime Entry\n\n"
        b"Before persistent mutation, Claude must be in a READY state.\n"
        b"Run `aegis log --pending-id current` after every mutation.\n"
        b"Run handoff repair and closeout before completion.\n"
    )
    write_managed_baseline(target, "CLAUDE.md", legacy_runtime)
    baseline_manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
        baseline_manifest=baseline_manifest,
    )

    assert report["status"] == "applied"
    text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN in text
    assert aegis_installer.AEGIS_CLAUDE_BLOCK_END in text
    assert_mode_aware_entrypoint(
        managed_entrypoint_content(
            text,
            aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN,
            aegis_installer.AEGIS_CLAUDE_BLOCK_END,
        )
    )
    assert "Before persistent mutation" not in text
    assert "aegis log --pending-id current" not in text
    assert "## Existing Project Instructions" not in text


def test_install_preserves_modified_markerless_claude_runtime_conservatively(
    tmp_path: Path,
) -> None:
    target = tmp_path / "modified-markerless-claude-runtime"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    legacy_runtime = b"# Legacy Aegis Claude runtime\n"
    write_managed_baseline(target, "CLAUDE.md", legacy_runtime)
    customized = legacy_runtime + b"\n# Project rule\nKeep this owner-authored rule.\n"
    (target / "CLAUDE.md").write_bytes(customized)
    baseline_manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
        baseline_manifest=baseline_manifest,
    )

    assert report["status"] == "applied"
    text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "## Existing Project Instructions" in text
    assert text.split("## Existing Project Instructions\n\n", 1)[1].encode("utf-8") == customized


def test_install_merges_existing_codex_entrypoint_without_losing_project_context(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing-codex-project"
    target.mkdir()
    codex = target / "CODEX.md"
    codex.write_text("# Existing Codex instructions\n", encoding="utf-8")

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )

    assert report["status"] == "applied"
    text = codex.read_text(encoding="utf-8")
    assert aegis_installer.AEGIS_CODEX_BLOCK_BEGIN in text
    assert aegis_installer.AEGIS_CODEX_BLOCK_END in text
    assert_mode_aware_entrypoint(
        managed_entrypoint_content(
            text,
            aegis_installer.AEGIS_CODEX_BLOCK_BEGIN,
            aegis_installer.AEGIS_CODEX_BLOCK_END,
        )
    )
    assert "## Existing Codex Instructions" in text
    assert text.split("## Existing Codex Instructions\n\n", 1)[1] == (
        "# Existing Codex instructions\n"
    )
    codex_operation = next(
        operation for operation in report["plan"]["operations"] if operation["path"] == "CODEX.md"
    )
    assert codex_operation["classification"] == "modify"
    assert codex_operation["safe_to_apply"] is True
    assert (target / AEGIS_MANIFEST_REL).exists()


def test_install_merges_existing_agents_entrypoint_without_losing_project_context(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing-agents-project"
    target.mkdir()
    agents = target / "AGENTS.md"
    agents.write_text("# Existing agent instructions\n", encoding="utf-8")

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )

    assert report["status"] == "applied"
    text = agents.read_text(encoding="utf-8")
    assert aegis_installer.AEGIS_AGENTS_BLOCK_BEGIN in text
    assert aegis_installer.AEGIS_AGENTS_BLOCK_END in text
    assert_mode_aware_entrypoint(
        managed_entrypoint_content(
            text,
            aegis_installer.AEGIS_AGENTS_BLOCK_BEGIN,
            aegis_installer.AEGIS_AGENTS_BLOCK_END,
        )
    )
    assert "## Existing Agent Instructions" in text
    assert text.split("## Existing Agent Instructions\n\n", 1)[1] == (
        "# Existing agent instructions\n"
    )
    agents_operation = next(
        operation for operation in report["plan"]["operations"] if operation["path"] == "AGENTS.md"
    )
    assert agents_operation["classification"] == "modify"
    assert agents_operation["safe_to_apply"] is True
    assert (target / AEGIS_MANIFEST_REL).exists()


@pytest.mark.parametrize(
    ("primary_agent", "agents", "expected_entrypoints"),
    [
        ("claude", ["claude"], ("CLAUDE.md", "AGENTS.md")),
        ("codex", ["codex"], ("CODEX.md", "AGENTS.md")),
        ("multi", ["claude", "codex"], ("CLAUDE.md", "CODEX.md", "AGENTS.md")),
    ],
)
def test_fresh_install_renders_bounded_mode_aware_agent_entrypoints(
    tmp_path: Path,
    primary_agent: str,
    agents: list[str],
    expected_entrypoints: tuple[str, ...],
) -> None:
    target = tmp_path / f"fresh-{primary_agent}"
    target.mkdir()

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
        apply=True,
    )

    assert report["status"] == "applied"
    markers = {
        "CLAUDE.md": (
            aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN,
            aegis_installer.AEGIS_CLAUDE_BLOCK_END,
        ),
        "CODEX.md": (
            aegis_installer.AEGIS_CODEX_BLOCK_BEGIN,
            aegis_installer.AEGIS_CODEX_BLOCK_END,
        ),
        "AGENTS.md": (
            aegis_installer.AEGIS_AGENTS_BLOCK_BEGIN,
            aegis_installer.AEGIS_AGENTS_BLOCK_END,
        ),
    }
    for rel_path in expected_entrypoints:
        text = (target / rel_path).read_text(encoding="utf-8")
        begin_marker, end_marker = markers[rel_path]
        assert begin_marker in text
        assert end_marker in text
        assert_mode_aware_entrypoint(managed_entrypoint_content(text, begin_marker, end_marker))

    second_plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent=primary_agent,
        agents=agents,
    )
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}


def test_repeat_multi_agent_install_refreshes_only_managed_blocks(
    tmp_path: Path,
) -> None:
    target = tmp_path / "repeat-multi-agent"
    target.mkdir()
    project_content = {
        "CLAUDE.md": "# Project Claude\n\nClaude-owned rule.\n",
        "CODEX.md": "# Project Codex\n\nCodex-owned rule.\n",
        "AGENTS.md": "# Project Agents\n\nShared project rule.\n",
    }
    headings = {
        "CLAUDE.md": "Existing Project Instructions",
        "CODEX.md": "Existing Codex Instructions",
        "AGENTS.md": "Existing Agent Instructions",
    }
    markers = {
        "CLAUDE.md": (
            aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN,
            aegis_installer.AEGIS_CLAUDE_BLOCK_END,
        ),
        "CODEX.md": (
            aegis_installer.AEGIS_CODEX_BLOCK_BEGIN,
            aegis_installer.AEGIS_CODEX_BLOCK_END,
        ),
        "AGENTS.md": (
            aegis_installer.AEGIS_AGENTS_BLOCK_BEGIN,
            aegis_installer.AEGIS_AGENTS_BLOCK_END,
        ),
    }
    for rel_path, content in project_content.items():
        (target / rel_path).write_text(content, encoding="utf-8")

    first = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
        apply=True,
    )
    assert first["status"] == "applied"

    expected_project_content: dict[str, str] = {}
    for rel_path, initial_content in project_content.items():
        local_content = f"{initial_content}Local post-install rule for {rel_path}.\n"
        expected_project_content[rel_path] = local_content
        path = target / rel_path
        text = path.read_text(encoding="utf-8")
        heading = headings[rel_path]
        prefix = text.split(f"## {heading}\n\n", 1)[0]
        text = f"{prefix}## {heading}\n\n{local_content}"
        begin_marker, end_marker = markers[rel_path]
        path.write_text(
            replace_managed_entrypoint_content(
                text,
                begin_marker,
                end_marker,
                "# Legacy strict ceremony\n\nRun `aegis log --pending-id current` after every mutation.",
            ),
            encoding="utf-8",
        )

    second = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
        apply=True,
    )
    assert second["status"] == "applied"

    installed_bytes: dict[str, bytes] = {}
    for rel_path, expected_content in expected_project_content.items():
        path = target / rel_path
        text = path.read_text(encoding="utf-8")
        begin_marker, end_marker = markers[rel_path]
        managed = managed_entrypoint_content(text, begin_marker, end_marker)
        assert_mode_aware_entrypoint(managed)
        assert "Legacy strict ceremony" not in text
        assert text.split(f"## {headings[rel_path]}\n\n", 1)[1] == expected_content
        installed_bytes[rel_path] = path.read_bytes()

    third = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="multi",
        agents=["claude", "codex"],
        apply=True,
    )
    assert third["status"] == "applied"
    for rel_path, expected_bytes in installed_bytes.items():
        assert (target / rel_path).read_bytes() == expected_bytes


def test_verify_fails_when_required_claude_gate_file_is_missing(tmp_path: Path) -> None:
    target = tmp_path / "missing-hook"
    target.mkdir()
    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"

    (target / ".claude" / "scripts" / "readiness.sh").unlink()

    verification = verify(target, source_root=REPO_ROOT)
    assert verification["status"] == "failed"
    assert any(
        check["gate_id"] == "claude.readiness" and check["status"] == "fail"
        for check in verification["checks"]
    )


def test_agent_selection_is_explicit_and_consistent(tmp_path: Path) -> None:
    with pytest.raises(AegisError, match="at least one explicit --agent"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="claude", agents=[])

    with pytest.raises(AegisError, match="must also be listed"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="codex", agents=["claude"])

    with pytest.raises(AegisError, match="requires at least two"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="multi", agents=["claude"])

    with pytest.raises(AegisError, match="cannot be combined"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="none", agents=["claude"])


def test_inspect_reports_installed_aegis_state(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    target.mkdir()
    before = inspect_project(target)
    assert before["aegis"]["installed"] is False
    assert before["detected_agents"]["claude"] is False
    assert before["workflow_guidance"]["phase"] == "bootstrap"
    assert before["workflow_guidance"]["state"] == "not_installed"
    assert before["workflow_guidance"]["suggested_mcp_call"]["tool"] == "aegis.init"
    assert before["workflow_guidance"]["details"]["must_initialize_before_source_edits"] is True
    assert "source edits" in before["workflow_guidance"]["details"]["forbidden_until_init"]
    assert "Taskmaster mutations" in before["workflow_guidance"]["details"]["forbidden_until_init"]

    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    after = inspect_project(target)

    assert after["aegis"]["installed"] is True
    assert after["aegis"]["primary_agent"] == "claude"
    assert after["detected_agents"]["claude"] is True
    assert after["workflow_guidance"]["state"] == "client_reload_required"


def test_aegis_cli_smoke_installs_and_verifies_generic_claude_profile(tmp_path: Path) -> None:
    target = tmp_path / "cli-repo"
    target.mkdir()

    plan_result = run_cli(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            str(target),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )
    assert plan_result.returncode == 0, plan_result.stderr
    plan = json.loads(plan_result.stdout)
    assert plan["mode"] == "dry_run"
    assert plan["summary"]["creates"] > 0

    install_result = run_cli(
        [
            "aegis",
            "install",
            "--target-dir",
            str(target),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
            "--apply",
        ]
    )
    assert install_result.returncode == 0, install_result.stderr
    install_report = json.loads(install_result.stdout)
    assert install_report["status"] == "applied"

    verify_result = run_cli(["aegis", "verify", "--target-dir", str(target)])
    assert verify_result.returncode == 0, verify_result.stderr
    verify_report = json.loads(verify_result.stdout)
    assert verify_report["status"] == "passed"

    second_plan_result = run_cli(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            str(target),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )
    assert second_plan_result.returncode == 0, second_plan_result.stderr
    second_plan = json.loads(second_plan_result.stdout)
    assert second_plan["summary"]["creates"] == 0
    assert second_plan["summary"]["manual_reviews"] == 0
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}

    stale_rel = ".claude/scripts/brief_lib.py"
    write_managed_baseline(target, stale_rel, b"# stale installed managed asset\n")

    update_preview_result = run_cli(["aegis", "update", "--target-dir", str(target)])
    assert update_preview_result.returncode == 0, update_preview_result.stderr
    update_preview = json.loads(update_preview_result.stdout)
    preview_operations = {
        operation["path"]: operation
        for operation in update_preview["install"]["plan"]["operations"]
    }
    assert update_preview["status"] == "preview"
    assert preview_operations[stale_rel]["classification"] == "modify"
    assert (target / stale_rel).read_text(encoding="utf-8") == "# stale installed managed asset\n"

    update_apply_result = run_cli(["aegis", "update", "--target-dir", str(target), "--apply"])
    assert update_apply_result.returncode == 0, update_apply_result.stderr
    update_report = json.loads(update_apply_result.stdout)
    assert update_report["status"] == "applied"
    assert (target / stale_rel).read_text(encoding="utf-8") == (REPO_ROOT / stale_rel).read_text(
        encoding="utf-8"
    )
    assert (target / AEGIS_UPDATE_REPORT_REL).is_file()
    assert (target / ".aegis" / "capsule" / "current.json").is_file()

    (target / stale_rel).write_text("# locally diverged managed asset\n", encoding="utf-8")
    refused_result = run_cli(["aegis", "update", "--target-dir", str(target)])
    assert refused_result.returncode == 1
    refused_report = json.loads(refused_result.stdout)
    refused_operations = {
        operation["path"]: operation
        for operation in refused_report["install"]["plan"]["operations"]
    }
    assert refused_report["status"] == "refused"
    assert refused_operations[stale_rel]["classification"] == "manual-review"
    assert (target / stale_rel).read_text(encoding="utf-8") == (
        "# locally diverged managed asset\n"
    )


def test_observation_report_stays_under_size_budget_with_huge_runtime_dir(tmp_path: Path) -> None:
    """TM #197: a large runtime directory must not balloon the guidance payload.

    Reproduces the 8MB observation-report class: thousands of ignored .wrangler KV
    blob paths. The committed report must stay <100KB via capped sample + counts by
    prefix, while the full enumeration remains available in the linked detail artifact.
    """

    target = tmp_path / "observe-huge-runtime"
    init_git_repo(target)
    # A tracked, git-ignored runtime dir so the blobs show up as !!-ignored deltas
    # (the allowed-runtime class), exactly like worker/.wrangler in the field.
    (target / ".gitignore").write_text("worker/.wrangler/\n", encoding="utf-8")
    git(target, "add", ".gitignore")
    git(target, "commit", "-m", "ignore wrangler state")

    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Huge runtime audit", source_root=REPO_ROOT)

    blob_root = target / "worker" / ".wrangler" / "state" / "v3" / "kv" / "blobs"
    blob_root.mkdir(parents=True, exist_ok=True)
    for index in range(4000):
        (blob_root / f"blob-{index:05d}.bin").write_text("x", encoding="utf-8")

    completed = stop_observation(
        target,
        summary="Huge runtime dir observed",
        source_root=REPO_ROOT,
        collect_artifacts=True,
    )
    assert completed["status"] == "completed"

    report_path = target / AEGIS_OBSERVATION_REPORT_REL
    report_size = report_path.stat().st_size
    assert report_size < 100 * 1024, f"observation report is {report_size} bytes (budget 100KB)"

    current_work_size = (target / AEGIS_CURRENT_WORK_REL).stat().st_size
    assert current_work_size < 100 * 1024, f"current-work.json is {current_work_size} bytes"

    summary = completed["allowed_runtime_changes_summary"]
    assert summary["total"] >= 4000, "the count is preserved even though the list is capped"
    assert len(summary["sample"]) <= 50, "sample is capped"
    assert summary["truncated"] is True
    assert summary["by_prefix"], "counts by path prefix are reported"

    # Nothing is silently dropped: the full enumeration lives in the detail artifact.
    detail = json.loads((target / completed["detail_ref"]).read_text(encoding="utf-8"))
    assert len(detail["allowed_runtime_changes"]) >= 4000
