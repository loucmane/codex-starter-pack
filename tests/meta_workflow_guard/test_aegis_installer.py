"""Tests for the Aegis Foundation installer CLI/core prototype."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import (
    AEGIS_MANIFEST_REL,
    AEGIS_CLOSEOUT_REPORT_REL,
    AEGIS_PENDING_TRACKING_REL,
    AEGIS_RELEASE_CERT_REPORT_REL,
    AEGIS_VERIFY_REPORT_REL,
    AegisError,
    certify_release_candidate,
    closeout,
    install,
    inspect_project,
    kickoff,
    log_work,
    next_action,
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

    verify_args = parser.parse_args(["aegis", "verify", "--target-dir", "/tmp/example", "--strict"])
    assert verify_args.subcommand == "verify"
    assert verify_args.strict is True

    next_args = parser.parse_args(["aegis", "next", "--target-dir", "/tmp/example"])
    assert next_args.subcommand == "next"
    assert next_args.target_dir == "/tmp/example"

    closeout_args = parser.parse_args([
        "aegis",
        "closeout",
        "--target-dir",
        "/tmp/example",
        "--update-handoff",
        "--dry-run",
    ])
    assert closeout_args.subcommand == "closeout"
    assert closeout_args.update_handoff is True
    assert closeout_args.dry_run is True

    certify_args = parser.parse_args([
        "aegis",
        "certify-release",
        "--source-dir",
        "/tmp/source",
        "--dist-dir",
        "/tmp/dist",
        "--skip-build",
        "--skip-smoke",
    ])
    assert certify_args.subcommand == "certify-release"
    assert certify_args.skip_build is True
    assert certify_args.skip_smoke is True

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
    assert log_args.plan_step == ""

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


def test_next_action_guides_not_installed_and_installed_states(tmp_path: Path) -> None:
    target = tmp_path / "guided-repo"
    target.mkdir()

    initial = next_action(target, source_root=REPO_ROOT)
    assert initial["read_only"] is True
    assert initial["phase"] == "bootstrap"
    assert initial["state"] == "not_installed"
    assert initial["suggested_mcp_call"]["tool"] == "aegis.plan_install"

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    installed = next_action(target, source_root=REPO_ROOT)
    assert installed["phase"] == "start"
    assert installed["state"] == "installed_no_current_work"
    assert installed["suggested_mcp_call"]["tool"] == "aegis.kickoff"


def test_next_action_guides_active_workflow_states(tmp_path: Path) -> None:
    target = tmp_path / "guided-workflow"
    target.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="guided-task",
        title="Guided Task",
        goals=["Exercise next action guidance"],
    )
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))

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

    pending_payload = {"tool_name": "Write", "tool_input": {"file_path": f"{current_work['paths']['reports']}/evidence.txt"}}
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
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    kickoff(
        target,
        task_id="42",
        slug="auto-step",
        title="Auto Step",
        goals=["Exercise deterministic plan step inference"],
    )
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))

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


def test_log_work_plan_step_auto_rejects_ambiguous_inference(tmp_path: Path) -> None:
    target = tmp_path / "ambiguous-auto-plan-step"
    target.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    kickoff(
        target,
        task_id="42",
        slug="ambiguous-auto",
        title="Ambiguous Auto",
        goals=["Exercise ambiguous plan step inference"],
    )
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))

    with pytest.raises(AegisError, match="plan-step auto is ambiguous"):
        log_work(
            target,
            handler="claude:scope-write",
            evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
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
    pending_payload = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    pending_event = pending_payload["events"][0]
    assert pending_event["evidence_location"]["path"] == evidence_path
    assert pending_event["evidence_location"]["display"] == f"{evidence_path}:1"
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
        plan_step="plan-step-implement",
        plan_status="in-progress",
    )
    assert logged["status"] == "logged"
    assert logged["pending"]["cleared"] == 1
    assert logged["entry"]["evidence_location"]["display"] == f"{evidence_path}:1"
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
    started = kickoff(target, task_id="42", slug="surface-defaults", title="Surface Defaults")
    assert started["next_action"]["action"] == "log_scope_before_edit"
    assert started["next_action"]["suggested_mcp"]["tool"] == "aegis.log"
    assert started["next_action"]["suggested_mcp"]["arguments"]["plan_step"] == "auto"
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
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
    kickoff(target, task_id="42", slug="pending-id", title="Pending Id")
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
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
    kickoff(target, task_id="42", slug="mcp-read-only", title="MCP Read Only")

    for tool_name in (
        "mcp__aegis__aegis_inspect",
        "mcp__aegis__aegis_status",
        "mcp__aegis__aegis_next",
        "mcp__aegis__aegis_plan_install",
        "mcp__aegis__aegis_closeout_ready",
        "mcp__aegis__aegis_list_profiles",
        "mcp__aegis__aegis_explain_profile",
    ):
        payload = {"tool_name": tool_name, "tool_input": {"target_dir": target.as_posix()}}
        pretool = run_target_pretooluse(target, payload)
        assert pretool.returncode == 0, pretool.stderr
        posttool = run_target_posttooluse(target, payload)
        assert posttool.returncode == 0, posttool.stderr
        assert not (target / AEGIS_PENDING_TRACKING_REL).exists(), tool_name


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
    kickoff(target, task_id="42", slug="repair-guidance", title="Repair Guidance")
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
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

    failed = closeout(target, source_root=REPO_ROOT, update_handoff=True)

    assert failed["status"] == "failed"
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
    assert strict_report["next_action"]["suggested_mcp"]["arguments"]["pending_event_id"] == "current"


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

    kickoff(
        target,
        task_id="42",
        slug="closeout-gate",
        title="Closeout Gate",
        goals=["Prove closeout validates semantic workflow completion"],
    )
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
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
    handoff_before_dry_run = (target / work_rel / "HANDOFF.md").read_text(encoding="utf-8")
    dry_failed = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert dry_failed["status"] == "failed"
    assert dry_failed["dry_run"] is True
    assert dry_failed["report_written"] is False
    assert dry_failed["state_updated"] is False
    assert dry_failed["handoff"]["updated"] is False
    assert dry_failed["handoff"]["would_update"] is True
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()
    assert (target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8") == manifest_before_dry_run
    assert (target / work_rel / "HANDOFF.md").read_text(encoding="utf-8") == handoff_before_dry_run

    failed = closeout(target, source_root=REPO_ROOT)
    assert failed["status"] == "failed"
    assert failed["next_action"]["action"] == "repair_closeout_gates_before_retry"
    assert "closeout.handoff.current_state" in failed["next_action"]["details"]["failed_required_gates"]
    assert any(
        check["gate_id"] == "closeout.handoff.current_state" and check["status"] == "fail"
        for check in failed["checks"]
    )

    passed = closeout(target, source_root=REPO_ROOT, update_handoff=True)
    assert passed["status"] == "passed"
    assert passed["next_action"]["action"] == "task_complete"
    assert passed["summary"]["failed_required"] == 0
    assert passed["git"]["legacy_manual_only"] == ["gac"]
    assert "git commit -m \"<type(scope): summary>\"" in passed["git"]["guidance"]
    assert (target / AEGIS_CLOSEOUT_REPORT_REL).is_file()
    refreshed_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
    assert refreshed_work["status"] == "in-progress"
    assert refreshed_work["closeout_report"] == AEGIS_CLOSEOUT_REPORT_REL
    handoff = (target / work_rel / "HANDOFF.md").read_text(encoding="utf-8")
    assert AEGIS_CLOSEOUT_REPORT_REL in handoff
    assert AEGIS_VERIFY_REPORT_REL in handoff
    assert report_rel in handoff


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
    assert "aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh" in wheel["missing_required_suffixes"]


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
        pytest.skip("Set AEGIS_RUN_CERTIFICATION_SMOKE=1 to run the full release certification smoke.")
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
