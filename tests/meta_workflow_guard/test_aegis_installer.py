"""Tests for the Aegis Foundation installer CLI/core prototype."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts._aegis_installer import (
    AEGIS_MANIFEST_REL,
    AEGIS_PENDING_TRACKING_REL,
    AegisError,
    install,
    inspect_project,
    kickoff,
    log_work,
    plan_install,
    verify,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schemas" / "aegis"


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
        ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--quick", "--root", str(target)],
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


def test_build_parser_accepts_aegis_commands() -> None:
    module = load_task_module()
    parser = module.build_parser()

    inspect_args = parser.parse_args(["aegis", "inspect", "--target-dir", "/tmp/example"])
    assert inspect_args.command == "aegis"
    assert inspect_args.subcommand == "inspect"
    assert inspect_args.target_dir == "/tmp/example"

    plan_args = parser.parse_args([
        "aegis",
        "plan-install",
        "--target-dir",
        "/tmp/example",
        "--primary-agent",
        "claude",
        "--agent",
        "claude",
    ])
    assert plan_args.primary_agent == "claude"
    assert plan_args.agent == ["claude"]

    install_args = parser.parse_args([
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
    ])
    assert install_args.apply is True
    assert install_args.agent == ["claude", "codex"]

    verify_args = parser.parse_args(["aegis", "verify", "--target-dir", "/tmp/example"])
    assert verify_args.subcommand == "verify"

    kickoff_args = parser.parse_args([
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
    ])
    assert kickoff_args.subcommand == "kickoff"
    assert kickoff_args.task == "1"

    log_args = parser.parse_args([
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
    ])
    assert log_args.subcommand == "log"
    assert log_args.handler == "claude-test"

    profile_args = parser.parse_args(["aegis", "explain-profile"])
    assert profile_args.profile == "generic"


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
    assert "Claude readiness is BLOCKED" in blocked_verify.stderr

    bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": 'aegis kickoff --task 1 --slug portable-smoke --title "Portable Smoke"'
            },
        },
    )
    assert bootstrap.returncode == 0, bootstrap.stderr

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
    assert "Aegis current work Task 1 is in-progress" in subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--root", str(target)],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    ).stdout

    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
    assert current_work["task"]["id"] == "1"
    assert current_work["integrations"]["taskmaster"] == {"detected": False, "required": False}
    assert current_work["integrations"]["serena"] == {"detected": False, "required": False}
    assert (target / "sessions" / "current").is_symlink()
    assert (target / "plans" / "current").is_symlink()
    assert (target / ".aegis" / "bin" / "aegis").is_file()
    assert os.access(target / ".aegis" / "bin" / "aegis", os.X_OK)
    assert (target / current_work["paths"]["work_tracking"] / "TRACKER.md").is_file()

    allowed = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{current_work['paths']['reports']}/allowed-evidence.txt"
            },
        },
    )
    assert allowed.returncode == 0, allowed.stderr

    evidence_path = f"{current_work['paths']['reports']}/allowed-evidence.txt"
    (target / evidence_path).write_text("allowed evidence\n", encoding="utf-8")
    tracked = run_target_posttooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": evidence_path}},
    )
    assert tracked.returncode == 0, tracked.stderr
    pending_next = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": f"{current_work['paths']['reports']}/blocked-before-log.txt"},
        },
    )
    assert pending_next.returncode == 2
    assert "pending S:W:H:E tracking must be logged" in pending_next.stderr

    with pytest.raises(AegisError, match="does not match any pending S:W:H:E tracking event"):
        log_work(
            target,
            handler="claude-installer-test",
            evidence=f"{current_work['paths']['reports']}/wrong-evidence.txt",
            note="Tried to log the wrong evidence",
        )
    assert (target / AEGIS_PENDING_TRACKING_REL).is_file()

    logged = log_work(
        target,
        handler="claude-installer-test",
        evidence=evidence_path,
        note="Recorded installer test evidence",
    )
    assert logged["status"] == "logged"
    assert logged["pending"]["cleared"] == 1
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(encoding="utf-8")
    plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
    implementation_text = (target / current_work["paths"]["work_tracking"] / "IMPLEMENTATION.md").read_text(encoding="utf-8")
    changelog_text = (target / current_work["paths"]["work_tracking"] / "CHANGELOG.md").read_text(encoding="utf-8")
    handoff_text = (target / current_work["paths"]["work_tracking"] / "HANDOFF.md").read_text(encoding="utf-8")
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in session_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in tracker_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in implementation_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in changelog_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in handoff_text
    assert "| plan-step-implement | Make only task-scoped changes and record implementation notes |" in plan_text
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
    }

    verify_loop_payload = {
        "tool_name": "Bash",
        "tool_input": {
            "command": (
                f"EV={evidence_path}; "
                'for f in sessions/current plans/current; do grep -q "$EV" "$f" 2>/dev/null; done'
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


def test_install_refuses_existing_file_conflict_without_overwrite(tmp_path: Path) -> None:
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

    assert report["status"] == "refused"
    assert claude.read_text(encoding="utf-8") == "# Existing Claude instructions\n"
    assert any(operation["path"] == "CLAUDE.md" for operation in report["unsafe_operations"])
    assert not (target / AEGIS_MANIFEST_REL).exists()


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

    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    after = inspect_project(target)

    assert after["aegis"]["installed"] is True
    assert after["aegis"]["primary_agent"] == "claude"
    assert after["detected_agents"]["claude"] is True


def test_aegis_cli_smoke_installs_and_verifies_generic_claude_profile(tmp_path: Path) -> None:
    target = tmp_path / "cli-repo"
    target.mkdir()

    plan_result = run_cli([
        "aegis",
        "plan-install",
        "--target-dir",
        str(target),
        "--primary-agent",
        "claude",
        "--agent",
        "claude",
    ])
    assert plan_result.returncode == 0, plan_result.stderr
    plan = json.loads(plan_result.stdout)
    assert plan["mode"] == "dry_run"
    assert plan["summary"]["creates"] > 0

    install_result = run_cli([
        "aegis",
        "install",
        "--target-dir",
        str(target),
        "--primary-agent",
        "claude",
        "--agent",
        "claude",
        "--apply",
    ])
    assert install_result.returncode == 0, install_result.stderr
    install_report = json.loads(install_result.stdout)
    assert install_report["status"] == "applied"

    verify_result = run_cli(["aegis", "verify", "--target-dir", str(target)])
    assert verify_result.returncode == 0, verify_result.stderr
    verify_report = json.loads(verify_result.stdout)
    assert verify_report["status"] == "passed"

    second_plan_result = run_cli([
        "aegis",
        "plan-install",
        "--target-dir",
        str(target),
        "--primary-agent",
        "claude",
        "--agent",
        "claude",
    ])
    assert second_plan_result.returncode == 0, second_plan_result.stderr
    second_plan = json.loads(second_plan_result.stdout)
    assert second_plan["summary"]["creates"] == 0
    assert second_plan["summary"]["manual_reviews"] == 0
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}
