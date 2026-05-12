"""Unit tests for codex-task wizard helpers."""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

from tests.meta_workflow_guard.cross_project_fixtures import REPO_SHAPES


def load_task_module():
    name = "codex_task_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/codex-task")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


class FakeCompletedProcess:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        base = cls(2026, 4, 24, 15, 3, 13)
        if tz is None:
            return base
        return base.replace(tzinfo=tz)


def test_build_parser_accepts_wizard_kickoff() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["wizard", "kickoff", "--task", "96", "--slug", "interactive-template-wizard"])
    assert args.command == "wizard"
    assert args.subcommand == "kickoff"
    assert args.task == "96"


def test_build_parser_accepts_sessions_continue() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "sessions",
        "continue",
        "--task",
        "42",
        "--slug",
        "session-management-system",
        "--plan",
        "plans/2026-05-08-task42-session-management-system.md",
    ])
    assert args.command == "sessions"
    assert args.subcommand == "continue"
    assert args.task == "42"
    assert args.slug == "session-management-system"


def test_build_parser_accepts_serena_status() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["serena", "status", "--strict", "--report-file", "reports/serena/status.txt"])
    assert args.command == "serena"
    assert args.subcommand == "status"
    assert args.strict is True
    assert args.report_file == "reports/serena/status.txt"


def test_build_parser_accepts_telemetry_report_kind() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["report", "generate", "--kind", "telemetry"])
    assert args.command == "report"
    assert args.subcommand == "generate"
    assert args.kind == "telemetry"


def test_handle_wizard_kickoff_creates_artifacts(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    sessions_dir = repo / "sessions"
    plans_dir = repo / "plans"
    active_dir = repo / "docs" / "ai" / "work-tracking" / "active"
    task_dir = repo / ".taskmaster" / "tasks"
    sessions_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)
    active_dir.mkdir(parents=True)
    task_dir.mkdir(parents=True)

    task_file = task_dir / "task_096.txt"
    task_file.write_text(
        "# Task ID: 96\n# Title: Build Interactive Template Wizard\n# Description: Create a wizard CLI.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(module, "WORK_TRACKING_BASE", active_dir)
    monkeypatch.setattr(module, "PLAN_CURRENT", plans_dir / "current")
    monkeypatch.setattr(module, "PLAN_STATE_DIR", repo / ".plan_state")
    monkeypatch.setattr(module, "PLAN_SYNC_LOG", repo / ".plan_state" / "sync.log")
    monkeypatch.setattr(module, "SESSION_STATE_PATH", sessions_dir / "state.json")
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    commands = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False):
        commands.append(cmd)
        if cmd[:3] == ["git", "branch", "--show-current"]:
            return FakeCompletedProcess(stdout="feat/task-96-interactive-template-wizard\n")
        if cmd[:2] == ["git", "status"]:
            return FakeCompletedProcess(stdout="")
        if cmd[:2] == ["task-master", "generate"]:
            output_dir = Path(cmd[cmd.index("--output") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "task_096.md").write_text(
                "# Task ID: 96\n\n**Title:** Build Interactive Template Wizard\n\n**Status:** in-progress\n",
                encoding="utf-8",
            )
            return FakeCompletedProcess(stdout="")
        if cmd[0] == "task-master":
            return FakeCompletedProcess(stdout="")
        return FakeCompletedProcess(stdout="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    args = argparse.Namespace(
        task="96",
        slug="interactive-template-wizard",
        title="Interactive Template Wizard",
        goal=None,
        task_source="Test kickoff",
        handler_target=None,
        force=False,
        dry_run=False,
    )

    module.handle_wizard_kickoff(args)

    active_folder = active_dir / "20260424-task96-interactive-template-wizard-ACTIVE"
    session_path = sessions_dir / "2026" / "04" / "2026-04-24-001-task96-interactive-template-wizard.md"
    plan_path = plans_dir / "2026-04-24-task96-interactive-template-wizard.md"

    assert active_folder.exists()
    assert session_path.exists()
    assert plan_path.exists()
    assert (sessions_dir / "current").resolve() == session_path
    assert (plans_dir / "current").resolve() == plan_path
    assert (repo / ".plan_state" / "sync.log").exists()

    state = json.loads((sessions_dir / "state.json").read_text(encoding="utf-8"))
    assert state["current"] == session_path.name
    assert state["paused"] == []

    tracker_text = (active_folder / "TRACKER.md").read_text(encoding="utf-8")
    assert "Define the scope and workflow boundary for Interactive Template Wizard" in tracker_text
    assert "[S:20260424|W:task96-interactive-template-wizard|H:task-master:set-status|E:.taskmaster/tasks/tasks.json]" in tracker_text
    session_text = session_path.read_text(encoding="utf-8")
    assert "[S:20260424|W:task96-interactive-template-wizard|H:shell:date|" in session_text
    assert "Marked Taskmaster Task 96 in progress" in session_text
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "scripts/codex-task" in plan_text

    assert ["task-master", "set-status", "--id=96", "--status=in-progress"] in commands
    assert ["task-master", "generate"] not in commands
    assert any(cmd[:2] == ["task-master", "generate"] and "--output" in cmd for cmd in commands)


def test_handle_sessions_continue_reuses_active_work_tracking_and_plan(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    sessions_dir = repo / "sessions"
    plans_dir = repo / "plans"
    active_dir = repo / "docs" / "ai" / "work-tracking" / "active"
    task_dir = repo / ".taskmaster" / "tasks"
    plan_state_dir = repo / ".plan_state"
    sessions_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)
    active_dir.mkdir(parents=True)
    task_dir.mkdir(parents=True)

    task_file = task_dir / "task_042.txt"
    task_file.write_text(
        "# Task ID: 42\n# Title: Implement Session Management System\n# Description: Create robust session tracking.\n",
        encoding="utf-8",
    )
    old_session = sessions_dir / "2026" / "04" / "2026-04-24-001-task42-session-management-system.md"
    old_session.parent.mkdir(parents=True)
    old_session.write_text("---\nsession_id: 2026-04-24-001\n---\n", encoding="utf-8")
    (sessions_dir / "current").symlink_to(Path("2026/04/2026-04-24-001-task42-session-management-system.md"))
    (sessions_dir / "state.json").write_text(
        '{"current":"2026-04-24-001-task42-session-management-system.md","paused":[],"updated_at":"2026-04-24T10:00:00+02:00"}\n',
        encoding="utf-8",
    )

    plan_file = plans_dir / "2026-04-24-task42-session-management-system.md"
    plan_file.write_text(
        "\n".join(
            [
                "# Plan",
                "",
                "| Step ID | Description | Evidence | Status |",
                "| --- | --- | --- | --- |",
                "| plan-step-scope | Scope | evidence | completed |",
                "| plan-step-implement | Implement | evidence | pending |",
                "| plan-step-verify | Verify | evidence | pending |",
                "| plan-step-emergency | Optional | evidence | n/a |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (plans_dir / "current").symlink_to(Path("2026-04-24-task42-session-management-system.md"))

    active_folder = active_dir / "20260424-task42-session-management-system-ACTIVE"
    active_folder.mkdir()
    tracker = active_folder / "TRACKER.md"
    tracker.write_text(
        "\n".join(
            [
                "# Tracker",
                "",
                "## Progress Log",
                "",
                "## Plan Compliance Checklist",
                "- [x] plan-step-scope",
                "- [ ] plan-step-implement",
                "- [ ] plan-step-verify",
                "- [ ] plan-step-emergency",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(module, "PLANS_DIR", plans_dir)
    monkeypatch.setattr(module, "WORK_TRACKING_BASE", active_dir)
    monkeypatch.setattr(module, "WORK_TRACKING_ACTIVE_REL", "docs/ai/work-tracking/active")
    monkeypatch.setattr(module, "PLAN_CURRENT", plans_dir / "current")
    monkeypatch.setattr(module, "PLAN_STATE_DIR", plan_state_dir)
    monkeypatch.setattr(module, "PLAN_SYNC_LOG", plan_state_dir / "sync.log")
    monkeypatch.setattr(module, "SESSION_STATE_PATH", sessions_dir / "state.json")
    monkeypatch.setattr(module, "TASKMASTER_TASKS_DIR", task_dir)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False):
        if cmd[:3] == ["git", "branch", "--show-current"]:
            return FakeCompletedProcess(stdout="feat/task-42-session-management-system\n")
        return FakeCompletedProcess(stdout="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module.handle_sessions_continue(
        argparse.Namespace(
            task="42",
            slug="session-management-system",
            title="Implement Session Management System",
            work=None,
            folder=None,
            plan=None,
            task_source="Test continuation",
            dry_run=False,
        )
    )

    new_session = sessions_dir / "2026" / "04" / "2026-04-24-002-task42-session-management-system.md"
    assert new_session.exists()
    assert (sessions_dir / "current").resolve() == new_session
    assert (plans_dir / "current").resolve() == plan_file
    assert list(active_dir.iterdir()) == [active_folder]
    state = json.loads((sessions_dir / "state.json").read_text(encoding="utf-8"))
    assert state["current"] == new_session.name
    assert state["paused"] == []
    assert "sessions continue" in new_session.read_text(encoding="utf-8")
    tracker_text = tracker.read_text(encoding="utf-8")
    assert "Created a fresh daily Task 42 continuation session" in tracker_text
    assert (plan_state_dir / "sync.log").exists()


def test_resolve_current_session_fails_closed_when_state_exists_without_current(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    sessions_dir = repo / "sessions"
    session_file = sessions_dir / "2026" / "04" / "2026-04-24-001-old-session.md"
    session_file.parent.mkdir(parents=True)
    session_file.write_text("---\nsession_id: 2026-04-24-001\n---\n", encoding="utf-8")
    state_path = sessions_dir / "state.json"
    state_path.write_text('{"current":null,"paused":[],"updated_at":"2026-04-24T10:00:00+02:00"}\n', encoding="utf-8")

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(module, "SESSION_STATE_PATH", state_path)
    monkeypatch.setattr(module, "SESSIONS_CURRENT_REL", "sessions/current")

    with pytest.raises(module.TaskError, match="refusing to infer the latest historical session"):
        module._resolve_current_session()

    assert module._resolve_current_session("sessions/2026/04/2026-04-24-001-old-session.md") == session_file


def test_build_parser_accepts_bootstrap_init() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["bootstrap", "init", "--target-dir", "/tmp/bootstrap-target", "--templates-root", "ops/templates"])
    assert args.command == "bootstrap"
    assert args.subcommand == "init"
    assert args.target_dir == "/tmp/bootstrap-target"
    assert args.templates_root == "ops/templates"


def test_build_parser_accepts_report_generate() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["report", "generate", "--kind", "all", "--strict-drift"])
    assert args.command == "report"
    assert args.subcommand == "generate"
    assert args.kind == "all"
    assert args.strict_drift is True


def test_build_parser_accepts_hooks_verify() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["hooks", "verify", "--require-installed"])
    assert args.command == "hooks"
    assert args.subcommand == "verify"
    assert args.require_installed is True


def test_build_parser_accepts_emergency_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "emergency",
        "plan",
        "--severity",
        "P1",
        "--summary",
        "Guard regression",
        "--label",
        "guard-regression",
    ])
    assert args.command == "emergency"
    assert args.subcommand == "plan"
    assert args.severity == "P1"
    assert args.summary == "Guard regression"
    assert args.label == "guard-regression"


def test_build_parser_accepts_taskmaster_generate_one() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["taskmaster", "generate-one", "--id", "104"])
    assert args.command == "taskmaster"
    assert args.subcommand == "generate-one"
    assert args.task_id == "104"


def test_build_parser_accepts_taskmaster_health() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["taskmaster", "health", "--tag", "master", "--report-file", "reports/taskmaster.txt"])
    assert args.command == "taskmaster"
    assert args.subcommand == "health"
    assert args.tag == "master"
    assert args.report_file == "reports/taskmaster.txt"


def test_build_parser_accepts_rollback_checkpoint_and_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    checkpoint_args = parser.parse_args([
        "rollback",
        "checkpoint",
        "--label",
        "before-risky-change",
        "--report-file",
        "reports/rollback/checkpoint.json",
        "--create-tag",
    ])
    assert checkpoint_args.command == "rollback"
    assert checkpoint_args.subcommand == "checkpoint"
    assert checkpoint_args.label == "before-risky-change"
    assert checkpoint_args.report_file == "reports/rollback/checkpoint.json"
    assert checkpoint_args.create_tag is True

    plan_args = parser.parse_args([
        "rollback",
        "plan",
        "--snapshot",
        "reports/rollback/checkpoint.json",
        "--report-file",
        "reports/rollback/plan.md",
    ])
    assert plan_args.command == "rollback"
    assert plan_args.subcommand == "plan"
    assert plan_args.snapshot == "reports/rollback/checkpoint.json"
    assert plan_args.report_file == "reports/rollback/plan.md"


def test_build_parser_accepts_compaction_checkpoint() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "compaction",
        "checkpoint",
        "--task",
        "31",
        "--slug",
        "compaction-protocol",
        "--summary",
        "scope complete",
        "--next-step",
        "implement helper",
        "--last-completed",
        "scope reconciliation",
        "--open-item",
        "tests",
        "--report-dir",
        "reports/compaction",
        "--session",
        "20260424",
        "--session-file",
        "sessions/2026/04/2026-04-24-001-task19-rollback.md",
        "--dry-run",
    ])
    assert args.command == "compaction"
    assert args.subcommand == "checkpoint"
    assert args.task == "31"
    assert args.slug == "compaction-protocol"
    assert args.summary == "scope complete"
    assert args.next_step == "implement helper"
    assert args.last_completed == ["scope reconciliation"]
    assert args.open_item == ["tests"]
    assert args.session == "20260424"
    assert args.session_file == "sessions/2026/04/2026-04-24-001-task19-rollback.md"
    assert args.dry_run is True


def test_build_parser_accepts_rehearsal_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "rehearsal",
        "plan",
        "--roadmap",
        "reports/roadmap.json",
        "--checkpoint",
        "reports/checkpoint.json",
        "--label",
        "phase-1",
        "--report-file",
        "reports/rehearsal.json",
        "--runbook-file",
        "reports/rehearsal.md",
        "--max-items",
        "3",
    ])
    assert args.command == "rehearsal"
    assert args.subcommand == "plan"
    assert args.roadmap == "reports/roadmap.json"
    assert args.checkpoint == "reports/checkpoint.json"
    assert args.label == "phase-1"
    assert args.report_file == "reports/rehearsal.json"
    assert args.runbook_file == "reports/rehearsal.md"
    assert args.max_items == 3


def test_build_parser_accepts_rollout_canary_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "rollout",
        "canary-plan",
        "--label",
        "foundation-canary",
        "--report-file",
        "reports/canary.json",
        "--runbook-file",
        "reports/canary.md",
        "--dry-run",
    ])
    assert args.command == "rollout"
    assert args.subcommand == "canary-plan"
    assert args.label == "foundation-canary"
    assert args.report_file == "reports/canary.json"
    assert args.runbook_file == "reports/canary.md"
    assert args.dry_run is True


def test_build_parser_accepts_agent_compatibility_report() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "agent",
        "compatibility-report",
        "--matrix-file",
        "templates/registry/agent-compatibility-matrix.json",
        "--report-file",
        "reports/agent-compatibility.json",
        "--runbook-file",
        "reports/agent-compatibility.md",
        "--strict",
        "--dry-run",
    ])
    assert args.command == "agent"
    assert args.subcommand == "compatibility-report"
    assert args.matrix_file == "templates/registry/agent-compatibility-matrix.json"
    assert args.report_file == "reports/agent-compatibility.json"
    assert args.runbook_file == "reports/agent-compatibility.md"
    assert args.strict is True
    assert args.dry_run is True


def test_build_parser_accepts_validation_final_suite() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "validation",
        "final-suite",
        "--label",
        "task68-final",
        "--report-dir",
        "reports/final-validation-suite",
        "--execute",
        "--pytest-target",
        "tests/meta_workflow_guard/test_codex_task.py",
    ])
    assert args.command == "validation"
    assert args.subcommand == "final-suite"
    assert args.label == "task68-final"
    assert args.report_dir == "reports/final-validation-suite"
    assert args.execute is True
    assert args.pytest_target == ["tests/meta_workflow_guard/test_codex_task.py"]


def test_build_parser_accepts_sync_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "sync",
        "plan",
        "--source-dir",
        "/tmp/source-repo",
        "--target-dir",
        "/tmp/target-repo",
        "--label",
        "foundation-sync",
        "--report-file",
        "reports/sync.json",
        "--runbook-file",
        "reports/sync.md",
    ])
    assert args.command == "sync"
    assert args.subcommand == "plan"
    assert args.source_dir == "/tmp/source-repo"
    assert args.target_dir == "/tmp/target-repo"
    assert args.label == "foundation-sync"
    assert args.report_file == "reports/sync.json"
    assert args.runbook_file == "reports/sync.md"


def _write_rollback_test_repo(module, monkeypatch, tmp_path) -> Path:
    repo = tmp_path
    sessions_dir = repo / "sessions"
    plans_dir = repo / "plans"
    active_dir = repo / "docs" / "ai" / "work-tracking" / "active"
    taskmaster_json = repo / ".taskmaster" / "tasks" / "tasks.json"
    memory_dir = repo / ".serena" / "memories"
    session_file = sessions_dir / "2026" / "04" / "2026-04-24-001-task19-rollback.md"
    plan_file = plans_dir / "2026-04-24-task19-rollback.md"

    session_file.parent.mkdir(parents=True)
    plan_file.parent.mkdir(parents=True)
    active_dir.mkdir(parents=True)
    taskmaster_json.parent.mkdir(parents=True)
    memory_dir.mkdir(parents=True)

    session_file.write_text(
        "---\nsession_id: 2026-04-24-001\ndate: 2026-04-24\n---\n\n# session\n\n### 📝 Progress Log\n\n",
        encoding="utf-8",
    )
    plan_file.write_text("# plan\n", encoding="utf-8")
    (active_dir / "20260424-task19-rollback-ACTIVE").mkdir()
    (repo / "sessions" / "current").symlink_to(Path("2026/04/2026-04-24-001-task19-rollback.md"))
    (repo / "plans" / "current").symlink_to(Path("2026-04-24-task19-rollback.md"))
    (sessions_dir / "state.json").write_text('{"current": "2026-04-24-001-task19-rollback.md", "paused": []}\n', encoding="utf-8")
    taskmaster_json.write_text(
        json.dumps({"master": {"tasks": [{"id": "19", "status": "in-progress", "dependencies": [], "subtasks": []}]}}),
        encoding="utf-8",
    )
    (memory_dir / "2026-04-24_task19_rollback.md").write_text("# memory\n", encoding="utf-8")

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(module, "PLAN_CURRENT", plans_dir / "current")
    monkeypatch.setattr(module, "WORK_TRACKING_BASE", active_dir)
    monkeypatch.setattr(module, "SESSION_STATE_PATH", sessions_dir / "state.json")
    monkeypatch.setattr(module, "TASKMASTER_TASKS_JSON", taskmaster_json)
    return repo


def test_handle_rollback_checkpoint_writes_portable_manifest(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = _write_rollback_test_repo(module, monkeypatch, tmp_path)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-19-rollback-mechanism"
        if args == ["rev-parse", "HEAD"]:
            return "abc123"
        if args == ["status", "--short"]:
            return " M scripts/codex-task\n?? reports/rollback/checkpoint.json"
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)

    output = repo / "reports" / "rollback" / "checkpoint.json"
    args = argparse.Namespace(
        label="task19-scope",
        report_file=str(output),
        create_tag=False,
        tag_prefix="codex-rollback",
        dry_run=False,
    )

    module.handle_rollback_checkpoint(args)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["label"] == "task19-scope"
    assert payload["git"]["branch"] == "feat/task-19-rollback-mechanism"
    assert payload["git"]["head"] == "abc123"
    assert payload["git"]["status"] == [
        {"status": " M", "path": "scripts/codex-task"},
        {"status": "??", "path": "reports/rollback/checkpoint.json"},
    ]
    assert payload["workflow"]["current_session"]["resolved"].endswith("2026-04-24-001-task19-rollback.md")
    assert payload["workflow"]["active_work_tracking"] == [
        "docs/ai/work-tracking/active/20260424-task19-rollback-ACTIVE"
    ]
    assert payload["taskmaster"]["summary"]["tasks"] == 1
    assert payload["serena"]["count"] == 1


def test_handle_rollback_plan_writes_non_destructive_guidance(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = _write_rollback_test_repo(module, monkeypatch, tmp_path)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    snapshot = repo / "checkpoint.json"
    snapshot.write_text(
        json.dumps(
            {
                "label": "before-risky-change",
                "created_at": "2026-04-24T15:03:13+00:00",
                "git": {"branch": "feat/task-19", "head": "abc123", "tag": "codex-rollback/example"},
                "workflow": {
                    "current_session": {"resolved": "sessions/2026/04/session.md"},
                    "current_plan": {"resolved": "plans/plan.md"},
                    "active_work_tracking": ["docs/ai/work-tracking/active/example-ACTIVE"],
                },
                "taskmaster": {"sha256": "deadbeef"},
            }
        ),
        encoding="utf-8",
    )
    report = repo / "reports" / "rollback-plan.md"
    args = argparse.Namespace(snapshot=str(snapshot), report_file=str(report), dry_run=False)

    module.handle_rollback_plan(args)

    rendered = report.read_text(encoding="utf-8")
    assert "git switch feat/task-19" in rendered
    assert "git restore --source abc123 --staged --worktree -- <path>" in rendered
    assert "git reset --hard" in rendered
    assert "No rollback commands were executed" in rendered


def test_handle_compaction_checkpoint_writes_manifest_memory_history_and_logs(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = _write_rollback_test_repo(module, monkeypatch, tmp_path)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    plan_state_dir = repo / ".plan_state"
    active_folder = repo / "docs" / "ai" / "work-tracking" / "active" / "20260424-task19-rollback-ACTIVE"
    tracker = active_folder / "TRACKER.md"
    tracker.write_text("# Tracker\n\n## Progress Log\n\n", encoding="utf-8")
    (active_folder / "HANDOFF.md").write_text("# Handoff\n\n## Current State\n- active\n", encoding="utf-8")

    monkeypatch.setattr(module, "PLAN_STATE_DIR", plan_state_dir)
    monkeypatch.setattr(module, "COMPACTION_HISTORY_PATH", plan_state_dir / "compaction-history.jsonl")

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-31-compaction-protocol"
        if args == ["rev-parse", "HEAD"]:
            return "abc123"
        if args == ["status", "--short"]:
            return " M scripts/codex-task"
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)

    report_dir = active_folder / "reports" / "compaction-protocol"
    module.handle_compaction_checkpoint(
        argparse.Namespace(
            task="31",
            slug="compaction-protocol",
            summary="Scope is complete",
            next_step="Implement compaction helper tests",
            last_completed=["Scope reconciliation"],
            open_item=["Helper verification"],
            report_dir=str(report_dir),
            memory_name=None,
            folder=None,
            work=None,
            session_file=None,
            session=None,
            dry_run=False,
        )
    )

    manifests = sorted(report_dir.glob("*-task31-compaction-protocol.json"))
    resumes = sorted(report_dir.glob("*-task31-compaction-protocol-resume.md"))
    assert len(manifests) == 1
    assert len(resumes) == 1
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest["kind"] == "compaction-checkpoint"
    assert manifest["task_id"] == "31"
    assert manifest["summary"] == "Scope is complete"
    assert manifest["next_step"] == "Implement compaction helper tests"
    assert manifest["git"]["status"] == [{"status": " M", "path": "scripts/codex-task"}]

    memory_file = repo / manifest["paths"]["memory_file"]
    assert memory_file.exists()
    assert "Compaction Checkpoint: Task 31" in memory_file.read_text(encoding="utf-8")
    assert "Implement compaction helper tests" in resumes[0].read_text(encoding="utf-8")
    assert (plan_state_dir / "compaction-history.jsonl").exists()
    assert "compaction checkpoint" in (repo / "sessions" / "2026" / "04" / "2026-04-24-001-task19-rollback.md").read_text(encoding="utf-8")
    assert "compaction checkpoint" in tracker.read_text(encoding="utf-8")
    assert "Compaction Checkpoints" in (active_folder / "HANDOFF.md").read_text(encoding="utf-8")
    assert (repo / "sessions" / "current").is_symlink()
    assert (repo / "plans" / "current").is_symlink()


def test_handle_compaction_checkpoint_requires_active_plan(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = _write_rollback_test_repo(module, monkeypatch, tmp_path)
    (repo / "plans" / "current").unlink()
    active_folder = repo / "docs" / "ai" / "work-tracking" / "active" / "20260424-task19-rollback-ACTIVE"
    (active_folder / "TRACKER.md").write_text("# Tracker\n\n## Progress Log\n\n", encoding="utf-8")

    with pytest.raises(module.TaskError, match="plans/current symlink missing"):
        module.handle_compaction_checkpoint(
            argparse.Namespace(
                task="31",
                slug="compaction-protocol",
                summary="Scope",
                next_step="Next",
                last_completed=None,
                open_item=None,
                report_dir=None,
                memory_name=None,
                folder=None,
                work=None,
                session_file=None,
                session=None,
                dry_run=False,
            )
        )


def test_handle_rehearsal_plan_writes_manifest_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = _write_rollback_test_repo(module, monkeypatch, tmp_path)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-23-migration-rehearsal-environment"
        if args == ["rev-parse", "HEAD"]:
            return "def456"
        if args == ["status", "--short"]:
            return " M scripts/codex-task\n?? reports/rehearsal-plan.json"
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)

    roadmap = repo / "reports" / "migration-roadmap.json"
    checkpoint = repo / "reports" / "checkpoint.json"
    report = repo / "reports" / "rehearsal-plan.json"
    runbook = repo / "reports" / "rehearsal-runbook.md"
    roadmap.parent.mkdir(parents=True)
    roadmap.write_text(
        json.dumps(
            {
                "metadata": {"scanner": "migration_roadmap", "scanner_version": "1.0.0"},
                "data": {
                    "generated_at": "2026-04-24T15:03:13",
                    "migration_roadmap_version": "1.0.0",
                    "summary_metrics": {"broken_references": 2, "pending_migration": 1},
                    "priority_counts": {"critical": 1, "high": 1},
                    "category_counts": {"references": 1, "migration": 1},
                    "phases": [
                        {
                            "title": "Critical integrity",
                            "priorities": ["critical"],
                            "start_day": 0,
                            "duration_days": 2,
                        }
                    ],
                    "items": [
                        {
                            "id": "critical-references-001",
                            "priority": "critical",
                            "category": "references",
                            "title": "Repair broken reference",
                            "effort": "S",
                            "risk": "high",
                            "finding_count": 1,
                            "source_files": ["templates/example.md"],
                            "dependencies": [],
                        },
                        {
                            "id": "high-migration-001",
                            "priority": "high",
                            "category": "migration",
                            "title": "Complete migration",
                            "effort": "M",
                            "risk": "medium",
                            "finding_count": 1,
                            "source_files": ["templates/legacy.md"],
                            "dependencies": ["critical-references-001"],
                        },
                    ],
                    "taskmaster_export": {"tasks": [{"title": "Repair broken reference"}]},
                },
            }
        ),
        encoding="utf-8",
    )
    checkpoint.write_text(
        json.dumps(
            {
                "label": "before-rehearsal",
                "created_at": "2026-04-24T15:04:00+00:00",
                "git": {
                    "branch": "feat/task-23-migration-rehearsal-environment",
                    "head": "abc123",
                    "tag": None,
                    "status": [],
                },
                "workflow": {
                    "current_session": {"resolved": "sessions/2026/04/session.md"},
                    "current_plan": {"resolved": "plans/plan.md"},
                    "active_work_tracking": ["docs/ai/work-tracking/active/task23-ACTIVE"],
                },
                "taskmaster": {"sha256": "deadbeef", "summary": {"tasks": 1}},
            }
        ),
        encoding="utf-8",
    )

    args = argparse.Namespace(
        roadmap=str(roadmap),
        checkpoint=str(checkpoint),
        label="phase-1-rehearsal",
        report_file=str(report),
        runbook_file=str(runbook),
        max_items=1,
        dry_run=False,
    )

    module.handle_rehearsal_plan(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["label"] == "phase-1-rehearsal"
    assert payload["mode"] == "non-destructive-local-rehearsal"
    assert payload["executes_mutations"] is False
    assert payload["roadmap"]["total_items"] == 2
    assert payload["roadmap"]["first_items"] == [
        {
            "id": "critical-references-001",
            "priority": "critical",
            "category": "references",
            "title": "Repair broken reference",
            "effort": "S",
            "risk": "high",
            "finding_count": 1,
            "source_files": ["templates/example.md"],
            "dependencies": [],
        }
    ]
    assert payload["checkpoint"]["git"]["head"] == "abc123"
    assert payload["current_state"]["git"]["status"] == [
        {"status": " M", "path": "scripts/codex-task"},
        {"status": "??", "path": "reports/rehearsal-plan.json"},
    ]
    assert payload["rehearsal_environment"]["automatic_worktree_creation"] is False
    assert "No Docker containers are created." in payload["non_goals"]

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Migration Rehearsal Runbook" in runbook_text
    assert "Repair broken reference" in runbook_text
    assert "No rehearsal commands were executed by this plan." in runbook_text
    assert "git reset --hard" not in runbook_text


def _patch_canary_rollout_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-40-canary-deployment-system"
        if args == ["rev-parse", "HEAD"]:
            return "abc123"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/session.md"},
            "current_plan": {"resolved": "plans/2026-05-08-task40-canary.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260508-task40-canary-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_dependencies": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 3})


def test_build_canary_rollout_plan_is_non_destructive(monkeypatch) -> None:
    module = load_task_module()
    _patch_canary_rollout_snapshots(module, monkeypatch)

    plan = module._build_canary_rollout_plan(argparse.Namespace(label="foundation-canary"))

    assert plan["version"] == 1
    assert plan["label"] == "foundation-canary"
    assert plan["mode"] == "non-destructive-foundation-canary-rollout-plan"
    assert plan["executes_mutations"] is False
    assert plan["current_state"]["git"]["branch"] == "feat/task-40-canary-deployment-system"
    assert [stage["id"] for stage in plan["stages"]] == ["codex", "claude", "other-agents"]
    assert [stage["minimum_observation_hours"] for stage in plan["stages"]] == [24, 48, 72]
    assert plan["promotion_model"]["automatic_promotion"] is False
    assert plan["promotion_model"]["requires_reviewed_evidence"] is True
    assert plan["promotion_model"]["minimum_total_observation_hours"] == 144
    assert plan["rollback_policy"]["automatic_rollback"] is False
    assert plan["rollback_policy"]["requires_checkpoint"] is True
    assert "No traffic is split." in plan["non_goals"]
    assert "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest" in plan["recommended_verification_commands"]


def test_render_canary_rollout_runbook_names_stages_and_non_goals(monkeypatch) -> None:
    module = load_task_module()
    _patch_canary_rollout_snapshots(module, monkeypatch)
    plan = module._build_canary_rollout_plan(argparse.Namespace(label="foundation-canary"))

    runbook = module._render_canary_rollout_runbook(plan)

    assert "# Foundation Canary Rollout Runbook" in runbook
    assert "Codex baseline canary" in runbook
    assert "Claude runtime canary" in runbook
    assert "Other agent/profile canary" in runbook
    assert "Minimum total observation hours: 144" in runbook
    assert "No deployment is executed." in runbook
    assert "No deployment, promotion, rollback, traffic split, dashboard update, or notification was executed by this plan." in runbook


def test_handle_rollout_canary_plan_writes_manifest_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_canary_rollout_snapshots(module, monkeypatch)

    report = repo / "reports" / "canary-plan.json"
    runbook = repo / "reports" / "canary-runbook.md"
    args = argparse.Namespace(
        label="task40-foundation-canary",
        report_file=str(report.relative_to(repo)),
        runbook_file=str(runbook.relative_to(repo)),
        dry_run=False,
    )

    module.handle_rollout_canary_plan(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task40-foundation-canary"
    assert payload["executes_mutations"] is False
    assert payload["stage_count"] == 3
    assert payload["stages"][0]["id"] == "codex"
    assert payload["stages"][1]["id"] == "claude"
    assert payload["stages"][2]["id"] == "other-agents"
    assert payload["promotion_model"]["automatic_promotion"] is False
    assert payload["rollback_policy"]["automatic_rollback"] is False

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Foundation Canary Rollout Runbook" in runbook_text
    assert "No deployment, promotion, rollback, traffic split, dashboard update, or notification was executed by this plan." in runbook_text


def test_real_agent_compatibility_matrix_validates() -> None:
    module = load_task_module()
    matrix_path, matrix = module._load_agent_compatibility_matrix("templates/registry/agent-compatibility-matrix.json")

    issues = module._validate_agent_compatibility_matrix(matrix, matrix_path)

    assert issues == []


def test_build_agent_compatibility_report_summarizes_matrix(monkeypatch) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    report = module._build_agent_compatibility_report(argparse.Namespace(
        matrix_file="templates/registry/agent-compatibility-matrix.json",
    ))

    assert report["valid"] is True
    assert report["matrix_schema"] == "agent-compatibility-matrix.v1"
    assert report["metrics"]["agent_count"] == 3
    assert report["metrics"]["feature_count"] == 10
    assert report["metrics"]["validation_issue_count"] == 0
    assert report["metrics"]["agent_status_counts"]["supported"] == 2
    assert report["metrics"]["agent_status_counts"]["planned"] == 1
    assert {agent["id"] for agent in report["agents"]} == {"codex", "claude", "generic-agent"}
    assert any(feature["id"] == "pre_mutation_gate" for feature in report["features"])


def test_agent_compatibility_matrix_rejects_unknown_feature_flag() -> None:
    module = load_task_module()
    _, matrix = module._load_agent_compatibility_matrix("templates/registry/agent-compatibility-matrix.json")
    matrix = json.loads(json.dumps(matrix))
    matrix["agents"][0]["capabilities"]["unknown-feature"] = "native"

    issues = module._validate_agent_compatibility_matrix(matrix)

    assert any("unknown feature flags: unknown-feature" in issue for issue in issues)


def test_agent_compatibility_runbook_lists_agents_and_metrics(monkeypatch) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    report = module._build_agent_compatibility_report(argparse.Namespace(
        matrix_file="templates/registry/agent-compatibility-matrix.json",
    ))

    runbook = module._render_agent_compatibility_runbook(report)

    assert "# Agent Compatibility Report" in runbook
    assert "Codex Deep Work Agent" in runbook
    assert "Claude Runtime Adapter" in runbook
    assert "Future Agent/Profile Adapter" in runbook
    assert "Mechanical feature coverage" in runbook
    assert "- None" in runbook


def test_handle_agent_compatibility_report_writes_json_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    report = tmp_path / "agent-compatibility.json"
    runbook = tmp_path / "agent-compatibility.md"
    args = argparse.Namespace(
        matrix_file="templates/registry/agent-compatibility-matrix.json",
        report_file=str(report),
        runbook_file=str(runbook),
        strict=True,
        dry_run=False,
    )

    module.handle_agent_compatibility_report(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["metrics"]["agent_count"] == 3
    assert payload["metrics"]["validation_issue_count"] == 0
    assert "Claude Runtime Adapter" in runbook.read_text(encoding="utf-8")


def _patch_final_validation_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-68-final-validation-suite"
        if args == ["rev-parse", "HEAD"]:
            return "feed123"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-12-task68.md"},
            "current_plan": {"resolved": "plans/2026-05-12-task68-final-validation-suite.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_refs": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 6})


def _final_validation_args(tmp_path: Path, *, execute: bool = False, allow_failures: bool = False, skip_pytest: bool = False):
    return argparse.Namespace(
        label="task68-final",
        report_dir=str(tmp_path / "reports" / "final-validation-suite"),
        report_file=None,
        runbook_file=None,
        execute=execute,
        allow_failures=allow_failures,
        pytest_target=["tests/meta_workflow_guard/test_codex_task.py"],
        skip_pytest=skip_pytest,
        dry_run=False,
    )


def test_build_final_validation_suite_maps_historical_requirements(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _patch_final_validation_snapshots(module, monkeypatch)

    plan = module._build_final_validation_suite(_final_validation_args(tmp_path))

    assert plan["mode"] == "final-validation-suite"
    assert plan["executes_commands"] is False
    assert plan["current_state"]["git"]["branch"] == "feat/task-68-final-validation-suite"
    requirement_ids = {requirement["id"] for requirement in plan["requirements"]}
    assert {
        "reference-integrity",
        "security-validation",
        "performance-validation",
        "cost-validation",
        "compatibility-validation",
        "sign-off-workflow",
    }.issubset(requirement_ids)
    check_ids = [check["id"] for check in plan["checks"]]
    assert "scanner-suite" in check_ids
    assert "static-report-pipeline" in check_ids
    assert "agent-compatibility" in check_ids
    assert "pytest" in check_ids
    assert any("--strict-performance" in check["command"] for check in plan["checks"])


def test_render_final_validation_runbook_names_signoff_and_commands(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _patch_final_validation_snapshots(module, monkeypatch)
    plan = module._build_final_validation_suite(_final_validation_args(tmp_path, skip_pytest=True))
    module._summarise_final_validation_suite(plan)

    runbook = module._render_final_validation_runbook(plan)

    assert "# Final Validation Suite Runbook" in runbook
    assert "Reference integrity checks" in runbook
    assert "Static validation report pipeline" in runbook
    assert "Sign-Off Checklist" in runbook
    assert "No validation commands were executed by this planned suite." in runbook


def test_handle_validation_final_suite_executes_and_captures_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    _patch_final_validation_snapshots(module, monkeypatch)
    calls = []

    def fake_run(command, cwd, capture_output, text, env):
        calls.append((command, cwd, env))
        return FakeCompletedProcess(returncode=0, stdout=f"ok: {' '.join(command)}\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    args = _final_validation_args(tmp_path, execute=True, skip_pytest=True)

    module.handle_validation_final_suite(args)

    report = tmp_path / "reports" / "final-validation-suite" / "20260424-150313-task68-final.json"
    runbook = tmp_path / "reports" / "final-validation-suite" / "20260424-150313-task68-final.md"
    assert report.exists()
    assert runbook.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["summary"]["status"] == "passed"
    assert payload["summary"]["failed_required"] == 0
    assert payload["valid"] is True
    assert len(calls) == len(payload["checks"])
    first_evidence = tmp_path / payload["checks"][0]["result"]["evidence"]
    assert "Exit code: 0" in first_evidence.read_text(encoding="utf-8")
    assert "Validation command outputs are captured" in runbook.read_text(encoding="utf-8")


def test_handle_validation_final_suite_fails_after_writing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    _patch_final_validation_snapshots(module, monkeypatch)

    def fake_run(command, cwd, capture_output, text, env):
        if any(str(part).endswith("codex-guard") for part in command) and "validate" in command:
            return FakeCompletedProcess(returncode=2, stdout="", stderr="guard blocked")
        return FakeCompletedProcess(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    args = _final_validation_args(tmp_path, execute=True, skip_pytest=True)

    with pytest.raises(module.TaskError, match="Final validation suite failed"):
        module.handle_validation_final_suite(args)

    report = tmp_path / "reports" / "final-validation-suite" / "20260424-150313-task68-final.json"
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["summary"]["status"] == "failed"
    assert payload["summary"]["failed_required"] == 1
    failed = [check for check in payload["checks"] if check["result"]["status"] == "failed"]
    assert failed[0]["id"] == "codex-guard"
    failed_evidence = tmp_path / failed[0]["result"]["evidence"]
    assert "guard blocked" in failed_evidence.read_text(encoding="utf-8")


def _write_emergency_response_policy(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "description": "test policy",
                "halt_recommended_for": ["P0", "P1"],
                "severities": {
                    "P0": {
                        "title": "Critical",
                        "description": "critical incident",
                        "response_sla_minutes": 15,
                        "review_sla_hours": 24,
                        "examples": ["main is blocked"],
                    },
                    "P1": {
                        "title": "High",
                        "description": "high-risk incident",
                        "response_sla_minutes": 30,
                        "review_sla_hours": 48,
                        "examples": ["guard regression"],
                    },
                    "P2": {
                        "title": "Recoverable",
                        "description": "recoverable issue",
                        "response_sla_minutes": 120,
                        "review_sla_hours": 72,
                        "examples": [],
                    },
                },
                "halt_mechanism": {
                    "automatic_halt": False,
                    "guidance": ["Stop implementation until state is inspected."],
                },
                "response_checklist": [
                    {
                        "id": "confirm-state",
                        "title": "Confirm state",
                        "commands": ["git status --short --branch"],
                    }
                ],
                "escalation_guidance": {
                    "repo_native": "Record the incident in work tracking.",
                    "external_integrations": "No external service configured.",
                },
                "post_incident_review": ["What happened?"],
                "non_goals": ["No notification is sent."],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _patch_emergency_response_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-35-emergency-response-system"
        if args == ["rev-parse", "HEAD"]:
            return "def456"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/session.md"},
            "current_plan": {"resolved": "plans/2026-05-10-task35.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260510-task35-emergency-response-system-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_dependencies": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 4})


def test_build_emergency_response_plan_classifies_and_stays_non_destructive(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    policy = repo / "templates" / "metadata" / "emergency-response-policy.json"
    _write_emergency_response_policy(policy)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_emergency_response_snapshots(module, monkeypatch)

    plan = module._build_emergency_response_plan(
        argparse.Namespace(
            severity="P1",
            summary="Guard regression after merge",
            label="guard-regression",
            policy_file=str(policy),
        )
    )

    assert plan["version"] == 1
    assert plan["mode"] == "non-destructive-emergency-response-plan"
    assert plan["executes_actions"] is False
    assert plan["incident"]["id"] == "20260424-150313-guard-regression"
    assert plan["incident"]["severity"] == "P1"
    assert plan["incident"]["classification"]["response_sla_minutes"] == 30
    assert plan["halt"]["recommended"] is True
    assert plan["halt"]["automatic_halt"] is False
    assert plan["current_state"]["git"]["branch"] == "feat/task-35-emergency-response-system"
    assert "python3 scripts/codex-guard validate --include-untracked" in plan["recommended_verification_commands"]
    assert "No notification is sent." in plan["non_goals"]
    assert any("No rollback" in item for item in plan["non_goals"])


def test_build_emergency_response_plan_rejects_unknown_severity(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    policy = tmp_path / "policy.json"
    _write_emergency_response_policy(policy)
    _patch_emergency_response_snapshots(module, monkeypatch)

    with pytest.raises(module.TaskError, match="Unknown emergency severity P9"):
        module._build_emergency_response_plan(
            argparse.Namespace(severity="P9", summary="unknown", label=None, policy_file=str(policy))
        )


def test_render_emergency_response_runbook_names_halt_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    policy = tmp_path / "policy.json"
    _write_emergency_response_policy(policy)
    _patch_emergency_response_snapshots(module, monkeypatch)
    plan = module._build_emergency_response_plan(
        argparse.Namespace(severity="P0", summary="Main blocked", label="main-blocked", policy_file=str(policy))
    )

    runbook = module._render_emergency_response_runbook(plan)

    assert "# Emergency Response Runbook" in runbook
    assert "Severity: P0 - Critical" in runbook
    assert "Halt recommended: True" in runbook
    assert "`git status --short --branch`" in runbook
    assert "What happened?" in runbook
    assert "No halt, notification, rollback, reset, cleanup, dashboard update, or external incident action was executed by this plan." in runbook


def test_handle_emergency_plan_writes_manifest_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    policy = repo / "templates" / "metadata" / "emergency-response-policy.json"
    _write_emergency_response_policy(policy)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_emergency_response_snapshots(module, monkeypatch)

    report = repo / "reports" / "emergency-plan.json"
    runbook = repo / "reports" / "emergency-runbook.md"
    args = argparse.Namespace(
        severity="P2",
        summary="Monitoring warning",
        label="monitoring-warning",
        policy_file=str(policy),
        report_file=str(report.relative_to(repo)),
        runbook_file=str(runbook.relative_to(repo)),
        dry_run=False,
    )

    module.handle_emergency_plan(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["incident"]["severity"] == "P2"
    assert payload["halt"]["recommended"] is False
    assert payload["executes_actions"] is False

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Emergency Response Runbook" in runbook_text
    assert "Monitoring warning" in runbook_text
    assert "No halt, notification, rollback, reset, cleanup, dashboard update, or external incident action was executed by this plan." in runbook_text


SYNC_TEST_ASSET_PATHS = [
    ".codex/config.toml",
    "templates/metadata/template-metadata-policy.json",
    "templates/metadata/template-monitoring-policy.json",
    "templates/metadata/template-performance-policy.json",
    "templates/metadata/template-cost-policy.json",
    "templates/metadata/emergency-response-policy.json",
    "templates/engine/core/portable-foundation-spec.md",
    "templates/engine/validation/foundation-adoption-guide.md",
    "scripts/_repo_structure.py",
    "scripts/codex-guard",
    "scripts/codex-task",
    "scripts/template-metrics-dashboard",
    "scripts/template-monitoring",
    "scripts/template-phase0-validation",
    "scripts/template-performance-harness",
    "scripts/template-cost-report",
    "scripts/template-migration-health-dashboard",
]


def _write_sync_test_assets(root: Path, marker: str) -> None:
    for relative in SYNC_TEST_ASSET_PATHS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == ".codex/config.toml":
            path.write_text(
                "[repo_structure]\n"
                'templates_root = "templates"\n'
                'sessions_root = "sessions"\n'
                'plans_root = "plans"\n'
                'plan_state_dir = ".plan_state"\n'
                'taskmaster_root = ".taskmaster"\n'
                'work_tracking_root = "docs/ai/work-tracking"\n'
                'reports_root = "reports"\n',
                encoding="utf-8",
            )
        else:
            path.write_text(f"{marker}: {relative}\n", encoding="utf-8")


def _file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_handle_sync_plan_reports_review_queue_without_mutating_repos(tmp_path) -> None:
    module = load_task_module()
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_sync_test_assets(source, "source")
    _write_sync_test_assets(target, "source")

    (target / "templates" / "metadata" / "template-metadata-policy.json").unlink()
    (target / "scripts" / "codex-task").write_text("target-local codex-task\n", encoding="utf-8")

    before_source = _file_snapshot(source)
    before_target = _file_snapshot(target)
    report = tmp_path / "reports" / "sync-plan.json"
    runbook = tmp_path / "reports" / "sync-runbook.md"

    args = argparse.Namespace(
        source_dir=str(source),
        target_dir=str(target),
        label="fixture-sync",
        report_file=str(report),
        runbook_file=str(runbook),
        dry_run=False,
    )

    module.handle_sync_plan(args)

    assert _file_snapshot(source) == before_source
    assert _file_snapshot(target) == before_target

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["label"] == "fixture-sync"
    assert payload["mode"] == "non-destructive-cross-repo-sync-plan"
    assert payload["executes_mutations"] is False
    assert payload["asset_count"] == len(SYNC_TEST_ASSET_PATHS)
    assert payload["source"]["git"]["inside_work_tree"] is False
    assert payload["target"]["git"]["inside_work_tree"] is False
    statuses = {asset["id"]: asset["status"] for asset in payload["assets"]}
    assert statuses["codex-config"] == "identical"
    assert statuses["metadata-policy"] == "missing"
    assert statuses["codex-task"] == "different"
    queue = {item["asset_id"]: item for item in payload["manual_review_queue"]}
    assert queue["metadata-policy"]["action"] == "copy-from-source"
    assert queue["codex-task"]["action"] == "review-update"
    assert "No branches, commits, pushes, or pull requests are created." in payload["non_goals"]

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Cross-Repository Sync Runbook" in runbook_text
    assert "Template metadata policy" in runbook_text
    assert "Codex task helper" in runbook_text
    assert "No sync commands were executed by this plan." in runbook_text


def test_handle_report_generate_runs_drift_before_metrics(monkeypatch) -> None:
    module = load_task_module()
    commands = []

    def fake_run(cmd, cwd=None):
        commands.append(cmd)
        return FakeCompletedProcess(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    args = argparse.Namespace(
        kind="all",
        report_dir="reports/template-metrics",
        drift_report_dir="reports/template-drift",
        metrics_file="reports/template-metrics/latest.json",
        monitoring_report_dir="reports/template-monitoring",
        scanner_data_dir="scripts/template-ssot-scanner/output/data",
        phase0_monitoring_file="reports/template-monitoring/latest.json",
        phase0_report_dir="reports/phase0-scanner-validation",
        performance_report_dir="reports/template-performance",
        performance_baseline_file=None,
        cost_report_dir="reports/cost-tracking",
        cost_usage_file=None,
        migration_health_report_dir="reports/migration-health",
        strict_drift=True,
        strict_monitoring=True,
        strict_phase0=True,
        strict_performance=True,
        strict_cost=True,
        strict_migration_health=True,
        dry_run=False,
    )

    module.handle_report_generate(args)

    assert len(commands) == 7
    assert Path(commands[0][1]).name == "codex-guard"
    assert commands[0][2:] == ["drift-check", "--report-dir", "reports/template-drift", "--strict"]
    assert Path(commands[1][1]).name == "template-metrics-dashboard"
    assert commands[1][2:] == ["--report-dir", "reports/template-metrics"]
    assert Path(commands[2][1]).name == "template-monitoring"
    assert commands[2][2:] == [
        "--metrics",
        "reports/template-metrics/latest.json",
        "--report-dir",
        "reports/template-monitoring",
        "--strict",
    ]
    assert Path(commands[3][1]).name == "template-phase0-validation"
    assert commands[3][2:] == [
        "--scanner-data-dir",
        "scripts/template-ssot-scanner/output/data",
        "--monitoring-file",
        "reports/template-monitoring/latest.json",
        "--report-dir",
        "reports/phase0-scanner-validation",
        "--strict",
    ]
    assert Path(commands[4][1]).name == "template-performance-harness"
    assert commands[4][2:] == [
        "--report-dir",
        "reports/template-performance",
        "--strict",
    ]
    assert Path(commands[5][1]).name == "template-cost-report"
    assert commands[5][2:] == [
        "--report-dir",
        "reports/cost-tracking",
        "--strict",
    ]
    assert Path(commands[6][1]).name == "template-migration-health-dashboard"
    assert commands[6][2:] == [
        "--metrics-file",
        "reports/template-metrics/latest.json",
        "--monitoring-file",
        "reports/template-monitoring/latest.json",
        "--phase0-file",
        "reports/phase0-scanner-validation/latest.json",
        "--performance-file",
        "reports/template-performance/latest.json",
        "--cost-file",
        "reports/cost-tracking/latest.json",
        "--report-dir",
        "reports/migration-health",
        "--strict",
    ]


def test_handle_report_generate_telemetry_kind_runs_full_static_pipeline(monkeypatch) -> None:
    module = load_task_module()
    commands = []

    def fake_run(cmd, cwd=None):
        commands.append(cmd)
        return FakeCompletedProcess(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    args = argparse.Namespace(
        kind="telemetry",
        report_dir="reports/template-metrics",
        drift_report_dir="reports/template-drift",
        metrics_file="reports/template-metrics/latest.json",
        monitoring_report_dir="reports/template-monitoring",
        scanner_data_dir="scripts/template-ssot-scanner/output/data",
        phase0_monitoring_file="reports/template-monitoring/latest.json",
        phase0_report_dir="reports/phase0-scanner-validation",
        performance_report_dir="reports/template-performance",
        performance_baseline_file=None,
        cost_report_dir="reports/cost-tracking",
        cost_usage_file=None,
        migration_health_report_dir="reports/migration-health",
        strict_drift=True,
        strict_monitoring=True,
        strict_phase0=True,
        strict_performance=True,
        strict_cost=True,
        strict_migration_health=True,
        dry_run=False,
    )

    module.handle_report_generate(args)

    assert [Path(command[1]).name for command in commands] == [
        "codex-guard",
        "template-metrics-dashboard",
        "template-monitoring",
        "template-phase0-validation",
        "template-performance-harness",
        "template-cost-report",
        "template-migration-health-dashboard",
    ]
    assert commands[3][2:] == [
        "--scanner-data-dir",
        "scripts/template-ssot-scanner/output/data",
        "--monitoring-file",
        "reports/template-monitoring/latest.json",
        "--report-dir",
        "reports/phase0-scanner-validation",
        "--strict",
    ]


def _write_pre_commit_test_repo(
    module,
    monkeypatch,
    tmp_path,
    config_text: str | None = None,
    create_binary: bool = True,
) -> tuple[Path, Path]:
    repo = tmp_path
    config = repo / ".pre-commit-config.yaml"
    hook = repo / ".git" / "hooks" / "pre-commit"
    binary = repo / ".venv" / "bin" / "pre-commit"
    config.write_text(
        config_text
        or """
repos:
  - repo: local
    hooks:
      - id: codex-guard-validate
        entry: python3 scripts/codex-guard validate --include-untracked
        language: system
        pass_filenames: false
        always_run: true
      - id: codex-guard-drift-check
        entry: python3 scripts/codex-guard drift-check --strict --report-dir ""
        language: system
        pass_filenames: false
        always_run: true
""".lstrip(),
        encoding="utf-8",
    )
    if create_binary:
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\nprintf 'pre-commit 4.6.0\\n'\n", encoding="utf-8")
        binary.chmod(0o755)
    hook.parent.mkdir(parents=True)

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "PRE_COMMIT_CONFIG", config)
    monkeypatch.setattr(module, "PRE_COMMIT_HOOK", hook)
    monkeypatch.setattr(module, "_pre_commit_version", lambda path: "pre-commit 4.6.0")
    return repo, hook


def test_handle_hooks_verify_warns_when_local_hook_missing(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    _write_pre_commit_test_repo(module, monkeypatch, tmp_path)

    module.handle_hooks_verify(argparse.Namespace(require_installed=False))

    output = capsys.readouterr().out
    assert ".pre-commit-config.yaml: ok" in output
    assert "pre-commit binary: ok" in output
    assert "local pre-commit hook: warning" in output
    assert ".venv/bin/pre-commit install" in output
    assert "Hook verification passed" in output


def test_handle_hooks_verify_can_require_installed_hook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _write_pre_commit_test_repo(module, monkeypatch, tmp_path)

    with pytest.raises(module.TaskError):
        module.handle_hooks_verify(argparse.Namespace(require_installed=True))


def test_handle_hooks_verify_accepts_installed_pre_commit_hook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    _, hook = _write_pre_commit_test_repo(module, monkeypatch, tmp_path)
    hook.write_text("#!/bin/sh\n# pre-commit hook\n", encoding="utf-8")
    hook.chmod(0o755)

    module.handle_hooks_verify(argparse.Namespace(require_installed=True))

    output = capsys.readouterr().out
    assert "local pre-commit hook: ok" in output
    assert "Hook verification passed" in output


def test_handle_hooks_verify_rejects_missing_pre_commit_binary(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _write_pre_commit_test_repo(module, monkeypatch, tmp_path, create_binary=False)
    monkeypatch.setattr(module.shutil, "which", lambda name: None)

    with pytest.raises(module.TaskError):
        module.handle_hooks_verify(argparse.Namespace(require_installed=False))


def test_handle_hooks_verify_rejects_unmanaged_hook_file(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _, hook = _write_pre_commit_test_repo(module, monkeypatch, tmp_path)
    hook.write_text("#!/bin/sh\nprintf 'custom hook\\n'\n", encoding="utf-8")
    hook.chmod(0o755)

    with pytest.raises(module.TaskError):
        module.handle_hooks_verify(argparse.Namespace(require_installed=True))


def test_handle_hooks_verify_rejects_missing_guard_entry(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _write_pre_commit_test_repo(
        module,
        monkeypatch,
        tmp_path,
        config_text="""
repos:
  - repo: local
    hooks:
      - id: codex-guard-validate
        entry: python3 scripts/codex-guard validate --include-untracked
        language: system
        pass_filenames: false
        always_run: true
""".lstrip(),
    )

    with pytest.raises(module.TaskError):
        module.handle_hooks_verify(argparse.Namespace(require_installed=False))


def test_handle_report_generate_dry_run_does_not_execute(monkeypatch, capsys) -> None:
    module = load_task_module()

    def fake_run(cmd, cwd=None):  # pragma: no cover - should never be called
        raise AssertionError("dry-run should not execute report commands")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    args = argparse.Namespace(
        kind="metrics",
        report_dir="reports/template-metrics",
        drift_report_dir="reports/template-drift",
        metrics_file="reports/template-metrics/latest.json",
        monitoring_report_dir="reports/template-monitoring",
        scanner_data_dir="scripts/template-ssot-scanner/output/data",
        phase0_monitoring_file="reports/template-monitoring/latest.json",
        phase0_report_dir="reports/phase0-scanner-validation",
        performance_report_dir="reports/template-performance",
        performance_baseline_file=None,
        cost_report_dir="reports/cost-tracking",
        cost_usage_file=None,
        migration_health_report_dir="reports/migration-health",
        strict_drift=False,
        strict_monitoring=False,
        strict_phase0=False,
        strict_performance=False,
        strict_cost=False,
        strict_migration_health=False,
        dry_run=True,
    )

    module.handle_report_generate(args)

    output = capsys.readouterr().out
    assert "Would run:" in output
    assert "template-metrics-dashboard" in output


def test_handle_bootstrap_init_creates_starter_assets(tmp_path) -> None:
    module = load_task_module()
    target = tmp_path / "storefront"
    args = argparse.Namespace(
        target_dir=str(target),
        force=False,
        templates_root=None,
        sessions_root=None,
        plans_root=None,
        plan_state_dir=None,
        taskmaster_root=None,
        work_tracking_root=None,
        reports_root=None,
        dry_run=False,
    )

    module.handle_bootstrap_init(args)

    config_path = target / ".codex" / "config.toml"
    policy_path = target / "templates" / "metadata" / "template-metadata-policy.json"
    monitoring_policy_path = target / "templates" / "metadata" / "template-monitoring-policy.json"
    performance_policy_path = target / "templates" / "metadata" / "template-performance-policy.json"
    cost_policy_path = target / "templates" / "metadata" / "template-cost-policy.json"
    emergency_policy_path = target / "templates" / "metadata" / "emergency-response-policy.json"
    setup_path = target / ".codex" / "bootstrap" / "FOUNDATION-SETUP.md"

    assert config_path.exists()
    assert policy_path.exists()
    assert monitoring_policy_path.exists()
    assert performance_policy_path.exists()
    assert cost_policy_path.exists()
    assert emergency_policy_path.exists()
    assert setup_path.exists()
    assert "[repo_structure]" in config_path.read_text(encoding="utf-8")
    assert '"required_keys"' in policy_path.read_text(encoding="utf-8")
    assert "portable Codex foundation starter assets" in setup_path.read_text(encoding="utf-8")

    assert (target / "sessions").is_dir()
    assert (target / "plans").is_dir()
    assert (target / ".plan_state").is_dir()
    assert (target / ".taskmaster" / "tasks").is_dir()
    assert (target / "docs" / "ai" / "work-tracking" / "active").is_dir()
    assert (target / "docs" / "ai" / "work-tracking" / "archive").is_dir()
    assert (target / "reports" / "template-drift").is_dir()
    assert (target / "reports" / "template-metrics").is_dir()
    assert (target / "reports" / "template-monitoring").is_dir()
    assert (target / "reports" / "phase0-scanner-validation").is_dir()
    assert (target / "reports" / "template-performance").is_dir()
    assert (target / "reports" / "cost-tracking").is_dir()
    assert (target / "reports" / "migration-health").is_dir()
    assert (target / "reports" / "session-continuation").is_dir()


def test_work_tracking_audit_allows_between_sessions_state(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    sessions_dir = repo / "sessions"
    active_dir = repo / "docs" / "ai" / "work-tracking" / "active"
    sessions_dir.mkdir(parents=True)
    active_dir.mkdir(parents=True)
    state_path = sessions_dir / "state.json"
    state_path.write_text(
        '{"current":null,"paused":[],"updated_at":"2030-01-02T17:35:49+02:00"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(module, "WORK_TRACKING_BASE", active_dir)
    monkeypatch.setattr(module, "SESSION_STATE_PATH", state_path)
    monkeypatch.setattr(module, "SESSIONS_CURRENT_REL", "sessions/current")

    module.handle_work_tracking_audit(argparse.Namespace())

    output = capsys.readouterr().out
    assert "Audit issues detected" not in output
    assert "between sessions" in output


def test_plan_sync_allows_between_sessions_state(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    sessions_dir = repo / "sessions"
    plans_dir = repo / "plans"
    sessions_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)
    state_path = sessions_dir / "state.json"
    state_path.write_text(
        '{"current":null,"paused":[],"updated_at":"2030-01-02T17:35:49+02:00"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(module, "PLAN_CURRENT", plans_dir / "current")
    monkeypatch.setattr(module, "SESSION_STATE_PATH", state_path)

    module.handle_plan_sync(argparse.Namespace(plan=None, tracker=None, dry_run=False))

    output = capsys.readouterr().out
    assert "between sessions" in output
    assert "Plan sync skipped" in output


def test_work_tracking_scaffold_creates_missing_active_parent(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    active_dir = repo / "docs" / "ai" / "work-tracking" / "active"

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "WORK_TRACKING_BASE", active_dir)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    module.handle_work_tracking_scaffold(
        argparse.Namespace(
            task="104",
            slug="targeted-taskmaster-generation-helper",
            title="Targeted Taskmaster Generation",
            goal=None,
            force=False,
            dry_run=False,
        )
    )

    assert (active_dir / "20260424-task104-targeted-taskmaster-generation-helper-ACTIVE" / "TRACKER.md").exists()


def test_taskmaster_generate_one_updates_only_requested_existing_txt(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    tasks_dir = repo / ".taskmaster" / "tasks"
    tasks_dir.mkdir(parents=True)
    target = tasks_dir / "task_104.txt"
    unrelated = tasks_dir / "task_103.txt"
    target.write_text("# Task ID: 104\n# Status: pending\n", encoding="utf-8")
    unrelated.write_text("# Task ID: 103\n# Status: done\n", encoding="utf-8")

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "TASKMASTER_TASKS_DIR", tasks_dir)

    commands = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False):
        commands.append(cmd)
        if cmd[:2] == ["git", "status"]:
            return FakeCompletedProcess(stdout="")
        if cmd[:2] == ["task-master", "generate"]:
            output_dir = Path(cmd[cmd.index("--output") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "task_104.md").write_text(
                "# Task ID: 104\n\n"
                "**Title:** Add Targeted Taskmaster Task-File Generation Helper\n\n"
                "**Status:** in-progress\n\n"
                "**Dependencies:** 103 ✓\n\n"
                "**Priority:** high\n\n"
                "**Description:** Update one task file.\n\n"
                "**Details:**\n\n"
                "Generated details.\n\n"
                "**Test Strategy:**\n\n"
                "No test strategy provided.\n",
                encoding="utf-8",
            )
            return FakeCompletedProcess(stdout="")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module.handle_taskmaster_generate_one(argparse.Namespace(task_id="104", dry_run=False))

    output = capsys.readouterr().out
    assert "Updated .taskmaster/tasks/task_104.txt" in output
    target_text = target.read_text(encoding="utf-8")
    assert "# Status: in-progress" in target_text
    assert "# Dependencies: 103" in target_text
    assert "**Status:**" not in target_text
    assert unrelated.read_text(encoding="utf-8") == "# Task ID: 103\n# Status: done\n"
    assert any(cmd[:2] == ["task-master", "generate"] and "--output" in cmd for cmd in commands)


def test_taskmaster_generate_one_rejects_unrelated_dirty_task_file(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    tasks_dir = repo / ".taskmaster" / "tasks"
    tasks_dir.mkdir(parents=True)

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "TASKMASTER_TASKS_DIR", tasks_dir)

    commands = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False):
        commands.append(cmd)
        if cmd[:2] == ["git", "status"]:
            return FakeCompletedProcess(stdout=" M .taskmaster/tasks/task_103.txt\n")
        if cmd[:2] == ["task-master", "generate"]:  # pragma: no cover - should not run
            raise AssertionError("targeted generation should stop before broad generate")
        return FakeCompletedProcess(stdout="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(module.TaskError, match="Unrelated Taskmaster task files are dirty"):
        module.handle_taskmaster_generate_one(argparse.Namespace(task_id="104", dry_run=False))

    assert not any(cmd[:2] == ["task-master", "generate"] for cmd in commands)


def test_taskmaster_generate_one_rejects_missing_generated_task_file(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    tasks_dir = repo / ".taskmaster" / "tasks"
    tasks_dir.mkdir(parents=True)

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "TASKMASTER_TASKS_DIR", tasks_dir)

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False):
        if cmd[:2] == ["git", "status"]:
            return FakeCompletedProcess(stdout="")
        if cmd[:2] == ["task-master", "generate"]:
            return FakeCompletedProcess(stdout="")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(module.TaskError, match="Generated task file for task 104 not found"):
        module.handle_taskmaster_generate_one(argparse.Namespace(task_id="104", dry_run=False))


def test_serena_status_reports_project_and_codex_mcp_config(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    (repo / ".codex").mkdir(parents=True)
    (repo / ".serena" / "memories").mkdir(parents=True)
    (repo / ".serena" / "memories" / "2026-05-08_task15_serena.md").write_text("memory\n", encoding="utf-8")
    serena_args = [
        "--from",
        "git+https://github.com/oraios/serena@229fac066237f7156c8fe2a9fa7166f95715e0b3",
        "serena",
        "start-mcp-server",
        "--project-from-cwd",
    ]
    (repo / ".codex" / "config.toml").write_text(
        "[mcp_servers.serena]\n"
        'type = "stdio"\n'
        'command = "uvx"\n'
        f"args = {json.dumps(serena_args)}\n",
        encoding="utf-8",
    )
    (repo / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"serena": {"type": "stdio", "command": "uvx", "args": serena_args}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    report_file = repo / "reports" / "serena-status.txt"
    module.handle_serena_status(argparse.Namespace(strict=True, report_file=str(report_file)))

    output = capsys.readouterr().out
    report = report_file.read_text(encoding="utf-8")
    assert "Wrote Serena status report" in output
    assert "Serena integration status: OK" in report
    assert "Serena memory count: 1" in report
    assert ".mcp.json" in report


def test_serena_status_strict_rejects_missing_project_mcp_entry(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    (repo / ".codex").mkdir(parents=True)
    serena_args = [
        "--from",
        "git+https://github.com/oraios/serena@229fac066237f7156c8fe2a9fa7166f95715e0b3",
        "serena",
        "start-mcp-server",
        "--project-from-cwd",
    ]
    (repo / ".codex" / "config.toml").write_text(
        "[mcp_servers.serena]\n"
        'type = "stdio"\n'
        'command = "uvx"\n'
        f"args = {json.dumps(serena_args)}\n",
        encoding="utf-8",
    )
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    with pytest.raises(module.TaskError, match="Serena integration status failed"):
        module.handle_serena_status(argparse.Namespace(strict=True, report_file=None))


def test_taskmaster_health_reports_valid_full_graph(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    tasks_json = repo / ".taskmaster" / "tasks" / "tasks.json"
    tasks_json.parent.mkdir(parents=True)
    tasks_json.write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {"id": 1, "status": "done", "dependencies": [], "subtasks": []},
                        {
                            "id": 12,
                            "status": "in-progress",
                            "dependencies": [1],
                            "subtasks": [
                                {"id": 1, "status": "pending", "dependencies": []},
                                {"id": 2, "status": "pending", "dependencies": [1]},
                            ],
                        },
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "TASKMASTER_TASKS_JSON", tasks_json)

    report_file = repo / "reports" / "taskmaster-health.txt"
    module.handle_taskmaster_health(argparse.Namespace(tag=None, report_file=str(report_file)))

    output = capsys.readouterr().out
    assert "Taskmaster health: OK" in output
    assert "Tasks: 2" in output
    assert "Subtasks: 2" in output
    assert "Statuses: done=1, in-progress=1" in output
    assert "Invalid dependency refs: 0" in output
    assert "filtered-view dependency warnings" in report_file.read_text(encoding="utf-8")


def test_taskmaster_health_rejects_invalid_parent_dependency(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    tasks_json = repo / ".taskmaster" / "tasks" / "tasks.json"
    tasks_json.parent.mkdir(parents=True)
    tasks_json.write_text(
        json.dumps({"master": {"tasks": [{"id": 12, "status": "pending", "dependencies": [999], "subtasks": []}]}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "TASKMASTER_TASKS_JSON", tasks_json)

    with pytest.raises(module.TaskError, match="Taskmaster dependency health failed"):
        module.handle_taskmaster_health(argparse.Namespace(tag=None, report_file=None))


def test_handle_bootstrap_init_preserves_existing_config_and_policy(tmp_path) -> None:
    module = load_task_module()
    target = tmp_path / "existing-repo"
    (target / ".codex").mkdir(parents=True)
    (target / "ops" / "templates" / "metadata").mkdir(parents=True)
    existing_config = """
[repo_structure]
templates_root = "ops/templates"
sessions_root = "ops/sessions"
plans_root = "ops/plans"
plan_state_dir = ".ops/plan-state"
taskmaster_root = ".ops/taskmaster"
work_tracking_root = "ops/work-tracking"
reports_root = "ops/reports"
""".strip() + "\n"
    existing_policy = '{"version":"existing"}\n'
    (target / ".codex" / "config.toml").write_text(existing_config, encoding="utf-8")
    (target / "ops" / "templates" / "metadata" / "template-metadata-policy.json").write_text(existing_policy, encoding="utf-8")

    args = argparse.Namespace(
        target_dir=str(target),
        force=False,
        templates_root="ignored/templates",
        sessions_root=None,
        plans_root=None,
        plan_state_dir=None,
        taskmaster_root=None,
        work_tracking_root=None,
        reports_root=None,
        dry_run=False,
    )

    module.handle_bootstrap_init(args)

    assert (target / ".codex" / "config.toml").read_text(encoding="utf-8") == existing_config
    assert (target / "ops" / "templates" / "metadata" / "template-metadata-policy.json").read_text(encoding="utf-8") == existing_policy
    assert (target / "ops" / "sessions").is_dir()
    assert (target / "ops" / "plans").is_dir()
    assert (target / ".ops" / "plan-state").is_dir()
    assert (target / ".ops" / "taskmaster" / "tasks").is_dir()
    assert (target / "ops" / "work-tracking" / "active").is_dir()
    assert (target / "ops" / "reports" / "template-drift").is_dir()
    assert (target / "ops" / "reports" / "cost-tracking").is_dir()
    assert (target / "ops" / "reports" / "emergency-response").is_dir()


def test_handle_bootstrap_init_force_overwrites_existing_starter_files(tmp_path) -> None:
    module = load_task_module()
    target = tmp_path / "force-repo"
    (target / ".codex").mkdir(parents=True)
    (target / "templates" / "metadata").mkdir(parents=True)
    (target / ".codex" / "config.toml").write_text("[repo_structure]\ntemplates_root = \"legacy/templates\"\n", encoding="utf-8")
    (target / "templates" / "metadata" / "template-metadata-policy.json").write_text('{"legacy":true}\n', encoding="utf-8")

    args = argparse.Namespace(
        target_dir=str(target),
        force=True,
        templates_root=None,
        sessions_root=None,
        plans_root=None,
        plan_state_dir=None,
        taskmaster_root=None,
        work_tracking_root=None,
        reports_root=None,
        dry_run=False,
    )

    module.handle_bootstrap_init(args)

    config_text = (target / ".codex" / "config.toml").read_text(encoding="utf-8")
    policy_text = (target / "templates" / "metadata" / "template-metadata-policy.json").read_text(encoding="utf-8")
    assert 'templates_root = "templates"' in config_text
    assert '"required_keys"' in policy_text


def test_handle_bootstrap_init_supports_cross_project_repo_shapes(tmp_path) -> None:
    module = load_task_module()

    for name, shape in REPO_SHAPES.items():
        target = tmp_path / name
        args = argparse.Namespace(
            target_dir=str(target),
            force=False,
            templates_root=shape.roots["templates_root"],
            sessions_root=shape.roots["sessions_root"],
            plans_root=shape.roots["plans_root"],
            plan_state_dir=shape.roots["plan_state_dir"],
            taskmaster_root=shape.roots["taskmaster_root"],
            work_tracking_root=shape.roots["work_tracking_root"],
            reports_root=shape.roots["reports_root"],
            dry_run=False,
        )

        module.handle_bootstrap_init(args)

        assert (target / ".codex" / "config.toml").exists()
        assert (target / shape.roots["templates_root"] / "metadata" / "template-metadata-policy.json").exists()
        assert (target / shape.roots["templates_root"] / "metadata" / "template-monitoring-policy.json").exists()
        assert (target / shape.roots["templates_root"] / "metadata" / "template-performance-policy.json").exists()
        assert (target / shape.roots["templates_root"] / "metadata" / "template-cost-policy.json").exists()
        assert (target / shape.roots["templates_root"] / "metadata" / "emergency-response-policy.json").exists()
        assert (target / shape.roots["sessions_root"]).is_dir()
        assert (target / shape.roots["plans_root"]).is_dir()
        assert (target / shape.roots["taskmaster_root"] / "tasks").is_dir()
        assert (target / shape.roots["work_tracking_root"] / "active").is_dir()
        assert (target / shape.roots["reports_root"] / "template-metrics").is_dir()
        assert (target / shape.roots["reports_root"] / "template-monitoring").is_dir()
        assert (target / shape.roots["reports_root"] / "phase0-scanner-validation").is_dir()
        assert (target / shape.roots["reports_root"] / "template-performance").is_dir()
        assert (target / shape.roots["reports_root"] / "cost-tracking").is_dir()
        assert (target / shape.roots["reports_root"] / "migration-health").is_dir()
