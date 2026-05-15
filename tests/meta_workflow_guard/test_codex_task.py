"""Unit tests for codex-task wizard helpers."""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import os
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


def _write_repo_config(repo: Path, templates_root: str = "templates") -> None:
    config_dir = repo / ".codex"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        "[repo_structure]\n"
        f'templates_root = "{templates_root}"\n'
        'sessions_root = "sessions"\n'
        'plans_root = "plans"\n'
        'plan_state_dir = ".plan_state"\n'
        'taskmaster_root = ".taskmaster"\n'
        'work_tracking_root = "docs/ai/work-tracking"\n'
        'reports_root = "reports"\n',
        encoding="utf-8",
    )


def _write_template_doc(path: Path, frontmatter: str, body: str = "# Template\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter.strip()}\n---\n\n{body}", encoding="utf-8")


def _write_template_registry(repo: Path, templates_root: str, entries: list[dict[str, object]]) -> None:
    registry_path = repo / templates_root / "registry" / "index.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def test_build_parser_accepts_wizard_kickoff() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["wizard", "kickoff", "--task", "96", "--slug", "interactive-template-wizard"])
    assert args.command == "wizard"
    assert args.subcommand == "kickoff"
    assert args.task == "96"


def test_build_parser_accepts_migration_archive() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["migration", "archive", "--query", "scanner"])
    assert args.command == "migration"
    assert args.subcommand == "archive"
    assert args.query == "scanner"


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


def test_build_parser_accepts_operations_runbook() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "operations",
        "runbook",
        "--label",
        "task57",
        "--report-file",
        "reports/operations.json",
        "--runbook-file",
        "reports/operations.md",
    ])
    assert args.command == "operations"
    assert args.subcommand == "runbook"
    assert args.label == "task57"
    assert args.report_file == "reports/operations.json"
    assert args.runbook_file == "reports/operations.md"


def test_build_parser_accepts_phase3_automation_review() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "automation",
        "phase3-review",
        "--label",
        "task56",
        "--report-file",
        "reports/phase3.json",
        "--runbook-file",
        "reports/phase3.md",
    ])
    assert args.command == "automation"
    assert args.subcommand == "phase3-review"
    assert args.label == "task56"
    assert args.report_file == "reports/phase3.json"
    assert args.runbook_file == "reports/phase3.md"


def test_build_parser_accepts_phase4_documentation_review() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "documentation",
        "phase4-review",
        "--label",
        "task63",
        "--report-file",
        "reports/phase4.json",
        "--runbook-file",
        "reports/phase4.md",
    ])
    assert args.command == "documentation"
    assert args.subcommand == "phase4-review"
    assert args.label == "task63"
    assert args.report_file == "reports/phase4.json"
    assert args.runbook_file == "reports/phase4.md"


def test_build_parser_accepts_knowledge_transfer_review() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "knowledge",
        "transfer-review",
        "--label",
        "task54",
        "--report-file",
        "reports/knowledge.json",
        "--runbook-file",
        "reports/knowledge.md",
    ])
    assert args.command == "knowledge"
    assert args.subcommand == "transfer-review"
    assert args.label == "task54"
    assert args.report_file == "reports/knowledge.json"
    assert args.runbook_file == "reports/knowledge.md"


def test_build_parser_accepts_knowledge_base() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "knowledge",
        "base",
        "--label",
        "task75",
        "--query",
        "runtime contract",
        "--max-items",
        "12",
        "--report-file",
        "reports/knowledge-base.json",
        "--runbook-file",
        "reports/knowledge-base.md",
    ])
    assert args.command == "knowledge"
    assert args.subcommand == "base"
    assert args.label == "task75"
    assert args.query == "runtime contract"
    assert args.max_items == 12
    assert args.report_file == "reports/knowledge-base.json"
    assert args.runbook_file == "reports/knowledge-base.md"


def test_build_parser_accepts_success_metrics() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "success",
        "metrics",
        "--label",
        "task67",
        "--strict",
        "--report-file",
        "reports/success.json",
        "--runbook-file",
        "reports/success.md",
    ])
    assert args.command == "success"
    assert args.subcommand == "metrics"
    assert args.label == "task67"
    assert args.strict is True
    assert args.report_file == "reports/success.json"
    assert args.runbook_file == "reports/success.md"


def test_build_parser_accepts_stakeholder_report() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "stakeholder",
        "report",
        "--label",
        "task73",
        "--strict",
        "--report-file",
        "reports/stakeholder.json",
        "--runbook-file",
        "reports/stakeholder.md",
    ])
    assert args.command == "stakeholder"
    assert args.subcommand == "report"
    assert args.label == "task73"
    assert args.strict is True
    assert args.report_file == "reports/stakeholder.json"
    assert args.runbook_file == "reports/stakeholder.md"


def test_build_parser_accepts_enhancement_phase5_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "enhancement",
        "phase5-plan",
        "--label",
        "task69",
        "--strict",
        "--report-file",
        "reports/enhancement.json",
        "--runbook-file",
        "reports/enhancement.md",
    ])
    assert args.command == "enhancement"
    assert args.subcommand == "phase5-plan"
    assert args.label == "task69"
    assert args.strict is True
    assert args.report_file == "reports/enhancement.json"
    assert args.runbook_file == "reports/enhancement.md"


def test_build_parser_accepts_enhancement_continuous_improvement() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "enhancement",
        "continuous-improvement",
        "--label",
        "task77",
        "--strict",
        "--report-file",
        "reports/continuous.json",
        "--runbook-file",
        "reports/continuous.md",
    ])
    assert args.command == "enhancement"
    assert args.subcommand == "continuous-improvement"
    assert args.label == "task77"
    assert args.strict is True
    assert args.report_file == "reports/continuous.json"
    assert args.runbook_file == "reports/continuous.md"


def test_build_parser_accepts_celebration_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "celebration",
        "plan",
        "--label",
        "task76",
        "--strict",
        "--report-file",
        "reports/celebration.json",
        "--runbook-file",
        "reports/celebration.md",
    ])
    assert args.command == "celebration"
    assert args.subcommand == "plan"
    assert args.label == "task76"
    assert args.strict is True
    assert args.report_file == "reports/celebration.json"
    assert args.runbook_file == "reports/celebration.md"


def test_build_parser_accepts_feedback_collection_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "feedback",
        "collection-plan",
        "--label",
        "task59",
        "--strict",
        "--report-file",
        "reports/feedback.json",
        "--runbook-file",
        "reports/feedback.md",
    ])
    assert args.command == "feedback"
    assert args.subcommand == "collection-plan"
    assert args.label == "task59"
    assert args.strict is True
    assert args.report_file == "reports/feedback.json"
    assert args.runbook_file == "reports/feedback.md"


def test_build_parser_accepts_cleanup_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "cleanup",
        "plan",
        "--label",
        "task64",
        "--strict",
        "--report-file",
        "reports/cleanup.json",
        "--runbook-file",
        "reports/cleanup.md",
    ])
    assert args.command == "cleanup"
    assert args.subcommand == "plan"
    assert args.label == "task64"
    assert args.strict is True
    assert args.report_file == "reports/cleanup.json"
    assert args.runbook_file == "reports/cleanup.md"


def test_build_parser_accepts_maintenance_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "maintenance",
        "plan",
        "--label",
        "task70",
        "--strict",
        "--report-file",
        "reports/maintenance.json",
        "--runbook-file",
        "reports/maintenance.md",
    ])
    assert args.command == "maintenance"
    assert args.subcommand == "plan"
    assert args.label == "task70"
    assert args.strict is True
    assert args.report_file == "reports/maintenance.json"
    assert args.runbook_file == "reports/maintenance.md"


def test_build_parser_accepts_deployment_readiness() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "deployment",
        "readiness",
        "--label",
        "task80",
        "--strict",
        "--report-file",
        "reports/deployment.json",
        "--runbook-file",
        "reports/deployment.md",
    ])
    assert args.command == "deployment"
    assert args.subcommand == "readiness"
    assert args.label == "task80"
    assert args.strict is True
    assert args.report_file == "reports/deployment.json"
    assert args.runbook_file == "reports/deployment.md"


def test_build_parser_accepts_deprecation_review() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "deprecation",
        "review",
        "--label",
        "task66",
        "--today",
        "2026-05-13",
        "--report-file",
        "reports/deprecation.json",
        "--runbook-file",
        "reports/deprecation.md",
    ])
    assert args.command == "deprecation"
    assert args.subcommand == "review"
    assert args.label == "task66"
    assert args.today == "2026-05-13"
    assert args.report_file == "reports/deprecation.json"
    assert args.runbook_file == "reports/deprecation.md"


def test_build_parser_accepts_incident_post_mortem() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "incident",
        "post-mortem",
        "--summary",
        "Guard regression after merge",
        "--severity",
        "P1",
        "--timeline",
        "2026-05-13T10:00:00+02:00|Detection|Guard failed|reports/guard.txt",
        "--root-cause",
        "workflow|Evidence was missing",
        "--action-item",
        "foundation_maintainer|Add test|open|2026-05-20",
        "--prevention",
        "Run audit before guard|python3 scripts/codex-task work-tracking audit",
        "--lesson",
        "Capture evidence before plan sync",
        "--report-file",
        "reports/post-mortem.json",
        "--runbook-file",
        "reports/post-mortem.md",
    ])
    assert args.command == "incident"
    assert args.subcommand == "post-mortem"
    assert args.summary == "Guard regression after merge"
    assert args.severity == "P1"
    assert args.timeline == ["2026-05-13T10:00:00+02:00|Detection|Guard failed|reports/guard.txt"]
    assert args.report_file == "reports/post-mortem.json"
    assert args.runbook_file == "reports/post-mortem.md"


def test_build_parser_accepts_migration_metrics() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["migration", "metrics", "--label", "task-55"])
    assert args.command == "migration"
    assert args.subcommand == "metrics"
    assert args.label == "task-55"


def test_build_parser_accepts_post_migration_monitoring() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["migration", "monitoring", "--label", "task-60"])
    assert args.command == "migration"
    assert args.subcommand == "monitoring"
    assert args.label == "task-60"


def test_build_parser_accepts_template_bundle_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "template",
        "bundle-plan",
        "--template",
        "engine-core-ultrathink-protocol",
        "--target-dir",
        "/tmp/template-target",
        "--label",
        "task46",
    ])
    assert args.command == "template"
    assert args.subcommand == "bundle-plan"
    assert args.templates == ["engine-core-ultrathink-protocol"]
    assert args.target_dir == "/tmp/template-target"
    assert args.label == "task46"


def test_build_parser_accepts_template_usage_analytics() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "template",
        "usage-analytics",
        "--label",
        "task51",
        "--include-archive",
        "--max-items",
        "5",
        "--max-examples",
        "2",
        "--report-file",
        "reports/usage.json",
        "--runbook-file",
        "reports/usage.md",
    ])
    assert args.command == "template"
    assert args.subcommand == "usage-analytics"
    assert args.label == "task51"
    assert args.include_archive is True
    assert args.max_items == 5
    assert args.max_examples == 2


def test_build_parser_accepts_template_quality_score() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "template",
        "quality-score",
        "--label",
        "task65",
        "--strict",
        "--report-file",
        "reports/template-quality/latest.json",
        "--runbook-file",
        "reports/template-quality/latest.md",
    ])
    assert args.command == "template"
    assert args.subcommand == "quality-score"
    assert args.label == "task65"
    assert args.strict is True
    assert args.report_file == "reports/template-quality/latest.json"
    assert args.runbook_file == "reports/template-quality/latest.md"


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


def test_build_parser_accepts_recovery_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "recovery",
        "plan",
        "--error-class",
        "transient",
        "--summary",
        "Network timeout while checking PR status",
        "--label",
        "pr-timeout",
        "--max-attempts",
        "3",
        "--base-delay-seconds",
        "10",
        "--max-delay-seconds",
        "30",
    ])
    assert args.command == "recovery"
    assert args.subcommand == "plan"
    assert args.error_class == "transient"
    assert args.summary == "Network timeout while checking PR status"
    assert args.label == "pr-timeout"
    assert args.max_attempts == 3
    assert args.base_delay_seconds == 10
    assert args.max_delay_seconds == 30


def test_build_parser_accepts_security_audit() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "security",
        "audit",
        "--summary",
        "Task 50 foundation security audit",
        "--label",
        "task50-security",
        "--security-report",
        "reports/security.json",
        "--phase0-report",
        "reports/phase0.json",
    ])
    assert args.command == "security"
    assert args.subcommand == "audit"
    assert args.summary == "Task 50 foundation security audit"
    assert args.label == "task50-security"
    assert args.security_report == "reports/security.json"
    assert args.phase0_report == "reports/phase0.json"


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


def test_build_parser_accepts_rollout_experiment_plan() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "rollout",
        "experiment-plan",
        "--label",
        "foundation-experiment",
        "--control",
        "current-foundation",
        "--variant",
        "candidate-a",
        "--variant",
        "candidate-b",
        "--error-threshold-pct",
        "4.5",
        "--report-file",
        "reports/experiment.json",
        "--runbook-file",
        "reports/experiment.md",
        "--dry-run",
    ])
    assert args.command == "rollout"
    assert args.subcommand == "experiment-plan"
    assert args.label == "foundation-experiment"
    assert args.control == "current-foundation"
    assert args.variant == ["candidate-a", "candidate-b"]
    assert args.error_threshold_pct == 4.5
    assert args.report_file == "reports/experiment.json"
    assert args.runbook_file == "reports/experiment.md"
    assert args.dry_run is True


def test_build_parser_accepts_change_advisory() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args([
        "change",
        "advisory",
        "--summary",
        "Breaking template policy update",
        "--task",
        "44",
        "--path",
        "templates/example.md",
        "--previous-version",
        "1.0.0",
        "--current-version",
        "2.0.0",
        "--report-file",
        "reports/change-advisory.json",
        "--runbook-file",
        "reports/change-advisory.md",
        "--dry-run",
    ])
    assert args.command == "change"
    assert args.subcommand == "advisory"
    assert args.summary == "Breaking template policy update"
    assert args.task == "44"
    assert args.paths == ["templates/example.md"]
    assert args.previous_version == "1.0.0"
    assert args.current_version == "2.0.0"
    assert args.report_file == "reports/change-advisory.json"
    assert args.runbook_file == "reports/change-advisory.md"
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


def _write_migration_metrics_inputs(repo: Path, *, clean: bool = False) -> tuple[Path, Path, Path]:
    reports = repo / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    baseline = reports / "baseline_summary.json"
    roadmap = reports / "migration-roadmap.json"
    security = reports / "security_validation.json"
    baseline.write_text(
        json.dumps(
            {
                "metadata": {
                    "scan_timestamp": "2026-05-13T10:00:00",
                    "scanner": "baseline_summary",
                    "stats": {},
                },
                "data": {
                    "generated_at": "2026-05-13T10:00:00",
                    "metrics": {
                        "migration_percentage": 100.0 if clean else 37.5,
                        "pending_migration": 0 if clean else 6,
                        "broken_references": 0 if clean else 2,
                        "circular_dependencies": 0 if clean else 1,
                        "duplicate_count": 0 if clean else 4,
                        "total_fixes": 0 if clean else 7,
                    },
                    "outputs": {
                        "migration_status": {
                            "path": "scripts/template-ssot-scanner/output/data/migration_status.json",
                            "scanner": "migration_detector",
                            "scan_timestamp": "2026-05-13T09:59:00",
                        }
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    roadmap.write_text(
        json.dumps(
            {
                "metadata": {"scanner": "migration_roadmap", "scanner_version": "1.0.0"},
                "data": {
                    "generated_at": "2026-05-13T10:01:00",
                    "migration_roadmap_version": "1.0.0",
                    "summary_metrics": {"pending_migration": 0 if clean else 6},
                    "priority_counts": {"critical": 0 if clean else 1, "high": 2},
                    "category_counts": {"references": 1, "migration": 2},
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
                            "finding_count": 2,
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
    security.write_text(
        json.dumps(
            {
                "metadata": {
                    "scan_timestamp": "2026-05-13T10:02:00",
                    "scanner": "security_validator",
                    "stats": {"findings": 0 if clean else 1},
                },
                "data": {
                    "summary": {
                        "total_findings": 0 if clean else 1,
                        "severity_counts": {} if clean else {"error": 1},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return baseline, roadmap, security


def test_build_migration_metrics_report_summarizes_baseline_roadmap_and_security(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    baseline, roadmap, security = _write_migration_metrics_inputs(repo)

    report = module._build_migration_metrics_report(
        argparse.Namespace(
            label="task-55",
            baseline_summary=str(baseline),
            roadmap=str(roadmap),
            security_report=str(security),
            max_roadmap_items=1,
        )
    )

    assert report["mode"] == "static-file-backed-migration-metrics"
    assert report["executes_external_actions"] is False
    assert report["aggregate_status"] == "fail"
    assert report["summary"]["failures"] >= 3
    kpis = {kpi["id"]: kpi for kpi in report["kpis"]}
    assert kpis["migration-completion"]["value"] == 37.5
    assert kpis["broken-references"]["status"] == "fail"
    assert kpis["security-findings"]["status"] == "fail"
    assert kpis["roadmap-critical-items"]["value"] == 1
    assert report["roadmap"]["first_items"][0]["id"] == "critical-references-001"
    assert "No time-series database is read or written." in report["non_goals"]


def test_migration_metrics_report_handles_missing_optional_inputs(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    baseline, _, _ = _write_migration_metrics_inputs(repo, clean=True)

    report = module._build_migration_metrics_report(
        argparse.Namespace(
            label="task-55",
            baseline_summary=str(baseline),
            roadmap=None,
            security_report=str(repo / "missing-security.json"),
            max_roadmap_items=5,
        )
    )

    assert report["aggregate_status"] == "warn"
    kpis = {kpi["id"]: kpi for kpi in report["kpis"]}
    assert kpis["security-findings"]["status"] == "missing"
    assert kpis["roadmap-critical-items"]["status"] == "missing"
    assert report["roadmap"] is None


def test_render_migration_metrics_runbook_lists_kpis_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    baseline, roadmap, security = _write_migration_metrics_inputs(repo)
    report = module._build_migration_metrics_report(
        argparse.Namespace(
            label="task-55",
            baseline_summary=str(baseline),
            roadmap=str(roadmap),
            security_report=str(security),
            max_roadmap_items=1,
        )
    )

    runbook = module._render_migration_metrics_runbook(report)

    assert "# Migration Metrics Collection" in runbook
    assert "Broken references" in runbook
    assert "Critical roadmap items" in runbook
    assert "No metric agent, time-series database, live dashboard" in runbook
    assert "git reset --hard" not in runbook


def test_handle_migration_metrics_writes_report_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    baseline, roadmap, security = _write_migration_metrics_inputs(repo)
    report = repo / "reports" / "migration-metrics.json"
    runbook = repo / "reports" / "migration-metrics.md"

    module.handle_migration_metrics(
        argparse.Namespace(
            label="task-55",
            baseline_summary=str(baseline),
            roadmap=str(roadmap),
            security_report=str(security),
            max_roadmap_items=1,
            report_file=str(report),
            runbook_file=str(runbook),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote migration metrics report to reports/migration-metrics.json" in output
    assert "Wrote migration metrics runbook to reports/migration-metrics.md" in output
    assert json.loads(report.read_text(encoding="utf-8"))["aggregate_status"] == "fail"
    assert "Migration Metrics Collection" in runbook.read_text(encoding="utf-8")


def test_handle_migration_metrics_strict_fails_after_writing(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    baseline, roadmap, security = _write_migration_metrics_inputs(repo)
    report = repo / "reports" / "migration-metrics.json"

    with pytest.raises(module.TaskError, match="aggregate status is fail"):
        module.handle_migration_metrics(
            argparse.Namespace(
                label="task-55",
                baseline_summary=str(baseline),
                roadmap=str(roadmap),
                security_report=str(security),
                max_roadmap_items=1,
                report_file=str(report),
                runbook_file=None,
                dry_run=False,
                strict=True,
            )
        )

    assert report.exists()


def _write_post_migration_monitoring_inputs(repo: Path, metrics_status: str = "fail", health_status: str = "warn"):
    metrics = repo / "reports" / "migration-metrics.json"
    health = repo / "reports" / "migration-health" / "latest.json"
    metrics.parent.mkdir(parents=True, exist_ok=True)
    health.parent.mkdir(parents=True, exist_ok=True)
    metrics.write_text(
        json.dumps(
            {
                "created_at": "2026-05-13T14:00:00+02:00",
                "aggregate_status": metrics_status,
                "summary": {"total_kpis": 2, "failures": 1 if metrics_status == "fail" else 0},
                "kpis": [
                    {
                        "id": "migration-completion",
                        "title": "Migration completion",
                        "status": "pass",
                        "severity": "info",
                        "value": 100.0,
                        "target": "100",
                        "evidence": "baseline_summary.json",
                    },
                    {
                        "id": "broken-references",
                        "title": "Broken references",
                        "status": metrics_status,
                        "severity": "error" if metrics_status == "fail" else "info",
                        "value": 4 if metrics_status == "fail" else 0,
                        "target": "0",
                        "evidence": "baseline_summary.json",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    health.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-13T14:05:00+02:00",
                "status": health_status,
                "summary": {"total": 2, "warnings": 1 if health_status == "warn" else 0, "errors": 0},
                "components": [
                    {
                        "id": "metrics",
                        "title": "Template metrics dashboard",
                        "status": "pass",
                        "severity": "info",
                        "evidence": "reports/template-metrics/latest.json",
                        "message": "Loaded.",
                    },
                    {
                        "id": "monitoring",
                        "title": "Template monitoring",
                        "status": health_status,
                        "severity": "warning" if health_status == "warn" else "info",
                        "evidence": "reports/template-monitoring/latest.json",
                        "message": "Review warning.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return metrics, health


def test_build_post_migration_monitoring_report_combines_metrics_and_health(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    metrics, health = _write_post_migration_monitoring_inputs(repo)

    report = module._build_post_migration_monitoring_report(
        argparse.Namespace(
            label="task-60",
            metrics_report=str(metrics),
            migration_health_report=str(health),
            max_items=5,
        )
    )

    assert report["mode"] == "static-file-backed-post-migration-monitoring"
    assert report["executes_external_actions"] is False
    assert report["aggregate_status"] == "fail"
    assert report["summary"]["available_inputs"] == 2
    assert report["inputs"]["migration_metrics"]["items"][1]["title"] == "Broken references"
    assert report["inputs"]["migration_health"]["items"][1]["title"] == "Template monitoring"
    assert {action["id"] for action in report["required_actions"]} == {
        "resolve-failing-migration-kpis",
        "review-warning-migration-health",
    }
    assert "No scheduler, daemon, cron job, or background worker is installed." in report["non_goals"]


def test_post_migration_monitoring_report_handles_missing_inputs(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    report = module._build_post_migration_monitoring_report(
        argparse.Namespace(
            label="task-60",
            metrics_report=None,
            migration_health_report=str(repo / "reports" / "migration-health" / "latest.json"),
            max_items=5,
        )
    )

    assert report["aggregate_status"] == "warn"
    assert report["summary"]["available_inputs"] == 0
    assert report["inputs"]["migration_metrics"]["status"] == "missing"
    assert report["inputs"]["migration_health"]["status"] == "missing"
    assert {action["id"] for action in report["required_actions"]} == {
        "generate-migration-metrics",
        "generate-migration-health",
    }


def test_render_post_migration_monitoring_runbook_lists_cadences_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    metrics, health = _write_post_migration_monitoring_inputs(repo, metrics_status="pass", health_status="pass")
    report = module._build_post_migration_monitoring_report(
        argparse.Namespace(
            label="task-60",
            metrics_report=str(metrics),
            migration_health_report=str(health),
            max_items=5,
        )
    )

    runbook = module._render_post_migration_monitoring_runbook(report)

    assert "# Post-Migration Monitoring" in runbook
    assert "Weekly scanner and migration-health refresh" in runbook
    assert "Monthly usage and cost review" in runbook
    assert "No scheduler, daemon, cron job" in runbook
    assert "git reset --hard" not in runbook


def test_handle_post_migration_monitoring_writes_report_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    metrics, health = _write_post_migration_monitoring_inputs(repo)
    report = repo / "reports" / "post-migration-monitoring.json"
    runbook = repo / "reports" / "post-migration-monitoring.md"

    module.handle_post_migration_monitoring(
        argparse.Namespace(
            label="task-60",
            metrics_report=str(metrics),
            migration_health_report=str(health),
            max_items=5,
            report_file=str(report),
            runbook_file=str(runbook),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote post-migration monitoring report to reports/post-migration-monitoring.json" in output
    assert "Wrote post-migration monitoring runbook to reports/post-migration-monitoring.md" in output
    assert json.loads(report.read_text(encoding="utf-8"))["aggregate_status"] == "fail"
    assert "Post-Migration Monitoring" in runbook.read_text(encoding="utf-8")


def test_handle_post_migration_monitoring_strict_fails_after_writing(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    metrics, health = _write_post_migration_monitoring_inputs(repo)
    report = repo / "reports" / "post-migration-monitoring.json"

    with pytest.raises(module.TaskError, match="aggregate status is fail"):
        module.handle_post_migration_monitoring(
            argparse.Namespace(
                label="task-60",
                metrics_report=str(metrics),
                migration_health_report=str(health),
                max_items=5,
                report_file=str(report),
                runbook_file=None,
                dry_run=False,
                strict=True,
            )
        )

    assert report.exists()


def _patch_migration_archive_state(module, monkeypatch, repo: Path) -> None:
    _write_repo_config(repo, "templates")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "PLANS_DIR", repo / "plans")
    monkeypatch.setattr(module, "datetime", FixedDatetime)


def _write_migration_archive_fixture(repo: Path) -> None:
    archive = repo / "docs" / "ai" / "work-tracking" / "archive" / "20260510-task38-phase1-reference-remediation-COMPLETED"
    archive.mkdir(parents=True)
    (archive / "TRACKER.md").write_text(
        "# Tracker\n\n- [S:20260510|W:task38-phase1-reference-remediation|H:scanner|E:reports] Scanner reference remediation completed.\n",
        encoding="utf-8",
    )
    (archive / "DECISIONS.md").write_text(
        "# Decisions\n\n- 2026-05-10 — Keep scanner reference fixes as migration evidence.\n",
        encoding="utf-8",
    )
    (archive / "FINDINGS.md").write_text(
        "# Findings\n\n- 2026-05-10 — Broken references were remediated with scanner evidence.\n",
        encoding="utf-8",
    )
    (archive / "HANDOFF.md").write_text(
        "# Handoff\n\n- Migration reference remediation is complete and archived.\n",
        encoding="utf-8",
    )
    report_dir = archive / "reports" / "phase1-reference-remediation"
    report_dir.mkdir(parents=True)
    (report_dir / "guard.txt").write_text("Guard passed\n", encoding="utf-8")

    reports = repo / "reports" / "migration-health"
    reports.mkdir(parents=True)
    (reports / "README.md").write_text("# Migration Health\n\nMigration health reports.\n", encoding="utf-8")
    scanner = repo / "scripts" / "template-ssot-scanner"
    (scanner / "output" / "data").mkdir(parents=True)
    (scanner / "output" / "scripts").mkdir(parents=True)
    (scanner / "migration_roadmap.py").write_text("# migration roadmap scanner tool\n", encoding="utf-8")
    (scanner / "output" / "data" / "baseline_summary.json").write_text('{"data": {"metrics": {}}}\n', encoding="utf-8")
    (scanner / "output" / "scripts" / "archive_duplicates.sh").write_text("#!/usr/bin/env bash\n# archive duplicate templates\n", encoding="utf-8")

    plans = repo / "plans"
    plans.mkdir(parents=True)
    (plans / "2026-05-10-task38-phase1-reference-remediation.md").write_text(
        "# Plan\n\nMigration reference remediation plan.\n",
        encoding="utf-8",
    )
    tasks = repo / ".taskmaster" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "task_038.txt").write_text(
        "# Task ID: 38\n# Title: Phase 1 Reference Remediation\nScanner migration fixes.\n",
        encoding="utf-8",
    )
    memories = repo / ".serena" / "memories"
    memories.mkdir(parents=True)
    (memories / "2026-05-10_task38_phase1_reference_remediation.md").write_text(
        "# Memory\n\nMigration scanner reference remediation complete.\n",
        encoding="utf-8",
    )


def test_build_migration_archive_report_indexes_canonical_artifacts(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_migration_archive_state(module, monkeypatch, repo)
    _write_migration_archive_fixture(repo)

    report = module._build_migration_archive_report(
        argparse.Namespace(label="task-71", query=None, max_items=25)
    )

    assert report["mode"] == "static-migration-archive-index"
    assert report["executes_external_actions"] is False
    assert report["summary"]["completed_work"] == 1
    assert report["summary"]["decision_records"] == 1
    assert report["summary"]["lessons_learned_candidates"] >= 1
    assert report["timeline"][0]["task_id"] == "38"
    assert any(entry["path"].endswith("migration_roadmap.py") for entry in report["sections"]["tools_and_outputs"])
    assert "No files are moved" in report["non_goals"][0]


def test_migration_archive_query_returns_matching_search_results(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_migration_archive_state(module, monkeypatch, repo)
    _write_migration_archive_fixture(repo)

    report = module._build_migration_archive_report(
        argparse.Namespace(label="task-71", query="reference remediation", max_items=25)
    )

    assert report["query"] == "reference remediation"
    assert report["summary"]["search_results"] >= 1
    assert all("reference" in json.dumps(entry).lower() for entry in report["search_results"])
    assert all("remediation" in json.dumps(entry).lower() for entry in report["search_results"])


def test_render_migration_archive_runbook_lists_timeline_and_search(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_migration_archive_state(module, monkeypatch, repo)
    _write_migration_archive_fixture(repo)
    report = module._build_migration_archive_report(
        argparse.Namespace(label="task-71", query="scanner", max_items=25)
    )

    runbook = module._render_migration_archive_runbook(report)

    assert "# Migration Archive" in runbook
    assert "Migration Timeline" in runbook
    assert "Search Results" in runbook
    assert "Task38 Phase1 Reference Remediation" in runbook
    assert "static archive index" in runbook
    assert "git reset --hard" not in runbook


def test_handle_migration_archive_writes_report_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_migration_archive_state(module, monkeypatch, repo)
    _write_migration_archive_fixture(repo)
    report = repo / "reports" / "migration-archive" / "latest.json"
    runbook = repo / "reports" / "migration-archive" / "latest.md"

    module.handle_migration_archive(
        argparse.Namespace(
            label="task-71",
            query=None,
            max_items=25,
            report_file=str(report),
            runbook_file=str(runbook),
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote migration archive report to reports/migration-archive/latest.json" in output
    assert "Wrote migration archive runbook to reports/migration-archive/latest.md" in output
    assert json.loads(report.read_text(encoding="utf-8"))["summary"]["completed_work"] == 1
    assert "Migration Archive" in runbook.read_text(encoding="utf-8")


def _patch_operational_runbook_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-57-operational-runbook"
        if args == ["rev-parse", "HEAD"]:
            return "op57abc"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-13-007-task57-operational-runbook.md"},
            "current_plan": {"resolved": "plans/2026-05-13-task57-operational-runbook.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260513-task57-operational-runbook-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_refs": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 7})


def test_build_operational_runbook_composes_procedures_and_state(monkeypatch) -> None:
    module = load_task_module()
    _patch_operational_runbook_snapshots(module, monkeypatch)

    report = module._build_operational_runbook(argparse.Namespace(label="task57"))

    assert report["mode"] == "non-destructive-operational-runbook"
    assert report["executes_actions"] is False
    assert report["current_state"]["git"]["branch"] == "feat/task-57-operational-runbook"
    assert report["procedure_count"] == len(report["procedures"])
    assert {procedure["id"] for procedure in report["procedures"]} >= {
        "daily-start",
        "weekly-maintenance",
        "monthly-review",
        "incident-response",
        "validation-signoff",
    }
    assert any("wizard kickoff" in command for command in report["related_helpers"].values())
    assert "No scheduler, daemon, cron job, or background worker is installed." in report["non_goals"]


def test_render_operational_runbook_names_cadences_escalation_and_non_goals(monkeypatch) -> None:
    module = load_task_module()
    _patch_operational_runbook_snapshots(module, monkeypatch)
    report = module._build_operational_runbook(argparse.Namespace(label="task57"))

    runbook = module._render_operational_runbook(report)

    assert "# Operational Runbook" in runbook
    assert "Daily session start" in runbook
    assert "Weekly static telemetry refresh" in runbook
    assert "Monthly backlog, cost, and adoption review" in runbook
    assert "Incident, recovery, and emergency response" in runbook
    assert "Role-Based Escalation" in runbook
    assert "`emergency_approver`" in runbook
    assert "python3 scripts/codex-task validation final-suite" in runbook
    assert "No scheduler, notification, ticket, dashboard update, deployment, rollback, reset, cleanup, or external incident action was executed by this runbook." in runbook
    assert "git reset --hard" not in runbook


def test_handle_operational_runbook_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_operational_runbook_snapshots(module, monkeypatch)

    report = repo / "reports" / "operations.json"
    runbook = repo / "reports" / "operations.md"
    args = argparse.Namespace(
        label="task57",
        report_file=str(report.relative_to(repo)),
        runbook_file=str(runbook.relative_to(repo)),
        dry_run=False,
    )

    module.handle_operational_runbook(args)

    output = capsys.readouterr().out
    assert "Wrote operational runbook report to reports/operations.json" in output
    assert "Wrote operational runbook to reports/operations.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task57"
    assert payload["executes_actions"] is False
    assert payload["procedure_count"] >= 8
    assert "# Operational Runbook" in runbook.read_text(encoding="utf-8")


def _patch_incident_post_mortem_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-72-post-mortem-process"
        if args == ["rev-parse", "HEAD"]:
            return "pm72abc"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-13-010-task72-post-mortem-process.md"},
            "current_plan": {"resolved": "plans/2026-05-13-task72-post-mortem-process.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260513-task72-post-mortem-process-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_refs": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 10})


def _incident_post_mortem_args(**overrides):
    values = {
        "summary": "Guard regression after merge",
        "severity": "P1",
        "impact": "Guard blocked closeout until evidence was repaired",
        "detection_source": "codex-guard",
        "label": "guard-regression",
        "timeline": [
            "2026-05-13T10:00:00+02:00|Detection|Guard failed during validation|reports/guard-fail.txt",
            "2026-05-13T10:45:00+02:00|Recovery|Tracker evidence repaired|reports/guard-pass.txt",
        ],
        "root_cause": ["workflow|Tracker referenced evidence before it existed"],
        "contributing_factor": ["Plan sync ran before final report capture"],
        "action_item": [
            "foundation_maintainer|Add regression coverage for missing evidence links|open|2026-05-20",
            "active_agent|Record final guard evidence in tracker|done|2026-05-13",
        ],
        "prevention": [
            "Run work-tracking audit before guard|python3 scripts/codex-task work-tracking audit|open",
        ],
        "lesson": ["Capture report files before marking plan-step-verify complete"],
        "report_file": None,
        "runbook_file": None,
        "dry_run": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_build_incident_post_mortem_composes_packet_and_metrics(monkeypatch) -> None:
    module = load_task_module()
    _patch_incident_post_mortem_snapshots(module, monkeypatch)

    report = module._build_incident_post_mortem(_incident_post_mortem_args())

    assert report["mode"] == "static-incident-post-mortem-packet"
    assert report["executes_actions"] is False
    assert report["incident"]["id"] == "20260424-150313-guard-regression"
    assert report["incident"]["severity"] == "P1"
    assert report["current_state"]["git"]["branch"] == "feat/task-72-post-mortem-process"
    assert report["metrics"]["timeline_entries"] == 2
    assert report["metrics"]["action_item_count"] == 2
    assert report["metrics"]["open_action_item_count"] == 1
    assert report["metrics"]["prevention_measure_count"] == 1
    assert report["metrics"]["detection_to_recovery_minutes"] == 45
    assert "python3 scripts/codex-task recovery plan" in report["recommended_helpers"]["recovery_plan"]
    assert "No external incident, issue, ticket" in report["non_goals"][0]


def test_render_incident_post_mortem_names_sections_and_non_goals(monkeypatch) -> None:
    module = load_task_module()
    _patch_incident_post_mortem_snapshots(module, monkeypatch)
    report = module._build_incident_post_mortem(_incident_post_mortem_args())

    runbook = module._render_incident_post_mortem(report)

    assert "# Incident Post-Mortem Packet" in runbook
    assert "Guard regression after merge" in runbook
    assert "## Timeline" in runbook
    assert "## Root Cause Analysis" in runbook
    assert "## Action Items" in runbook
    assert "## Prevention Measures" in runbook
    assert "detection_to_recovery_minutes: 45" in runbook
    assert "python3 scripts/codex-task validation final-suite" in runbook
    assert "No scheduler, daemon, reminder service" in runbook
    assert "git reset --hard" not in runbook


def test_build_incident_post_mortem_rejects_malformed_entries(monkeypatch) -> None:
    module = load_task_module()
    _patch_incident_post_mortem_snapshots(module, monkeypatch)

    with pytest.raises(module.TaskError, match="Timeline entry must contain"):
        module._build_incident_post_mortem(
            _incident_post_mortem_args(timeline=["2026-05-13T10:00:00+02:00|Detection"])
        )

    with pytest.raises(module.TaskError, match="Action item entry must contain"):
        module._build_incident_post_mortem(_incident_post_mortem_args(action_item=["owner|missing status"]))


def test_handle_incident_post_mortem_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_incident_post_mortem_snapshots(module, monkeypatch)

    report = repo / "reports" / "post-mortem.json"
    runbook = repo / "reports" / "post-mortem.md"
    module.handle_incident_post_mortem(
        _incident_post_mortem_args(
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
        )
    )

    output = capsys.readouterr().out
    assert "Wrote incident post-mortem report to reports/post-mortem.json" in output
    assert "Wrote incident post-mortem runbook to reports/post-mortem.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "guard-regression"
    assert payload["metrics"]["open_action_item_count"] == 1
    assert "# Incident Post-Mortem Packet" in runbook.read_text(encoding="utf-8")


def _patch_phase3_automation_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-56-phase3-automation-integration"
        if args == ["rev-parse", "HEAD"]:
            return "phase3abc"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-13-009-task56-phase3.md"},
            "current_plan": {"resolved": "plans/2026-05-13-task56-phase3.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260513-task56-phase3-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_refs": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 9})


def _write_phase3_required_paths(repo: Path, module) -> None:
    for domain in module.PHASE3_AUTOMATION_DOMAINS:
        for raw_path in domain["required_paths"]:
            path = repo / raw_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix:
                path.write_text("fixture\n", encoding="utf-8")
            else:
                path.mkdir(parents=True, exist_ok=True)


def _write_phase3_evidence_paths(repo: Path, module) -> None:
    for domain in module.PHASE3_AUTOMATION_DOMAINS:
        for raw_path in domain["evidence_paths"]:
            path = repo / raw_path
            if raw_path.endswith("/"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")


def test_build_phase3_automation_review_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase3_automation_snapshots(module, monkeypatch)
    _write_phase3_required_paths(repo, module)
    _write_phase3_evidence_paths(repo, module)

    report = module._build_phase3_automation_review(argparse.Namespace(label="task56"))

    assert report["mode"] == "static-phase3-automation-integration-review"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == len(module.PHASE3_AUTOMATION_DOMAINS)
    assert report["current_state"]["git"]["branch"] == "feat/task-56-phase3-automation-integration"
    assert {domain["id"] for domain in report["domains"]} >= {
        "ci-cd-gates",
        "guard-auto-fix",
        "canary-rollout",
        "usage-analytics",
        "final-validation",
    }
    assert "No production deployment is executed." in report["non_goals"]


def test_build_phase3_automation_review_reports_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase3_automation_snapshots(module, monkeypatch)
    _write_phase3_required_paths(repo, module)

    report = module._build_phase3_automation_review(argparse.Namespace(label="task56"))

    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert report["summary"]["needs_evidence"] == len(module.PHASE3_AUTOMATION_DOMAINS)
    assert all(domain["missing_evidence_paths"] for domain in report["domains"])
    assert not any(domain["missing_required_paths"] for domain in report["domains"])


def test_render_phase3_automation_review_lists_domains_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase3_automation_snapshots(module, monkeypatch)
    _write_phase3_required_paths(repo, module)
    _write_phase3_evidence_paths(repo, module)
    report = module._build_phase3_automation_review(argparse.Namespace(label="task56"))

    runbook = module._render_phase3_automation_review(report)

    assert "# Phase 3 Automation Integration Review" in runbook
    assert "CI/CD gates" in runbook
    assert "Guard auto-fix readiness" in runbook
    assert "Canary rollout plan" in runbook
    assert "Final validation suite" in runbook
    assert "Historical Requirements Reconciled Out Of Scope" in runbook
    assert "No production deployment is executed." in runbook
    assert "git reset --hard" not in runbook


def test_handle_phase3_automation_review_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase3_automation_snapshots(module, monkeypatch)
    _write_phase3_required_paths(repo, module)
    _write_phase3_evidence_paths(repo, module)

    report = repo / "reports" / "phase3.json"
    runbook = repo / "reports" / "phase3.md"
    module.handle_phase3_automation_review(
        argparse.Namespace(
            label="task56",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote Phase 3 automation review to reports/phase3.json" in output
    assert "Wrote Phase 3 automation runbook to reports/phase3.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task56"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Phase 3 Automation Integration Review" in runbook.read_text(encoding="utf-8")


def _patch_phase4_documentation_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-63-phase4-documentation-delivery"
        if args == ["rev-parse", "HEAD"]:
            return "phase4abc"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-13-011-task63-phase4.md"},
            "current_plan": {"resolved": "plans/2026-05-13-task63-phase4.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260513-task63-phase4-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_refs": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 11})


def _write_phase4_required_paths(repo: Path, module) -> None:
    for domain in module.PHASE4_DOCUMENTATION_DOMAINS:
        for raw_path in domain["required_paths"]:
            path = repo / raw_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")


def _write_phase4_evidence_paths(repo: Path, module) -> None:
    for domain in module.PHASE4_DOCUMENTATION_DOMAINS:
        for raw_path in domain["evidence_paths"]:
            path = repo / raw_path
            if raw_path.endswith("/"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")


def test_build_phase4_documentation_review_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase4_documentation_snapshots(module, monkeypatch)
    _write_phase4_required_paths(repo, module)
    _write_phase4_evidence_paths(repo, module)

    report = module._build_phase4_documentation_review(argparse.Namespace(label="task63"))

    assert report["mode"] == "static-phase4-documentation-delivery-review"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == len(module.PHASE4_DOCUMENTATION_DOMAINS)
    assert report["current_state"]["git"]["branch"] == "feat/task-63-phase4-documentation-delivery"
    assert {domain["id"] for domain in report["domains"]} >= {
        "documentation-suite",
        "training-materials",
        "communication-templates",
        "operational-runbook",
        "phase3-automation-review",
        "final-validation",
    }
    assert "No production documentation publication or hosted docs deployment is executed." in report["non_goals"]


def test_build_phase4_documentation_review_reports_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase4_documentation_snapshots(module, monkeypatch)
    _write_phase4_required_paths(repo, module)

    report = module._build_phase4_documentation_review(argparse.Namespace(label="task63"))

    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert report["summary"]["needs_evidence"] == len(module.PHASE4_DOCUMENTATION_DOMAINS)
    assert all(domain["missing_evidence_paths"] for domain in report["domains"])
    assert not any(domain["missing_required_paths"] for domain in report["domains"])


def test_render_phase4_documentation_review_lists_domains_guidance_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase4_documentation_snapshots(module, monkeypatch)
    _write_phase4_required_paths(repo, module)
    _write_phase4_evidence_paths(repo, module)
    report = module._build_phase4_documentation_review(argparse.Namespace(label="task63"))

    runbook = module._render_phase4_documentation_review(report)

    assert "# Phase 4 Documentation Delivery Review" in runbook
    assert "Documentation suite" in runbook
    assert "Training materials" in runbook
    assert "Communication templates" in runbook
    assert "Operational runbook" in runbook
    assert "Feedback Capture Guidance" in runbook
    assert "Historical Requirements Reconciled Out Of Scope" in runbook
    assert "No production documentation publication or hosted docs deployment is executed." in runbook
    assert "git reset --hard" not in runbook


def test_handle_phase4_documentation_review_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_phase4_documentation_snapshots(module, monkeypatch)
    _write_phase4_required_paths(repo, module)
    _write_phase4_evidence_paths(repo, module)

    report = repo / "reports" / "phase4.json"
    runbook = repo / "reports" / "phase4.md"
    module.handle_phase4_documentation_review(
        argparse.Namespace(
            label="task63",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote Phase 4 documentation review to reports/phase4.json" in output
    assert "Wrote Phase 4 documentation runbook to reports/phase4.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task63"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Phase 4 Documentation Delivery Review" in runbook.read_text(encoding="utf-8")


def _patch_deprecation_review_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-66-deprecation-management"
        if args == ["rev-parse", "HEAD"]:
            return "deprecationabc"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-13-012-task66-deprecation.md"},
            "current_plan": {"resolved": "plans/2026-05-13-task66-deprecation.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260513-task66-deprecation-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_refs": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 12})
    monkeypatch.setattr(module, "_build_deprecation_lifecycle_snapshot", _fake_deprecation_lifecycle_snapshot)


def _fake_deprecation_lifecycle_snapshot(today):
    records = [
        {
            "path": "templates/stable.md",
            "status": "stable",
            "canonical_status": "stable",
            "ok": True,
            "issues": [],
        },
        {
            "path": "templates/old.md",
            "status": "deprecated",
            "canonical_status": "deprecated",
            "ok": True,
            "issues": [
                {
                    "severity": "warning",
                    "code": "deprecation_grace_expired",
                    "message": "Deprecated template is 45 days old; 30-day grace period expired",
                },
                {
                    "severity": "recommendation",
                    "code": "archive_recommended",
                    "message": "Deprecated template is 95 days old; archive threshold is 90 days",
                },
            ],
        },
        {
            "path": "templates/missing-guidance.md",
            "status": "deprecated",
            "canonical_status": "deprecated",
            "ok": True,
            "issues": [
                {
                    "severity": "warning",
                    "code": "missing_migration_notice",
                    "message": "Deprecated template should define replacement or migration_notice",
                }
            ],
        },
    ]
    return {
        "available": True,
        "today": today.isoformat(),
        "policy": {
            "version": "test",
            "states": ["draft", "review", "stable", "deprecated", "archived"],
            "grace_days": 30,
            "archive_after_days": 90,
            "deprecated_since_key": "deprecated_since",
            "replacement_key": "replacement",
            "migration_notice_key": "migration_notice",
        },
        "metrics": _summarise_deprecation_records_for_test(records),
        "issue_records": [record for record in records if record["issues"]],
        "deprecated_records": [record for record in records if record["canonical_status"] == "deprecated"],
    }


def _summarise_deprecation_records_for_test(records):
    module = load_task_module()
    return module._summarise_deprecation_audit_records(records)


def _write_deprecation_required_paths(repo: Path, module) -> None:
    for domain in module.DEPRECATION_MANAGEMENT_DOMAINS:
        for raw_path in domain["required_paths"]:
            path = repo / raw_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")


def _write_deprecation_evidence_paths(repo: Path, module) -> None:
    for domain in module.DEPRECATION_MANAGEMENT_DOMAINS:
        for raw_path in domain["evidence_paths"]:
            path = repo / raw_path
            if raw_path.endswith("/"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")


def test_summarise_deprecation_audit_records_counts_recommendations() -> None:
    module = load_task_module()
    records = [
        {"canonical_status": "stable", "ok": True, "issues": []},
        {
            "canonical_status": "deprecated",
            "ok": True,
            "issues": [
                {"severity": "warning", "code": "deprecation_grace_expired"},
                {"severity": "recommendation", "code": "archive_recommended"},
            ],
        },
        {
            "canonical_status": "deprecated",
            "ok": True,
            "issues": [{"severity": "warning", "code": "missing_migration_notice"}],
        },
    ]

    summary = module._summarise_deprecation_audit_records(records)

    assert summary["records"] == 3
    assert summary["deprecated_records"] == 2
    assert summary["grace_expired"] == 1
    assert summary["archive_recommended"] == 1
    assert summary["missing_migration_guidance"] == 1
    assert summary["status_counts"]["deprecated"] == 2


def test_build_deprecation_management_review_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_deprecation_review_snapshots(module, monkeypatch)
    _write_deprecation_required_paths(repo, module)
    _write_deprecation_evidence_paths(repo, module)

    report = module._build_deprecation_management_review(argparse.Namespace(label="task66", today="2026-05-13"))

    assert report["mode"] == "static-deprecation-management-review"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == len(module.DEPRECATION_MANAGEMENT_DOMAINS)
    assert report["summary"]["deprecated_records"] == 2
    assert report["summary"]["archive_recommended"] == 1
    assert report["current_state"]["git"]["branch"] == "feat/task-66-deprecation-management"
    assert {domain["id"] for domain in report["domains"]} >= {
        "lifecycle-policy-audit",
        "versioning-policy",
        "communication-guidance",
        "operational-runbook",
        "emergency-recovery-guidance",
        "final-validation",
    }
    assert "No automatic template archival, file movement, deletion, or migration is executed." in report["non_goals"]


def test_build_deprecation_management_review_reports_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_deprecation_review_snapshots(module, monkeypatch)
    _write_deprecation_required_paths(repo, module)

    report = module._build_deprecation_management_review(argparse.Namespace(label="task66", today="2026-05-13"))

    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert report["summary"]["needs_evidence"] == len(module.DEPRECATION_MANAGEMENT_DOMAINS)
    assert all(domain["missing_evidence_paths"] for domain in report["domains"])
    assert not any(domain["missing_required_paths"] for domain in report["domains"])


def test_render_deprecation_management_review_lists_metrics_guidance_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_deprecation_review_snapshots(module, monkeypatch)
    _write_deprecation_required_paths(repo, module)
    _write_deprecation_evidence_paths(repo, module)
    report = module._build_deprecation_management_review(argparse.Namespace(label="task66", today="2026-05-13"))

    runbook = module._render_deprecation_management_review(report)

    assert "# Deprecation Management Review" in runbook
    assert "Lifecycle Audit Metrics" in runbook
    assert "Archive recommended: 1" in runbook
    assert "Deprecation Action Guidance" in runbook
    assert "Lifecycle policy and audit" in runbook
    assert "No automatic template archival, file movement, deletion, or migration is executed." in runbook
    assert "git reset --hard" not in runbook


def test_handle_deprecation_review_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_deprecation_review_snapshots(module, monkeypatch)
    _write_deprecation_required_paths(repo, module)
    _write_deprecation_evidence_paths(repo, module)

    report = repo / "reports" / "deprecation.json"
    runbook = repo / "reports" / "deprecation.md"
    module.handle_deprecation_review(
        argparse.Namespace(
            label="task66",
            today="2026-05-13",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote deprecation review to reports/deprecation.json" in output
    assert "Wrote deprecation runbook to reports/deprecation.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task66"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Deprecation Management Review" in runbook.read_text(encoding="utf-8")


def _patch_knowledge_transfer_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-54-knowledge-transfer-process"
        if args == ["rev-parse", "HEAD"]:
            return "knowledgeabc"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-001-task54.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task54.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task54-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"available": True})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"available": True, "memories": ["task54"]})


def _patch_knowledge_base_repo(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)


def _write_knowledge_base_fixture(repo: Path) -> None:
    files = {
        "templates/USER-GUIDE.md": "# User Guide\n\nOperator guide for the portable foundation.\n",
        "templates/guides/index.md": "# Guide Hub\n\nHuman-facing quickstart, onboarding, and troubleshooting knowledge.\n",
        "templates/engine/core/codex-readiness.md": "# Codex Readiness\n\nRuntime contract and readiness gate protocol.\n",
        "templates/workflows/session/lifecycle.md": "# Session Lifecycle\n\nSession workflow protocol and handoff rules.\n",
        ".claude/engine/runtime-contract.md": "# Claude Runtime Contract\n\nPreToolUse gate and runtime contract for Claude.\n",
        "CLAUDE.md": "# Claude Execution Runtime\n\nClaude entrypoint for the gated runtime.\n",
        "CODEX.md": "# Codex Execution Engine\n\nCodex entrypoint and ownership boundary.\n",
        "templates/TOOLS.md": "# Tools\n\nKnowledge command reference for codex-task.\n",
        "reports/README.md": "# Reports\n\nStatic report family reference and runbook index.\n",
        ".taskmaster/tasks/task_075.txt": "# Task ID: 75\n# Title: Create Knowledge Base\n\nSearchable knowledge repository.\n",
        "plans/2026-05-15-task75-create-knowledge-base.md": "# Plan - Task 75\n\nKnowledge base implementation plan.\n",
        "sessions/2026/05/2026-05-15-005-task75-create-knowledge-base.md": "# Session\n\nTask 75 knowledge base session log.\n",
        "docs/ai/work-tracking/archive/20260514-task54-knowledge-transfer-process-COMPLETED/HANDOFF.md": "# Handoff\n\nKnowledge transfer handoff and lessons learned.\n",
        "docs/ai/work-tracking/archive/20260514-task54-knowledge-transfer-process-COMPLETED/DECISIONS.md": "# Decisions\n\n- Keep knowledge base repo-native and static.\n",
        ".serena/memories/2026-05-14_task54_knowledge_transfer_process_completion.md": "# Memory\n\nContinuity memory for knowledge transfer.\n",
    }
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_build_knowledge_base_index_indexes_canonical_surfaces(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _patch_knowledge_base_repo(module, monkeypatch, tmp_path)
    _write_knowledge_base_fixture(tmp_path)

    report = module._build_knowledge_base_index(argparse.Namespace(label="task75", query="", max_items=30))

    assert report["mode"] == "static-knowledge-base-index"
    assert report["executes_actions"] is False
    assert report["summary"]["total_entries"] >= 10
    assert {category["id"] for category in report["categories"]} >= {
        "operator-guides",
        "workflow-protocols",
        "tool-report-references",
        "task-plan-session-evidence",
        "work-tracking-knowledge",
        "continuity-memories",
    }
    assert all(category["count"] > 0 for category in report["categories"])
    assert any(entry["path"] == "templates/guides/index.md" for entry in report["entries"])
    assert any(entry["path"].endswith("HANDOFF.md") for entry in report["entries"])
    assert "No hosted knowledge-base platform" in report["non_goals"][0]


def test_knowledge_base_query_returns_matching_results(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _patch_knowledge_base_repo(module, monkeypatch, tmp_path)
    _write_knowledge_base_fixture(tmp_path)

    report = module._build_knowledge_base_index(
        argparse.Namespace(label="task75-query", query="runtime contract", max_items=30)
    )

    assert report["query"] == "runtime contract"
    assert report["summary"]["search_results"] >= 2
    assert {entry["path"] for entry in report["search_results"]} >= {
        "templates/engine/core/codex-readiness.md",
        ".claude/engine/runtime-contract.md",
    }


def test_render_knowledge_base_index_lists_categories_search_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    _patch_knowledge_base_repo(module, monkeypatch, tmp_path)
    _write_knowledge_base_fixture(tmp_path)
    report = module._build_knowledge_base_index(
        argparse.Namespace(label="task75-query", query="runtime contract", max_items=30)
    )

    runbook = module._render_knowledge_base_index(report)

    assert "# Knowledge Base Index" in runbook
    assert "Operator Guides" in runbook
    assert "Search Results" in runbook
    assert "Codex Readiness" in runbook
    assert "No hosted knowledge-base platform" in runbook
    assert "canonical repository knowledge" in runbook


def test_handle_knowledge_base_writes_index_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    _patch_knowledge_base_repo(module, monkeypatch, tmp_path)
    _write_knowledge_base_fixture(tmp_path)

    report = tmp_path / "reports" / "knowledge-base.json"
    runbook = tmp_path / "reports" / "knowledge-base.md"
    module.handle_knowledge_base(
        argparse.Namespace(
            label="task75",
            query="knowledge",
            max_items=30,
            report_file=str(report.relative_to(tmp_path)),
            runbook_file=str(runbook.relative_to(tmp_path)),
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote knowledge base index to reports/knowledge-base.json" in output
    assert "Wrote knowledge base runbook to reports/knowledge-base.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task75"
    assert payload["summary"]["search_results"] > 0
    assert "# Knowledge Base Index" in runbook.read_text(encoding="utf-8")


def _write_knowledge_transfer_paths(repo: Path, module, key: str) -> None:
    for domain in module.KNOWLEDGE_TRANSFER_DOMAINS:
        for path_text in domain.get(key, ()):
            path = repo / path_text.rstrip("/")
            if path_text.endswith("/"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("knowledge transfer evidence\n", encoding="utf-8")


def _write_knowledge_transfer_required_paths(repo: Path, module) -> None:
    _write_knowledge_transfer_paths(repo, module, "required_paths")


def _write_knowledge_transfer_evidence_paths(repo: Path, module) -> None:
    _write_knowledge_transfer_paths(repo, module, "evidence_paths")


def test_build_knowledge_transfer_review_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_knowledge_transfer_snapshots(module, monkeypatch)
    _write_knowledge_transfer_required_paths(repo, module)
    _write_knowledge_transfer_evidence_paths(repo, module)

    report = module._build_knowledge_transfer_review(argparse.Namespace(label="task54"))

    assert report["mode"] == "static-knowledge-transfer-review"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == len(module.KNOWLEDGE_TRANSFER_DOMAINS)
    assert report["current_state"]["git"]["branch"] == "feat/task-54-knowledge-transfer-process"
    assert {domain["id"] for domain in report["domains"]} >= {
        "documentation-suite",
        "onboarding-training",
        "troubleshooting-operations",
        "communication-feedback",
        "continuity-handoff",
        "validation-and-delivery",
    }
    assert "No hosted knowledge-base platform" in report["non_goals"][0]


def test_build_knowledge_transfer_review_reports_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_knowledge_transfer_snapshots(module, monkeypatch)
    _write_knowledge_transfer_required_paths(repo, module)

    report = module._build_knowledge_transfer_review(argparse.Namespace(label="task54"))

    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert report["summary"]["needs_evidence"] == len(module.KNOWLEDGE_TRANSFER_DOMAINS)
    assert all(domain["missing_evidence_paths"] for domain in report["domains"])
    assert not any(domain["missing_required_paths"] for domain in report["domains"])


def test_render_knowledge_transfer_review_lists_domains_guidance_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_knowledge_transfer_snapshots(module, monkeypatch)
    _write_knowledge_transfer_required_paths(repo, module)
    _write_knowledge_transfer_evidence_paths(repo, module)
    report = module._build_knowledge_transfer_review(argparse.Namespace(label="task54"))

    runbook = module._render_knowledge_transfer_review(report)

    assert "# Knowledge Transfer Process Review" in runbook
    assert "Onboarding training" in runbook
    assert "Continuity Guidance" in runbook
    assert "Task 75 remains the future platform-oriented knowledge-base task" in runbook
    assert "No hosted knowledge-base platform" in runbook
    assert "git reset --hard" not in runbook


def test_handle_knowledge_transfer_review_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_knowledge_transfer_snapshots(module, monkeypatch)
    _write_knowledge_transfer_required_paths(repo, module)
    _write_knowledge_transfer_evidence_paths(repo, module)

    report = repo / "reports" / "knowledge.json"
    runbook = repo / "reports" / "knowledge.md"
    module.handle_knowledge_transfer_review(
        argparse.Namespace(
            label="task54",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote knowledge transfer review to reports/knowledge.json" in output
    assert "Wrote knowledge transfer runbook to reports/knowledge.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task54"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Knowledge Transfer Process Review" in runbook.read_text(encoding="utf-8")


def _patch_success_metrics_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-67-success-metrics-dashboard"
        if args == ["rev-parse", "HEAD"]:
            return "successabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-002-task67.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task67.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task67-success-metrics-dashboard-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 93, "pending": 14, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["memory.md"]})


def _write_success_metrics_sources(repo: Path, include_migration_health: bool = True) -> None:
    template_metrics = repo / "reports" / "template-metrics" / "latest.json"
    template_metrics.parent.mkdir(parents=True, exist_ok=True)
    template_metrics.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-14T10:00:00+02:00",
                "template_metadata": {
                    "coverage_pct": 100.0,
                    "drifted_file_count": 0,
                },
                "drift": {"finding_count": 0},
            }
        ),
        encoding="utf-8",
    )
    performance = repo / "reports" / "template-performance" / "latest.json"
    performance.parent.mkdir(parents=True, exist_ok=True)
    performance.write_text(
        json.dumps({"generated_at": "2026-05-14T10:00:00+02:00", "status": "pass", "summary": {"passed": 4, "total": 4}}),
        encoding="utf-8",
    )
    if include_migration_health:
        migration_health = repo / "reports" / "migration-health" / "latest.json"
        migration_health.parent.mkdir(parents=True, exist_ok=True)
        migration_health.write_text(
            json.dumps({"generated_at": "2026-05-14T10:00:00+02:00", "status": "pass", "summary": {"passed": 5, "total": 5}}),
            encoding="utf-8",
        )
    final_validation = (
        repo
        / "docs"
        / "ai"
        / "work-tracking"
        / "archive"
        / "20260512-task68-final-validation-suite-COMPLETED"
        / "reports"
        / "final-validation-suite"
        / "20260512-130228-final-validation-suite.json"
    )
    final_validation.parent.mkdir(parents=True, exist_ok=True)
    final_validation.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    knowledge = (
        repo
        / "docs"
        / "ai"
        / "work-tracking"
        / "archive"
        / "20260514-task54-knowledge-transfer-process-COMPLETED"
        / "reports"
        / "knowledge-transfer-process"
        / "knowledge-transfer-review-2026-05-14.json"
    )
    knowledge.parent.mkdir(parents=True, exist_ok=True)
    knowledge.write_text(json.dumps({"summary": {"aggregate_status": "ready"}}), encoding="utf-8")


def test_build_success_metrics_report_scores_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_success_metrics_state(module, monkeypatch, repo)
    _write_success_metrics_sources(repo)

    report = module._build_success_metrics_report(argparse.Namespace(label="task67"))

    assert report["mode"] == "static-success-metrics-dashboard"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "pass"
    assert report["summary"]["success_score_pct"] == 100.0
    assert {domain["id"] for domain in report["domains"]} >= {
        "taskmaster-health",
        "workflow-state",
        "template-metrics",
        "migration-health",
        "template-performance",
        "final-validation",
        "knowledge-transfer",
    }


def test_build_success_metrics_report_surfaces_missing_upstream(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_success_metrics_state(module, monkeypatch, repo)
    _write_success_metrics_sources(repo, include_migration_health=False)

    report = module._build_success_metrics_report(argparse.Namespace(label="task67"))

    migration = next(domain for domain in report["domains"] if domain["id"] == "migration-health")
    assert migration["status"] == "missing"
    assert report["summary"]["aggregate_status"] == "warn"
    assert report["summary"]["success_score_pct"] < 100
    assert "python3 scripts/codex-task report generate --kind migration-health" in report["recommended_refresh_commands"]


def test_render_success_metrics_report_lists_domains_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_success_metrics_state(module, monkeypatch, repo)
    _write_success_metrics_sources(repo)
    report = module._build_success_metrics_report(argparse.Namespace(label="task67"))

    runbook = module._render_success_metrics_report(report)

    assert "# Success Metrics Dashboard" in runbook
    assert "Template metrics" in runbook
    assert "Success score: 100.0%" in runbook
    assert "No React/Vue UI" in runbook
    assert "git reset --hard" not in runbook


def test_handle_success_metrics_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_success_metrics_state(module, monkeypatch, repo)
    _write_success_metrics_sources(repo)
    report = repo / "reports" / "success.json"
    runbook = repo / "reports" / "success.md"

    module.handle_success_metrics(
        argparse.Namespace(
            label="task67",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote success metrics report to reports/success.json" in output
    assert "Wrote success metrics runbook to reports/success.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task67"
    assert payload["summary"]["aggregate_status"] == "pass"
    assert "# Success Metrics Dashboard" in runbook.read_text(encoding="utf-8")


def _patch_stakeholder_report_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-73-stakeholder-reporting"
        if args == ["rev-parse", "HEAD"]:
            return "stakeholderabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-003-task73.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task73.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task73-stakeholder-reporting-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 94, "pending": 13, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["memory.md"]})


def _write_stakeholder_report_sources(repo: Path, include_success: bool = True) -> None:
    if include_success:
        success = (
            repo
            / "docs"
            / "ai"
            / "work-tracking"
            / "archive"
            / "20260514-task67-success-metrics-dashboard-COMPLETED"
            / "reports"
            / "success-metrics-dashboard"
            / "success-metrics-2026-05-14-final.json"
        )
        success.parent.mkdir(parents=True, exist_ok=True)
        success.write_text(
            json.dumps({"summary": {"aggregate_status": "pass", "success_score_pct": 100.0, "missing": 0}}),
            encoding="utf-8",
        )
    knowledge = (
        repo
        / "docs"
        / "ai"
        / "work-tracking"
        / "archive"
        / "20260514-task54-knowledge-transfer-process-COMPLETED"
        / "reports"
        / "knowledge-transfer-process"
        / "knowledge-transfer-review-2026-05-14.json"
    )
    knowledge.parent.mkdir(parents=True, exist_ok=True)
    knowledge.write_text(json.dumps({"summary": {"aggregate_status": "ready", "ready": 6}}), encoding="utf-8")
    deprecation = (
        repo
        / "docs"
        / "ai"
        / "work-tracking"
        / "archive"
        / "20260513-task66-deprecation-management-COMPLETED"
        / "reports"
        / "deprecation-management"
        / "deprecation-review-2026-05-13.json"
    )
    deprecation.parent.mkdir(parents=True, exist_ok=True)
    deprecation.write_text(json.dumps({"summary": {"aggregate_status": "ready", "ready": 7}}), encoding="utf-8")
    communication = repo / "templates" / "guides" / "communication" / "foundation-communication-templates.md"
    communication.parent.mkdir(parents=True, exist_ok=True)
    communication.write_text("# Communication Templates\n", encoding="utf-8")


def test_build_stakeholder_report_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_stakeholder_report_state(module, monkeypatch, repo)
    _write_stakeholder_report_sources(repo)

    report = module._build_stakeholder_report(argparse.Namespace(label="task73"))

    assert report["mode"] == "static-stakeholder-reporting-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "pass"
    assert report["summary"]["stakeholder_signal"] == "ready-to-share"
    assert {domain["id"] for domain in report["domains"]} >= {
        "taskmaster-delivery-health",
        "workflow-compliance",
        "success-metrics",
        "knowledge-transfer",
        "deprecation-governance",
        "stakeholder-communication-guidance",
        "risk-compliance-summary",
    }
    assert "No hosted executive dashboard" in report["non_goals"][0]


def test_build_stakeholder_report_surfaces_missing_success_source(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_stakeholder_report_state(module, monkeypatch, repo)
    _write_stakeholder_report_sources(repo, include_success=False)

    report = module._build_stakeholder_report(argparse.Namespace(label="task73"))

    success = next(domain for domain in report["domains"] if domain["id"] == "success-metrics")
    risk = next(domain for domain in report["domains"] if domain["id"] == "risk-compliance-summary")
    assert success["status"] == "missing"
    assert risk["status"] == "warn"
    assert report["summary"]["aggregate_status"] == "warn"
    assert any(
        command.startswith("python3 scripts/codex-task success metrics")
        for command in report["recommended_refresh_commands"]
    )


def test_render_stakeholder_report_lists_messages_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_stakeholder_report_state(module, monkeypatch, repo)
    _write_stakeholder_report_sources(repo)
    report = module._build_stakeholder_report(argparse.Namespace(label="task73"))

    runbook = module._render_stakeholder_report(report)

    assert "# Stakeholder Reporting Packet" in runbook
    assert "Stakeholder Messages" in runbook
    assert "Success metrics" in runbook
    assert "No hosted executive dashboard" in runbook
    assert "git reset --hard" not in runbook


def test_handle_stakeholder_report_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_stakeholder_report_state(module, monkeypatch, repo)
    _write_stakeholder_report_sources(repo)
    report = repo / "reports" / "stakeholder.json"
    runbook = repo / "reports" / "stakeholder.md"

    module.handle_stakeholder_report(
        argparse.Namespace(
            label="task73",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote stakeholder report to reports/stakeholder.json" in output
    assert "Wrote stakeholder runbook to reports/stakeholder.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task73"
    assert payload["summary"]["aggregate_status"] == "pass"
    assert "# Stakeholder Reporting Packet" in runbook.read_text(encoding="utf-8")


def _patch_enhancement_plan_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-69-phase5-enhancement-planning"
        if args == ["rev-parse", "HEAD"]:
            return "enhancementabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-004-task69.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task69.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task69-phase5-enhancement-planning-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 95, "pending": 12, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task69.md"]})


def _touch_enhancement_source(repo: Path, path: str, content: str = "source\n") -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _mkdir_enhancement_source(repo: Path, path: str) -> None:
    (repo / path).mkdir(parents=True, exist_ok=True)


def _write_enhancement_plan_sources(repo: Path, include_compaction: bool = True) -> None:
    if include_compaction:
        _mkdir_enhancement_source(
            repo,
            "docs/ai/work-tracking/archive/20260508-task31-compaction-protocol-COMPLETED/reports/compaction-protocol",
        )
    _touch_enhancement_source(repo, "templates/workflows/session/compaction.md")
    _touch_enhancement_source(repo, "scripts/codex-task")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260508-task15-serena-integration-template-system-COMPLETED/designs/serena-integration-scope-reconciliation.md",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260511-task61-template-discovery-optimization-COMPLETED/designs/template-discovery-optimization-scope-reconciliation.md",
    )
    _touch_enhancement_source(repo, "scripts/template_registry.py")
    _touch_enhancement_source(repo, "templates/metadata/template-metadata-policy.json", "{}\n")
    _touch_enhancement_source(repo, "templates/registry/index.json", "[]\n")
    _touch_enhancement_source(repo, "reports/template-metrics/latest.json", "{}\n")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260512-task53-template-caching-layer-COMPLETED/reports/template-caching-layer/performance-final-2026-05-12.txt",
    )
    _mkdir_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260511-task61-template-discovery-optimization-COMPLETED/reports/template-discovery-optimization",
    )
    _touch_enhancement_source(repo, "reports/template-performance/latest.json", "{}\n")
    _touch_enhancement_source(repo, ".mcp.json", "{}\n")
    _touch_enhancement_source(repo, ".codex/config.toml", "[repo_structure]\n")
    _mkdir_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260508-task15-serena-integration-template-system-COMPLETED/reports/serena-integration-template-system",
    )
    _touch_enhancement_source(repo, "reports/success-metrics/README.md")
    _touch_enhancement_source(repo, "reports/stakeholder-reporting/README.md")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task73-stakeholder-reporting-COMPLETED/reports/stakeholder-reporting/stakeholder-report-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260508-task11-migration-roadmap-generator-COMPLETED/designs/migration-roadmap-scope-reconciliation.md",
    )
    _touch_enhancement_source(repo, "scripts/template-ssot-scanner/migration_roadmap.py")
    _mkdir_enhancement_source(repo, "scripts/template-ssot-scanner/output/data")


def test_build_enhancement_plan_summarizes_ready_and_planned_candidates(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_enhancement_plan_state(module, monkeypatch, repo)
    _write_enhancement_plan_sources(repo)

    report = module._build_enhancement_plan(argparse.Namespace(label="task69"))

    assert report["mode"] == "static-phase5-enhancement-planning-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready-with-planned-candidates"
    assert report["summary"]["total_candidates"] == 7
    assert report["summary"]["ready"] == 5
    assert report["summary"]["planned"] == 2
    assert {candidate["id"] for candidate in report["candidates"]} == {
        "compaction-trigger-policy-review",
        "semantic-discovery-verification",
        "ai-template-generation-guardrails",
        "registry-performance-follow-up",
        "optional-mcp-integration-evaluation",
        "enhancement-metrics-refresh",
        "scanner-roadmap-backlog-refresh",
    }
    generation = next(candidate for candidate in report["candidates"] if candidate["id"] == "ai-template-generation-guardrails")
    assert generation["readiness"] == "planned"
    assert "No optional MCP server is installed" in report["non_goals"][3]


def test_build_enhancement_plan_surfaces_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_enhancement_plan_state(module, monkeypatch, repo)
    _write_enhancement_plan_sources(repo, include_compaction=False)

    report = module._build_enhancement_plan(argparse.Namespace(label="task69"))

    compaction = next(candidate for candidate in report["candidates"] if candidate["id"] == "compaction-trigger-policy-review")
    assert compaction["readiness"] == "needs-evidence"
    assert "docs/ai/work-tracking/archive/20260508-task31-compaction-protocol-COMPLETED/reports/compaction-protocol" in compaction["missing_evidence_paths"]
    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert any(action["candidate_id"] == "compaction-trigger-policy-review" for action in report["recommended_next_actions"])


def test_render_enhancement_plan_lists_candidates_guidance_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_enhancement_plan_state(module, monkeypatch, repo)
    _write_enhancement_plan_sources(repo)
    report = module._build_enhancement_plan(argparse.Namespace(label="task69"))

    runbook = module._render_enhancement_plan(report)

    assert "# Phase 5 Enhancement Planning Packet" in runbook
    assert "Compaction trigger policy review" in runbook
    assert "AI-assisted template generation guardrail plan" in runbook
    assert "ready-with-planned-candidates" in runbook
    assert "No automatic compaction trigger" in runbook
    assert "git reset --hard" not in runbook


def test_handle_enhancement_phase5_plan_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_enhancement_plan_state(module, monkeypatch, repo)
    _write_enhancement_plan_sources(repo)
    report = repo / "reports" / "enhancement.json"
    runbook = repo / "reports" / "enhancement.md"

    module.handle_enhancement_phase5_plan(
        argparse.Namespace(
            label="task69",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote enhancement plan to reports/enhancement.json" in output
    assert "Wrote enhancement runbook to reports/enhancement.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task69"
    assert payload["summary"]["aggregate_status"] == "ready-with-planned-candidates"
    assert "# Phase 5 Enhancement Planning Packet" in runbook.read_text(encoding="utf-8")


def _patch_continuous_improvement_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-77-continuous-improvement"
        if args == ["rev-parse", "HEAD"]:
            return "continuousabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-15-006-task77.md"},
            "current_plan": {"resolved": "plans/2026-05-15-task77.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260515-task77-continuous-improvement-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 106, "pending": 1, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task77.md"]})


def _write_continuous_improvement_sources(repo: Path, include_feedback: bool = True) -> None:
    if include_feedback:
        _touch_enhancement_source(
            repo,
            "docs/ai/work-tracking/archive/20260514-task59-feedback-collection-system-COMPLETED/reports/feedback-collection/feedback-collection-plan-2026-05-14-final.json",
            "{}\n",
        )
    _touch_enhancement_source(repo, "reports/feedback-collection/README.md", "# Feedback Collection\n")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task69-phase5-enhancement-planning-COMPLETED/reports/phase5-enhancement-planning/phase5-plan-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "reports/enhancement-planning/README.md", "# Enhancement Planning\n")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task67-success-metrics-dashboard-COMPLETED/reports/success-metrics-dashboard/success-metrics-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "reports/success-metrics/README.md", "# Success Metrics\n")
    _touch_enhancement_source(repo, "reports/template-quality/README.md", "# Template Quality\n")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260512-task34-ab-testing-framework-COMPLETED/reports/ab-testing-framework/experiment-plan-2026-05-12.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260512-task44-change-advisory-board-process-COMPLETED/reports/change-advisory-board-process/change-advisory-2026-05-12.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260512-task68-final-validation-suite-COMPLETED/reports/final-validation-suite/20260512-132639-final-validation-suite.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task72-post-mortem-process-COMPLETED/reports/post-mortem-process/post-mortem-2026-05-13.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task73-stakeholder-reporting-COMPLETED/reports/stakeholder-reporting/stakeholder-report-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260515-task75-create-knowledge-base-COMPLETED/reports/knowledge-base/knowledge-base-2026-05-15.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task70-long-term-maintenance-COMPLETED/reports/long-term-maintenance/maintenance-plan-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "reports/maintenance/README.md", "# Maintenance\n")
    _touch_enhancement_source(repo, "reports/operational-runbook/README.md", "# Operational Runbook\n")


def test_build_continuous_improvement_review_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_continuous_improvement_state(module, monkeypatch, repo)
    _write_continuous_improvement_sources(repo)

    report = module._build_continuous_improvement_review(argparse.Namespace(label="task77"))

    assert report["mode"] == "static-continuous-improvement-review-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["total_domains"] == 6
    assert {domain["id"] for domain in report["domains"]} == {
        "feedback-intake-and-triage",
        "enhancement-roadmap-and-innovation-pipeline",
        "metric-driven-selection",
        "experiment-and-change-validation",
        "learning-and-communication-loop",
        "maintenance-and-operating-cadence",
    }
    assert any(stage["stage"] == "validate" for stage in report["loop_stages"])
    assert "No hosted suggestion portal" in report["non_goals"][0]


def test_build_continuous_improvement_review_surfaces_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_continuous_improvement_state(module, monkeypatch, repo)
    _write_continuous_improvement_sources(repo, include_feedback=False)

    report = module._build_continuous_improvement_review(argparse.Namespace(label="task77"))

    feedback = next(domain for domain in report["domains"] if domain["id"] == "feedback-intake-and-triage")
    assert feedback["status"] == "needs-evidence"
    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert any(item["domain_id"] == "feedback-intake-and-triage" for item in report["review_queue"])


def test_render_continuous_improvement_review_lists_domains_loop_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_continuous_improvement_state(module, monkeypatch, repo)
    _write_continuous_improvement_sources(repo)
    report = module._build_continuous_improvement_review(argparse.Namespace(label="task77"))

    runbook = module._render_continuous_improvement_review(report)

    assert "# Continuous Improvement Review Packet" in runbook
    assert "Feedback intake and triage" in runbook
    assert "Experiment and change validation" in runbook
    assert "Improvement Loop Stages" in runbook
    assert "No hosted suggestion portal" in runbook
    assert "Executes actions: True" not in runbook


def test_handle_continuous_improvement_review_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_continuous_improvement_state(module, monkeypatch, repo)
    _write_continuous_improvement_sources(repo)
    report = repo / "reports" / "continuous.json"
    runbook = repo / "reports" / "continuous.md"

    module.handle_continuous_improvement_review(
        argparse.Namespace(
            label="task77",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=True,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote continuous improvement review to reports/continuous.json" in output
    assert "Wrote continuous improvement runbook to reports/continuous.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task77"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Continuous Improvement Review Packet" in runbook.read_text(encoding="utf-8")


def _patch_celebration_plan_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-76-celebration-planning"
        if args == ["rev-parse", "HEAD"]:
            return "celebrationabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-005-task76.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task76.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task76-celebration-planning-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 96, "pending": 11, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task76.md"]})


def _write_celebration_plan_sources(repo: Path, include_success: bool = True) -> None:
    _touch_enhancement_source(repo, ".taskmaster/tasks/tasks.json", "{}\n")
    if include_success:
        _touch_enhancement_source(
            repo,
            "docs/ai/work-tracking/archive/20260514-task67-success-metrics-dashboard-COMPLETED/reports/success-metrics-dashboard/success-metrics-2026-05-14-final.json",
            "{}\n",
        )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task73-stakeholder-reporting-COMPLETED/reports/stakeholder-reporting/stakeholder-report-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "templates/guides/communication/foundation-communication-templates.md")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task69-phase5-enhancement-planning-COMPLETED/reports/phase5-enhancement-planning/phase5-plan-2026-05-14-final.json",
        "{}\n",
    )
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260514-task67-success-metrics-dashboard-COMPLETED")
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260514-task73-stakeholder-reporting-COMPLETED")
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260514-task69-phase5-enhancement-planning-COMPLETED")


def test_build_celebration_plan_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_celebration_plan_state(module, monkeypatch, repo)
    _write_celebration_plan_sources(repo)

    report = module._build_celebration_plan(argparse.Namespace(label="task76"))

    assert report["mode"] == "static-celebration-planning-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == 5
    assert {domain["id"] for domain in report["domains"]} == {
        "taskmaster-delivery-health",
        "success-metrics",
        "stakeholder-reporting",
        "phase5-roadmap",
        "work-tracking-archive",
    }
    assert report["announcement_draft"]["headline"] == "Portable foundation milestone ready for celebration"
    assert len(report["demo_candidates"]) == 3
    assert "No calendar event" in report["non_goals"][0]


def test_build_celebration_plan_surfaces_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_celebration_plan_state(module, monkeypatch, repo)
    _write_celebration_plan_sources(repo, include_success=False)

    report = module._build_celebration_plan(argparse.Namespace(label="task76"))

    success = next(domain for domain in report["domains"] if domain["id"] == "success-metrics")
    assert success["status"] == "needs-evidence"
    assert "docs/ai/work-tracking/archive/20260514-task67-success-metrics-dashboard-COMPLETED/reports/success-metrics-dashboard/success-metrics-2026-05-14-final.json" in success["missing_evidence_paths"]
    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert any(command.startswith("python3 scripts/codex-task success metrics") for command in report["recommended_refresh_commands"])


def test_render_celebration_plan_lists_review_materials_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_celebration_plan_state(module, monkeypatch, repo)
    _write_celebration_plan_sources(repo)
    report = module._build_celebration_plan(argparse.Namespace(label="task76"))

    runbook = module._render_celebration_plan(report)

    assert "# Celebration Planning Packet" in runbook
    assert "Announcement Draft" in runbook
    assert "Demo Candidates" in runbook
    assert "Retrospective Prompts" in runbook
    assert "No calendar event" in runbook
    assert "git reset --hard" not in runbook


def test_handle_celebration_plan_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_celebration_plan_state(module, monkeypatch, repo)
    _write_celebration_plan_sources(repo)
    report = repo / "reports" / "celebration.json"
    runbook = repo / "reports" / "celebration.md"

    module.handle_celebration_plan(
        argparse.Namespace(
            label="task76",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote celebration plan to reports/celebration.json" in output
    assert "Wrote celebration runbook to reports/celebration.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task76"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Celebration Planning Packet" in runbook.read_text(encoding="utf-8")


def _patch_feedback_collection_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-59-feedback-collection-system"
        if args == ["rev-parse", "HEAD"]:
            return "feedbackabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-006-task59.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task59.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task59-feedback-collection-system-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 97, "pending": 10, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task59.md"]})


def _write_feedback_collection_sources(repo: Path, include_communication: bool = True) -> None:
    _touch_enhancement_source(repo, ".taskmaster/tasks/tasks.json", "{}\n")
    if include_communication:
        _touch_enhancement_source(repo, "templates/guides/communication/foundation-communication-templates.md")
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260508-task49-communication-templates-COMPLETED")
    _touch_enhancement_source(repo, "templates/guides/training/foundation-onboarding.md")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task54-knowledge-transfer-process-COMPLETED/reports/knowledge-transfer-process/knowledge-transfer-review-2026-05-14.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task63-phase4-documentation-delivery-COMPLETED/reports/phase4-documentation-delivery/phase4-review-2026-05-13.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "reports/README.md")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task73-stakeholder-reporting-COMPLETED/reports/stakeholder-reporting/stakeholder-report-2026-05-14-final.json",
        "{}\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task76-celebration-planning-COMPLETED/reports/celebration-planning/celebration-plan-2026-05-14-final.json",
        "{}\n",
    )


def test_build_feedback_collection_plan_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_feedback_collection_state(module, monkeypatch, repo)
    _write_feedback_collection_sources(repo)

    report = module._build_feedback_collection_plan(argparse.Namespace(label="task59"))

    assert report["mode"] == "static-feedback-collection-planning-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == 5
    assert {domain["id"] for domain in report["domains"]} == {
        "taskmaster-follow-up-health",
        "communication-feedback-template",
        "onboarding-feedback-guidance",
        "phase4-feedback-guidance",
        "stakeholder-response-context",
    }
    assert any(field["field"] == "sentiment" for field in report["intake_schema"])
    assert any(route["category"] == "guard" for route in report["routing_matrix"])
    assert "No hosted form" in report["non_goals"][0]


def test_build_feedback_collection_plan_surfaces_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_feedback_collection_state(module, monkeypatch, repo)
    _write_feedback_collection_sources(repo, include_communication=False)

    report = module._build_feedback_collection_plan(argparse.Namespace(label="task59"))

    communication = next(domain for domain in report["domains"] if domain["id"] == "communication-feedback-template")
    assert communication["status"] == "needs-evidence"
    assert "templates/guides/communication/foundation-communication-templates.md" in communication["missing_evidence_paths"]
    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert any(command.startswith("PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_communication_templates.py") for command in report["recommended_refresh_commands"])


def test_render_feedback_collection_plan_lists_intake_routing_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_feedback_collection_state(module, monkeypatch, repo)
    _write_feedback_collection_sources(repo)
    report = module._build_feedback_collection_plan(argparse.Namespace(label="task59"))

    runbook = module._render_feedback_collection_plan(report)

    assert "# Feedback Collection Planning Packet" in runbook
    assert "Intake Schema" in runbook
    assert "Routing Matrix" in runbook
    assert "Manual Sentiment Labels" in runbook
    assert "No hosted form" in runbook
    assert "git reset --hard" not in runbook


def test_handle_feedback_collection_plan_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_feedback_collection_state(module, monkeypatch, repo)
    _write_feedback_collection_sources(repo)
    report = repo / "reports" / "feedback.json"
    runbook = repo / "reports" / "feedback.md"

    module.handle_feedback_collection_plan(
        argparse.Namespace(
            label="task59",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote feedback collection plan to reports/feedback.json" in output
    assert "Wrote feedback collection runbook to reports/feedback.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task59"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Feedback Collection Planning Packet" in runbook.read_text(encoding="utf-8")


def _patch_cleanup_plan_state(module, monkeypatch, repo: Path) -> None:
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-64-cleanup-automation"
        if args == ["rev-parse", "HEAD"]:
            return "cleanupabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-007-task64.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task64.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task64-cleanup-automation-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 98, "pending": 9, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task64.md"]})


def _write_cleanup_plan_sources(repo: Path, include_scanner: bool = True) -> None:
    _touch_enhancement_source(repo, ".taskmaster/tasks/tasks.json", "{}\n")
    if include_scanner:
        _touch_enhancement_source(repo, "scripts/template-ssot-scanner/output/data/duplicate_analysis.json", "{}\n")
    _touch_enhancement_source(repo, "scripts/template-ssot-scanner/output/data/fix_recommendations.json", "{}\n")
    _touch_enhancement_source(repo, "scripts/template-ssot-scanner/output/scripts/archive_duplicates.sh", "#!/usr/bin/env bash\n")
    _touch_enhancement_source(repo, "scripts/template-ssot-scanner/apply_reference_fixes.py")
    _mkdir_enhancement_source(repo, "scripts/template-ssot-scanner/output/backups/reference-fixes/20260510_165911")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task66-deprecation-management-COMPLETED/reports/deprecation-management/deprecation-review-2026-05-13.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "scripts/template_lifecycle.py")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260507-task19-rollback-mechanism-COMPLETED/reports/rollback-mechanism/checkpoint-2026-05-07.json",
        "{}\n",
    )
    _touch_enhancement_source(repo, "templates/metadata/emergency-response-policy.json", "{}\n")
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260507-task108-legacy-project-blog-cleanup-COMPLETED/reports/legacy-project-blog-cleanup")


def test_build_cleanup_plan_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_cleanup_plan_state(module, monkeypatch, repo)
    _write_cleanup_plan_sources(repo)

    report = module._build_cleanup_plan(argparse.Namespace(label="task64"))

    assert report["mode"] == "static-non-destructive-cleanup-planning-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["ready"] == 6
    assert {domain["id"] for domain in report["domains"]} == {
        "taskmaster-cleanup-health",
        "scanner-cleanup-evidence",
        "reference-fix-safety",
        "deprecation-lifecycle",
        "rollback-and-emergency-policy",
        "legacy-cleanup-example",
    }
    assert any(candidate["id"] == "scanner-generated-artifacts" for candidate in report["cleanup_candidates"])
    assert any(gate["gate"] == "rollback" for gate in report["approval_gates"])
    assert "No cron job" in report["non_goals"][0]


def test_build_cleanup_plan_surfaces_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_cleanup_plan_state(module, monkeypatch, repo)
    _write_cleanup_plan_sources(repo, include_scanner=False)

    report = module._build_cleanup_plan(argparse.Namespace(label="task64"))

    scanner = next(domain for domain in report["domains"] if domain["id"] == "scanner-cleanup-evidence")
    assert scanner["status"] == "needs-evidence"
    assert "scripts/template-ssot-scanner/output/data/duplicate_analysis.json" in scanner["missing_evidence_paths"]
    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert any(command == "python3 scripts/template-ssot-scanner/run_all_scanners.py" for command in report["recommended_refresh_commands"])


def test_render_cleanup_plan_lists_candidates_gates_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_cleanup_plan_state(module, monkeypatch, repo)
    _write_cleanup_plan_sources(repo)
    report = module._build_cleanup_plan(argparse.Namespace(label="task64"))

    runbook = module._render_cleanup_plan(report)

    assert "# Cleanup Automation Planning Packet" in runbook
    assert "Cleanup Candidates" in runbook
    assert "Approval Gates" in runbook
    assert "Backup And Rollback Guidance" in runbook
    assert "No cron job" in runbook
    assert "git reset --hard" in runbook
    assert "executes actions: True" not in runbook


def test_handle_cleanup_plan_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path
    _patch_cleanup_plan_state(module, monkeypatch, repo)
    _write_cleanup_plan_sources(repo)
    report = repo / "reports" / "cleanup.json"
    runbook = repo / "reports" / "cleanup.md"

    module.handle_cleanup_plan(
        argparse.Namespace(
            label="task64",
            report_file=str(report.relative_to(repo)),
            runbook_file=str(runbook.relative_to(repo)),
            dry_run=False,
            strict=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote cleanup plan to reports/cleanup.json" in output
    assert "Wrote cleanup runbook to reports/cleanup.md" in output
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task64"
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "# Cleanup Automation Planning Packet" in runbook.read_text(encoding="utf-8")


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


def test_build_experiment_rollout_plan_is_non_destructive(monkeypatch) -> None:
    module = load_task_module()
    _patch_canary_rollout_snapshots(module, monkeypatch)

    plan = module._build_experiment_rollout_plan(
        argparse.Namespace(
            label="foundation-experiment",
            control="current-foundation",
            variant=["candidate-a", "candidate-b"],
            error_threshold_pct=4.5,
        )
    )

    assert plan["version"] == 1
    assert plan["label"] == "foundation-experiment"
    assert plan["mode"] == "non-destructive-foundation-experiment-plan"
    assert plan["executes_mutations"] is False
    assert plan["current_state"]["git"]["branch"] == "feat/task-40-canary-deployment-system"
    assert plan["variant_count"] == 3
    assert [variant["id"] for variant in plan["variants"]] == ["current-foundation", "candidate-a", "candidate-b"]
    assert [variant["role"] for variant in plan["variants"]] == ["control", "candidate", "candidate"]
    assert [variant["allocation_percent"] for variant in plan["variants"]] == [33.33, 33.33, 33.34]
    assert plan["allocation_model"]["automatic_assignment"] is False
    assert plan["allocation_model"]["traffic_split"] is False
    assert plan["metric_model"]["error_threshold_pct"] == 4.5
    assert plan["promotion_model"]["automatic_promotion"] is False
    assert plan["rollback_policy"]["automatic_rollback"] is False
    assert "No LaunchDarkly or external feature flag service is configured." in plan["non_goals"]
    assert "python3 scripts/template-performance-harness --strict" in [
        metric["command"] for metric in plan["metric_model"]["metrics"]
    ]


def test_render_experiment_rollout_runbook_names_variants_metrics_and_non_goals(monkeypatch) -> None:
    module = load_task_module()
    _patch_canary_rollout_snapshots(module, monkeypatch)
    plan = module._build_experiment_rollout_plan(
        argparse.Namespace(
            label="foundation-experiment",
            control="current-foundation",
            variant=["candidate-foundation"],
            error_threshold_pct=5.0,
        )
    )

    runbook = module._render_experiment_rollout_runbook(plan)

    assert "# Foundation Experiment Runbook" in runbook
    assert "current-foundation (control): 50.0%" in runbook
    assert "candidate-foundation (candidate): 50.0%" in runbook
    assert "Guard validation" in runbook
    assert "Performance policy" in runbook
    assert "Automatic promotion: False" in runbook
    assert "No LaunchDarkly or external feature flag service is configured." in runbook
    assert "No feature flag service, traffic split, promotion, rollback, dashboard update, or notification was executed by this plan." in runbook


def test_handle_rollout_experiment_plan_writes_manifest_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_canary_rollout_snapshots(module, monkeypatch)

    report = repo / "reports" / "experiment-plan.json"
    runbook = repo / "reports" / "experiment-runbook.md"
    args = argparse.Namespace(
        label="task34-foundation-experiment",
        control="current-foundation",
        variant=["candidate-foundation"],
        error_threshold_pct=5.0,
        report_file=str(report.relative_to(repo)),
        runbook_file=str(runbook.relative_to(repo)),
        dry_run=False,
    )

    module.handle_rollout_experiment_plan(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task34-foundation-experiment"
    assert payload["executes_mutations"] is False
    assert payload["variant_count"] == 2
    assert payload["variants"][0]["role"] == "control"
    assert payload["variants"][1]["role"] == "candidate"
    assert payload["allocation_model"]["traffic_split"] is False
    assert payload["metric_model"]["error_threshold_pct"] == 5.0
    assert payload["rollback_policy"]["automatic_rollback"] is False

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Foundation Experiment Runbook" in runbook_text
    assert "No feature flag service, traffic split, promotion, rollback, dashboard update, or notification was executed by this plan." in runbook_text


def _patch_error_recovery_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-47-error-recovery-system"
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
            "current_plan": {"resolved": "plans/2026-05-13-task47-error-recovery-system.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260513-task47-error-recovery-system-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_dependencies": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 4})


def test_build_error_recovery_plan_classifies_and_stays_non_destructive(monkeypatch) -> None:
    module = load_task_module()
    _patch_error_recovery_snapshots(module, monkeypatch)

    plan = module._build_error_recovery_plan(
        argparse.Namespace(
            error_class="transient",
            summary="Network timeout while checking PR status",
            label="pr-timeout",
            max_attempts=3,
            base_delay_seconds=10,
            max_delay_seconds=30,
        )
    )

    assert plan["version"] == 1
    assert plan["mode"] == "non-destructive-error-recovery-plan"
    assert plan["executes_actions"] is False
    assert plan["recovery"]["error_class"] == "transient"
    assert plan["recovery"]["classification"]["severity"] == "P2"
    assert plan["current_state"]["git"]["branch"] == "feat/task-47-error-recovery-system"
    assert plan["retry_policy"]["retryable"] is True
    assert plan["retry_policy"]["automatic_retry"] is False
    assert [item["delay_seconds"] for item in plan["retry_policy"]["schedule"]] == [10, 20, 30]
    assert "python3 scripts/codex-task rollback checkpoint --label <label> --report-file <checkpoint.json>" in plan["related_helpers"]["rollback_checkpoint"]
    assert "No automatic retry loop is executed." in plan["non_goals"]


def test_build_error_recovery_plan_rejects_unknown_class(monkeypatch) -> None:
    module = load_task_module()
    _patch_error_recovery_snapshots(module, monkeypatch)

    with pytest.raises(module.TaskError, match="Unknown recovery error class unknown"):
        module._build_error_recovery_plan(
            argparse.Namespace(
                error_class="unknown",
                summary="Unknown issue",
                label="unknown-issue",
                max_attempts=3,
                base_delay_seconds=10,
                max_delay_seconds=30,
            )
        )


def test_render_error_recovery_runbook_names_class_backoff_and_non_goals(monkeypatch) -> None:
    module = load_task_module()
    _patch_error_recovery_snapshots(module, monkeypatch)
    plan = module._build_error_recovery_plan(
        argparse.Namespace(
            error_class="guard",
            summary="Guard blocked stale session",
            label="guard-stale-session",
            max_attempts=3,
            base_delay_seconds=10,
            max_delay_seconds=30,
        )
    )

    runbook = module._render_error_recovery_runbook(plan)

    assert "# Error Recovery Runbook" in runbook
    assert "Error class: guard - Guard or workflow policy failure" in runbook
    assert "Severity: P1" in runbook
    assert "No retry schedule; treat this class as requiring reviewed remediation." in runbook
    assert "python3 scripts/codex-guard validate --include-untracked" in runbook
    assert "No retry, rollback, reset, cleanup, notification, dashboard update, or external recovery action was executed by this plan." in runbook


def test_handle_recovery_plan_writes_manifest_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_error_recovery_snapshots(module, monkeypatch)

    report = repo / "reports" / "recovery-plan.json"
    runbook = repo / "reports" / "recovery-runbook.md"
    args = argparse.Namespace(
        error_class="validation",
        summary="Focused tests failed after recovery helper change",
        label="test-failure",
        max_attempts=4,
        base_delay_seconds=30,
        max_delay_seconds=300,
        report_file=str(report.relative_to(repo)),
        runbook_file=str(runbook.relative_to(repo)),
        dry_run=False,
    )

    module.handle_recovery_plan(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["recovery"]["error_class"] == "validation"
    assert payload["executes_actions"] is False
    assert payload["retry_policy"]["retryable"] is False
    assert payload["retry_policy"]["schedule"] == []
    assert "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <focused tests>" in payload["recommended_verification_commands"]

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Error Recovery Runbook" in runbook_text
    assert "A validation gate failed" in runbook_text
    assert "No retry, rollback, reset, cleanup, notification, dashboard update, or external recovery action was executed by this plan." in runbook_text


def _write_security_audit_fixture(repo: Path) -> tuple[Path, Path]:
    security_report = repo / "reports" / "security_validation.json"
    phase0_report = repo / "reports" / "phase0.json"
    security_report.parent.mkdir(parents=True, exist_ok=True)
    security_report.write_text(
        json.dumps(
            {
                "metadata": {
                    "scanner": "security_validator",
                    "scanner_version": "1.0.0",
                    "output_format_version": "2.0.0",
                    "stats": {"files_scanned": 3, "findings": 1, "warnings": 1, "errors": 0},
                },
                "data": {
                    "summary": {"rule_counts": {"security_path_traversal": 1}},
                    "findings": [
                        {
                            "severity": "warning",
                            "source_file": "templates/example.md",
                            "message": "Potential path traversal reference",
                        }
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    phase0_report.write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {"total": 7, "warnings": 1, "errors": 0},
                "checks": [
                    {"id": "security-warning-findings", "title": "Security warnings", "status": "warn"},
                    {"id": "monitoring-status", "title": "Monitoring", "status": "pass"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        "[project]\n"
        "dependencies = [\"click>=8\"]\n"
        "\n"
        "[dependency-groups]\n"
        "dev = [\"pytest>=7\"]\n",
        encoding="utf-8",
    )
    return security_report, phase0_report


def test_security_audit_dependency_inventory_counts_pyproject(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        "dependencies = [\"click>=8\", \"rich>=13\"]\n"
        "\n"
        "[dependency-groups]\n"
        "dev = [\"pytest>=7\"]\n",
        encoding="utf-8",
    )

    inventory = module._security_audit_dependency_inventory()

    assert inventory["counts"]["runtime"] == 2
    assert inventory["counts"]["groups"]["dev"] == 1
    assert inventory["counts"]["total"] == 3
    assert inventory["vulnerability_lookup"]["performed"] is False


def test_build_security_audit_uses_existing_evidence_without_external_actions(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    evidence_file = tmp_path / "evidence.txt"
    evidence_file.write_text("ok\n", encoding="utf-8")
    monkeypatch.setattr(
        module,
        "SECURITY_AUDIT_CONTROLS",
        (
            {
                "id": "fixture-control",
                "title": "Fixture control",
                "category": "fixture",
                "evidence_paths": ("evidence.txt",),
                "commands": ("echo verify",),
                "notes": ("fixture note",),
            },
        ),
    )
    security_report, phase0_report = _write_security_audit_fixture(tmp_path)

    audit = module._build_security_audit(
        argparse.Namespace(
            summary="Task 50 foundation security audit",
            label="task50-security",
            security_report=str(security_report.relative_to(tmp_path)),
            phase0_report=str(phase0_report.relative_to(tmp_path)),
        )
    )

    assert audit["mode"] == "non-destructive-security-audit-packet"
    assert audit["executes_actions"] is False
    assert audit["controls"][0]["status"] == "available"
    assert audit["security_validation"]["scanner"] == "security_validator"
    assert audit["security_validation"]["finding_count"] == 1
    assert audit["phase0_validation"]["status"] == "warning"
    assert audit["dependency_inventory"]["counts"]["total"] == 2
    assert audit["dependency_inventory"]["vulnerability_lookup"]["performed"] is False
    assert "No external dependency vulnerability lookup is executed." in audit["non_goals"]


def test_render_security_audit_runbook_names_controls_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    security_report, phase0_report = _write_security_audit_fixture(tmp_path)
    audit = module._build_security_audit(
        argparse.Namespace(
            summary="Task 50 foundation security audit",
            label="task50-security",
            security_report=str(security_report.relative_to(tmp_path)),
            phase0_report=str(phase0_report.relative_to(tmp_path)),
        )
    )

    runbook = module._render_security_audit_runbook(audit)

    assert "# Security Audit Runbook" in runbook
    assert "Security finding count: 1" in runbook
    assert "External vulnerability lookup: not performed" in runbook
    assert "No GDPR, SOC2, ISO, or legal compliance certification is claimed." in runbook
    assert "No external scan, CVE lookup, pentest, remediation mutation, notification, dashboard update, ticket creation, or compliance certification was executed by this audit packet." in runbook


def test_handle_security_audit_writes_packet_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "datetime", FixedDatetime)
    security_report, phase0_report = _write_security_audit_fixture(tmp_path)
    report = tmp_path / "reports" / "security-audit.json"
    runbook = tmp_path / "reports" / "security-audit.md"

    module.handle_security_audit(
        argparse.Namespace(
            summary="Task 50 foundation security audit",
            label="task50-security",
            security_report=str(security_report.relative_to(tmp_path)),
            phase0_report=str(phase0_report.relative_to(tmp_path)),
            report_file=str(report.relative_to(tmp_path)),
            runbook_file=str(runbook.relative_to(tmp_path)),
            dry_run=False,
        )
    )

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["label"] == "task50-security"
    assert payload["executes_actions"] is False
    assert payload["security_validation"]["finding_count"] == 1
    assert payload["dependency_inventory"]["vulnerability_lookup"]["performed"] is False

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Security Audit Runbook" in runbook_text
    assert "No external scan, CVE lookup, pentest, remediation mutation" in runbook_text


def _write_change_advisory_governance_policy(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "schema": "template-governance-review.v1",
                "default_review_class": "routine",
                "emergency_review_class": "emergency",
                "notification_mode": "evidence-only",
                "roles": {
                    "template_owner": "Owns the changed template or template family.",
                    "foundation_maintainer": "Maintains the foundation.",
                    "compatibility_reviewer": "Reviews compatibility impact.",
                    "emergency_approver": "Approves emergency changes.",
                },
                "review_classes": {
                    "routine": {
                        "priority": 10,
                        "required_roles": ["template_owner"],
                        "approval": "Template owner approval or active-session decision.",
                        "escalation": "No escalation required.",
                        "notification_audiences": ["active work-tracking folder"],
                        "required_evidence": ["DECISIONS.md entry when a design choice is made"],
                    },
                    "coordinated": {
                        "priority": 20,
                        "required_roles": ["template_owner", "foundation_maintainer"],
                        "approval": "Template owner and maintainer acknowledgement.",
                        "escalation": "Escalate when compatibility risk appears.",
                        "notification_audiences": ["active work-tracking folder", "task handoff"],
                        "required_evidence": ["guard and focused test evidence"],
                    },
                    "breaking": {
                        "priority": 30,
                        "required_roles": ["template_owner", "foundation_maintainer", "compatibility_reviewer"],
                        "approval": "All listed roles or explicit user approval.",
                        "escalation": "Create migration and rollback notes before merge.",
                        "notification_audiences": ["active work-tracking folder", "task handoff"],
                        "required_evidence": ["migration or rollback note"],
                    },
                    "emergency": {
                        "priority": 40,
                        "required_roles": ["foundation_maintainer", "emergency_approver"],
                        "approval": "Explicit user approval and emergency-bypass record.",
                        "escalation": "Follow emergency response policy.",
                        "notification_audiences": ["session log", "handoff"],
                        "required_evidence": ["emergency bypass reason"],
                    },
                },
                "version_change_review": {"major": "breaking", "minor": "routine", "patch": "routine"},
                "lifecycle_transition_review": {"review->stable": "coordinated"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _patch_change_advisory_snapshots(module, monkeypatch) -> None:
    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-44-change-advisory-board-process"
        if args == ["rev-parse", "HEAD"]:
            return "cab123"
        raise AssertionError(args)

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [{"status": " M", "path": "scripts/codex-task"}])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/session.md"},
            "current_plan": {"resolved": "plans/2026-05-12-task44.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260512-task44-change-advisory-board-process-ACTIVE"],
        },
    )
    monkeypatch.setattr(module, "_taskmaster_snapshot", lambda: {"summary": {"tasks": 108, "invalid_dependencies": 0}})
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"count": 5})


def test_build_change_advisory_plan_composes_governance_and_controls(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _write_change_advisory_governance_policy(repo / "templates" / "metadata" / "template-governance-policy.json")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_change_advisory_snapshots(module, monkeypatch)

    plan = module._build_change_advisory_plan(
        argparse.Namespace(
            summary="Major template contract update",
            label=None,
            task="44",
            paths=["templates/example.md"],
            previous_version="1.0.0",
            current_version="2.0.0",
            lifecycle_from=None,
            lifecycle_to=None,
            review_class=None,
            emergency=False,
            note="requires compatibility review",
        )
    )

    assert plan["mode"] == "non-destructive-change-advisory-packet"
    assert plan["executes_actions"] is False
    assert plan["change"]["task_id"] == "44"
    assert plan["governance"]["review_class"] == "breaking"
    assert plan["risk_assessment"]["risk_level"] == "high"
    assert plan["current_state"]["git"]["branch"] == "feat/task-44-change-advisory-board-process"
    assert "rollback checkpoint or reviewed rollback note before merge" in plan["advisory_controls"]["required_evidence"]
    assert any("validation final-suite" in command for command in plan["recommended_verification_commands"])
    assert "No stakeholder vote is requested or recorded by this helper." in plan["non_goals"]


def test_render_change_advisory_runbook_names_evidence_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _write_change_advisory_governance_policy(repo / "templates" / "metadata" / "template-governance-policy.json")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_change_advisory_snapshots(module, monkeypatch)
    plan = module._build_change_advisory_plan(
        argparse.Namespace(
            summary="Emergency guard repair",
            label="guard-repair",
            task="44",
            paths=["scripts/codex-guard"],
            previous_version=None,
            current_version=None,
            lifecycle_from=None,
            lifecycle_to=None,
            review_class="emergency",
            emergency=False,
            note=None,
        )
    )

    runbook = module._render_change_advisory_runbook(plan)

    assert "# Change Advisory Packet" in runbook
    assert "Review class: emergency" in runbook
    assert "Risk level: emergency" in runbook
    assert "emergency response plan/runbook evidence" in runbook
    assert "python3 scripts/codex-task emergency plan" in runbook
    assert "No CAB meeting, approval, notification, dashboard update, deployment, rollback, reset, cleanup, or external tracking action was executed by this advisory packet." in runbook


def test_handle_change_advisory_writes_packet_and_runbook(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path
    _write_change_advisory_governance_policy(repo / "templates" / "metadata" / "template-governance-policy.json")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    _patch_change_advisory_snapshots(module, monkeypatch)

    report = repo / "reports" / "change-advisory.json"
    runbook = repo / "reports" / "change-advisory.md"
    args = argparse.Namespace(
        summary="Coordinated lifecycle promotion",
        label="lifecycle-promotion",
        task="44",
        paths=["templates/example.md"],
        previous_version=None,
        current_version=None,
        lifecycle_from="review",
        lifecycle_to="stable",
        review_class=None,
        emergency=False,
        note=None,
        report_file=str(report.relative_to(repo)),
        runbook_file=str(runbook.relative_to(repo)),
        dry_run=False,
    )

    module.handle_change_advisory(args)

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["governance"]["review_class"] == "coordinated"
    assert payload["communication_guidance"]["mode"] == "evidence-only"
    assert payload["executes_actions"] is False

    runbook_text = runbook.read_text(encoding="utf-8")
    assert "# Change Advisory Packet" in runbook_text
    assert "Coordinated lifecycle promotion" in runbook_text
    assert "No CAB meeting, approval, notification, dashboard update" in runbook_text


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


def test_build_template_bundle_plan_includes_dependencies_and_target_conflicts(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    _write_repo_config(source, "templates")
    _write_repo_config(target, "target_templates")
    _write_template_doc(
        source / "templates" / "workflows" / "deploy.md",
        """
id: workflow-deploy
title: Deploy Workflow
type: workflow
status: stable
category: deployment
dependencies:
  - shared-evidence
  - missing-helper
""",
        "# Deploy\n",
    )
    _write_template_doc(
        source / "templates" / "shared" / "evidence.md",
        """
id: shared-evidence
title: Evidence Pattern
type: pattern
status: stable
category: evidence
""",
        "# Evidence\n",
    )
    _write_template_registry(
        source,
        "templates",
        [
            {"id": "workflow-deploy", "path": "templates/workflows/deploy.md", "tags": ["deployment"]},
            {"id": "shared-evidence", "path": "templates/shared/evidence.md", "tags": ["evidence"]},
        ],
    )
    _write_template_doc(
        target / "target_templates" / "workflows" / "deploy.md",
        """
id: workflow-deploy
title: Deploy Workflow
type: workflow
status: stable
category: deployment
""",
        "# Target variant\n",
    )

    monkeypatch.setattr(module, "REPO_ROOT", source)
    plan = module._build_template_bundle_plan(
        argparse.Namespace(
            source_dir=".",
            target_dir=str(target),
            templates=["workflow-deploy"],
            label="task46",
            no_dependencies=False,
        )
    )

    assert plan["mode"] == "non-destructive-template-bundle-plan"
    assert plan["executes_mutations"] is False
    assert plan["source"]["templates_root"] == "templates"
    assert plan["target"]["templates_root"] == "target_templates"
    assert plan["requested_templates"] == ["workflow-deploy"]
    assert plan["template_count"] == 2

    assets = {asset["id"]: asset for asset in plan["templates"]}
    assert assets["workflow-deploy"]["bundle_status"] == "different"
    assert assets["workflow-deploy"]["target_path"] == "target_templates/workflows/deploy.md"
    assert assets["shared-evidence"]["bundle_status"] == "missing"
    assert assets["shared-evidence"]["target_path"] == "target_templates/shared/evidence.md"
    assert plan["missing"]["dependencies"] == [
        {
            "query": "missing-helper",
            "requested_by": "workflow-deploy",
            "message": "Dependency could not be resolved from the local registry.",
        }
    ]
    assert {item["status"] for item in plan["manual_review_queue"]} == {"different", "missing"}


def test_handle_template_bundle_plan_writes_manifest_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_config(repo, "templates")
    _write_template_doc(
        repo / "templates" / "engine" / "core" / "readiness.md",
        """
id: engine-core-readiness
title: Readiness
type: engine
status: stable
category: core
""",
    )
    _write_template_registry(
        repo,
        "templates",
        [{"id": "engine-core-readiness", "path": "templates/engine/core/readiness.md"}],
    )
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    manifest = repo / "reports" / "bundle.json"
    runbook = repo / "reports" / "bundle.md"

    module.handle_template_bundle_plan(
        argparse.Namespace(
            source_dir=".",
            target_dir=None,
            templates=["engine-core-readiness"],
            label="task46",
            report_file="reports/bundle.json",
            runbook_file="reports/bundle.md",
            no_dependencies=False,
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote template bundle plan to reports/bundle.json" in output
    assert "Wrote template bundle runbook to reports/bundle.md" in output
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["templates"][0]["id"] == "engine-core-readiness"
    assert payload["templates"][0]["bundle_status"] == "not-checked"
    assert "No template copy, archive, extraction" in runbook.read_text(encoding="utf-8")


def test_handle_template_bundle_plan_dry_run_prints_json_without_writing(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_repo_config(repo, "templates")
    _write_template_registry(repo, "templates", [])
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    module.handle_template_bundle_plan(
        argparse.Namespace(
            source_dir=".",
            target_dir=None,
            templates=["missing-template"],
            label="task46",
            report_file="reports/bundle.json",
            runbook_file="reports/bundle.md",
            no_dependencies=False,
            dry_run=True,
        )
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["template_count"] == 0
    assert payload["missing"]["templates"][0]["query"] == "missing-template"
    assert not (repo / "reports").exists()


def _write_template_usage_test_repo(repo: Path) -> None:
    _write_repo_config(repo, "templates")
    _write_template_doc(
        repo / "templates" / "engine" / "core" / "codex-readiness.md",
        """
id: engine-core-codex-readiness
title: Codex Readiness
type: critical-enforcement
status: stable
category: engine
aliases:
  - codex-readiness
""",
        "# Codex Readiness\n",
    )
    _write_template_doc(
        repo / "templates" / "guides" / "index.md",
        """
id: guide-index
title: Guide Index
type: user-guide
status: stable
category: guides
""",
        "# Guide Index\n",
    )
    _write_template_registry(
        repo,
        "templates",
        [
            {
                "id": "engine-core-codex-readiness",
                "path": "templates/engine/core/codex-readiness.md",
                "aliases": ["codex-readiness"],
            },
            {"id": "guide-index", "path": "templates/guides/index.md"},
        ],
    )
    session = repo / "sessions" / "2026" / "05" / "2026-05-13-001-usage.md"
    session.parent.mkdir(parents=True)
    session.write_text(
        "Use engine-core-codex-readiness and templates/engine/core/codex-readiness.md.\n",
        encoding="utf-8",
    )
    plan = repo / "plans" / "2026-05-13-task51.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("Review codex-readiness before changing hooks.\n", encoding="utf-8")
    active = repo / "docs" / "ai" / "work-tracking" / "active" / "20260513-task51-ACTIVE" / "TRACKER.md"
    active.parent.mkdir(parents=True)
    active.write_text("Template path: templates/guides/index.md\n", encoding="utf-8")
    archived = repo / "docs" / "ai" / "work-tracking" / "archive" / "20260512-task50-COMPLETED" / "TRACKER.md"
    archived.parent.mkdir(parents=True)
    archived.write_text("Historical reference: engine-core-codex-readiness\n", encoding="utf-8")
    task_file = repo / ".taskmaster" / "tasks" / "task_051.txt"
    task_file.parent.mkdir(parents=True)
    task_file.write_text("Task references guide-index.\n", encoding="utf-8")


def test_build_template_usage_analytics_counts_static_references(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_template_usage_test_repo(repo)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    report = module._build_template_usage_analytics(
        argparse.Namespace(
            label="task51",
            source_dir=".",
            include_archive=False,
            max_items=5,
            max_examples=2,
        )
    )

    assert report["mode"] == "non-destructive-template-usage-analytics"
    assert report["executes_mutations"] is False
    assert report["source"]["include_archive"] is False
    assert report["source_summary"]["files_scanned"] == 4
    usage = {item["id"]: item for item in report["template_usage"]}
    assert usage["engine-core-codex-readiness"]["id_mentions"] == 1
    assert usage["engine-core-codex-readiness"]["path_mentions"] == 1
    assert usage["engine-core-codex-readiness"]["alias_mentions"] == 1
    assert usage["engine-core-codex-readiness"]["total_mentions"] == 3
    assert usage["guide-index"]["id_mentions"] == 1
    assert usage["guide-index"]["path_mentions"] == 1
    assert usage["guide-index"]["total_mentions"] == 2
    assert report["usage_summary"]["monthly_mentions"]["2026-05"] == 4
    assert "work_tracking_archive" not in report["source"]["source_types"]


def test_template_usage_analytics_optionally_includes_archive(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_template_usage_test_repo(repo)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    report = module._build_template_usage_analytics(
        argparse.Namespace(
            label="task51",
            source_dir=".",
            include_archive=True,
            max_items=5,
            max_examples=2,
        )
    )

    usage = {item["id"]: item for item in report["template_usage"]}
    assert report["source"]["include_archive"] is True
    assert "work_tracking_archive" in report["source"]["source_types"]
    assert usage["engine-core-codex-readiness"]["total_mentions"] == 4
    assert usage["engine-core-codex-readiness"]["source_counts"]["work_tracking_archive"] == 1


def test_render_template_usage_analytics_names_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_template_usage_test_repo(repo)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    report = module._build_template_usage_analytics(
        argparse.Namespace(
            label="task51",
            source_dir=".",
            include_archive=False,
            max_items=5,
            max_examples=2,
        )
    )
    runbook = module._render_template_usage_analytics(report)

    assert "# Template Usage Analytics" in runbook
    assert "engine-core-codex-readiness" in runbook
    assert "Path-Only References" in runbook
    assert "No runtime tracker, database, live dashboard" in runbook


def test_handle_template_usage_analytics_writes_report_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_template_usage_test_repo(repo)
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    module.handle_template_usage_analytics(
        argparse.Namespace(
            label="task51",
            source_dir=".",
            include_archive=False,
            max_items=5,
            max_examples=2,
            report_file="reports/template-usage-analytics/latest.json",
            runbook_file="reports/template-usage-analytics/latest.md",
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote template usage analytics report to reports/template-usage-analytics/latest.json" in output
    assert "Wrote template usage analytics runbook to reports/template-usage-analytics/latest.md" in output
    payload = json.loads((repo / "reports" / "template-usage-analytics" / "latest.json").read_text(encoding="utf-8"))
    assert payload["usage_summary"]["templates_with_observed_usage"] == 2
    assert "Template Usage Analytics" in (repo / "reports" / "template-usage-analytics" / "latest.md").read_text(encoding="utf-8")


def _patch_template_quality_state(module, monkeypatch, repo: Path) -> None:
    _write_repo_config(repo, "templates")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-65-template-quality-scoring"
        if args == ["rev-parse", "HEAD"]:
            return "qualityabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"resolved": "sessions/2026/05/2026-05-14-008-task65.md"},
            "current_plan": {"resolved": "plans/2026-05-14-task65.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 99, "pending": 8, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task65.md"]})


def _write_template_quality_sources(repo: Path, include_performance: bool = True) -> None:
    _write_template_doc(
        repo / "templates" / "engine" / "core" / "codex-readiness.md",
        """
id: engine-core-codex-readiness
title: Codex Readiness
type: critical-enforcement
status: stable
category: engine
aliases:
  - codex-readiness
""",
    )
    _write_template_registry(
        repo,
        "templates",
        [
            {
                "id": "engine-core-codex-readiness",
                "path": "templates/engine/core/codex-readiness.md",
                "aliases": ["codex-readiness"],
            }
        ],
    )
    _touch_enhancement_source(
        repo,
        "reports/template-metrics/latest.json",
        json.dumps(
            {
                "template_metadata": {"coverage_pct": 100.0, "drifted_file_count": 0},
                "drift": {"finding_count": 0},
            }
        )
        + "\n",
    )
    if include_performance:
        _touch_enhancement_source(
            repo,
            "reports/template-performance/latest.json",
            json.dumps(
                {
                    "status": "pass",
                    "policy_version": "1.0.0",
                    "summary": {"total": 2, "passed": 2, "warnings": 0, "errors": 0},
                }
            )
            + "\n",
        )
    _touch_enhancement_source(
        repo,
        "scripts/template-ssot-scanner/output/data/template_scan_results.json",
        json.dumps(
            {
                "metadata": {
                    "stats": {
                        "files_scanned": 5,
                        "total_lines": 250,
                        "issues_detected": 0,
                    }
                },
                "data": {"errors": []},
            }
        )
        + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task51-template-usage-analytics-COMPLETED/reports/template-usage-analytics/template-usage-analytics-2026-05-13.json",
        json.dumps(
            {
                "usage_summary": {
                    "total_mentions": 4,
                    "templates_with_observed_usage": 1,
                    "templates_without_observed_usage": 0,
                }
            }
        )
        + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task50-security-audit-process-COMPLETED/reports/security-audit-process/security-audit-2026-05-13.json",
        json.dumps(
            {
                "controls": [
                    {"id": "template-security-validator", "status": "available"},
                    {"id": "ci-and-guard", "status": "available"},
                ]
            }
        )
        + "\n",
    )


def test_build_template_quality_score_summarizes_pass(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_template_quality_state(module, monkeypatch, repo)
    _write_template_quality_sources(repo)

    report = module._build_template_quality_score(argparse.Namespace(label="task65"))

    assert report["mode"] == "static-non-destructive-template-quality-scorecard"
    assert report["executes_mutations"] is False
    assert report["summary"]["aggregate_status"] == "pass"
    assert report["summary"]["quality_score_pct"] == 100.0
    assert report["summary"]["quality_grade"] == "A+"
    assert {domain["id"] for domain in report["domains"]} == {
        "metadata-and-drift",
        "registry-health",
        "scanner-complexity",
        "template-performance",
        "usage-analytics",
        "security-audit",
        "workflow-continuity",
    }
    assert any(gate["gate"] == "metadata-coverage" for gate in report["quality_gates"])
    assert "No live dashboard" in report["non_goals"][0]


def test_build_template_quality_score_surfaces_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_template_quality_state(module, monkeypatch, repo)
    _write_template_quality_sources(repo, include_performance=False)

    report = module._build_template_quality_score(argparse.Namespace(label="task65"))

    performance = next(domain for domain in report["domains"] if domain["id"] == "template-performance")
    assert performance["status"] == "missing"
    assert "reports/template-performance/latest.json" in performance["evidence"]
    assert report["summary"]["aggregate_status"] == "warn"
    assert any(item["domain"] == "template-performance" for item in report["improvement_suggestions"])


def test_render_template_quality_score_lists_domains_gates_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_template_quality_state(module, monkeypatch, repo)
    _write_template_quality_sources(repo)
    report = module._build_template_quality_score(argparse.Namespace(label="task65"))

    runbook = module._render_template_quality_score(report)

    assert "# Template Quality Scorecard" in runbook
    assert "Quality grade: A+" in runbook
    assert "Domain Scores" in runbook
    assert "Quality Gates" in runbook
    assert "Improvement Suggestions" in runbook
    assert "No live dashboard" in runbook
    assert "Executes mutations: True" not in runbook


def test_handle_template_quality_score_writes_report_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_template_quality_state(module, monkeypatch, repo)
    _write_template_quality_sources(repo)

    module.handle_template_quality_score(
        argparse.Namespace(
            label="task65",
            report_file="reports/template-quality/latest.json",
            runbook_file="reports/template-quality/latest.md",
            strict=True,
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote template quality scorecard to reports/template-quality/latest.json" in output
    assert "Wrote template quality runbook to reports/template-quality/latest.md" in output
    payload = json.loads((repo / "reports" / "template-quality" / "latest.json").read_text(encoding="utf-8"))
    assert payload["summary"]["aggregate_status"] == "pass"
    assert "Template Quality Scorecard" in (repo / "reports" / "template-quality" / "latest.md").read_text(encoding="utf-8")


def _patch_maintenance_plan_state(module, monkeypatch, repo: Path) -> None:
    _write_repo_config(repo, "templates")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "TASKMASTER_TASKS_JSON", repo / ".taskmaster" / "tasks" / "tasks.json")
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-70-long-term-maintenance"
        if args == ["rev-parse", "HEAD"]:
            return "maintenanceabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"path": "sessions/current", "resolved": "sessions/2026/05/2026-05-14-009-task70.md"},
            "current_plan": {"path": "plans/current", "resolved": "plans/2026-05-14-task70.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260514-task70-long-term-maintenance-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 100, "pending": 7, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task70.md"]})


def _write_maintenance_plan_sources(
    repo: Path,
    *,
    include_performance: bool = True,
    monitoring_status: str = "pass",
    security_control_status: str = "available",
) -> None:
    _touch_enhancement_source(repo, "reports/operational-runbook/README.md", "# Operational Runbook\n")
    _touch_enhancement_source(repo, "pyproject.toml", "[project]\nname = \"codex\"\n")
    _touch_enhancement_source(repo, ".taskmaster/tasks/tasks.json", json.dumps({"master": {"tasks": []}}) + "\n")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task60-post-migration-monitoring-COMPLETED/reports/post-migration-monitoring/post-migration-monitoring-2026-05-13.json",
        json.dumps({"aggregate_status": monitoring_status, "summary": {"warnings": 0, "failures": 0}}) + "\n",
    )
    if include_performance:
        _touch_enhancement_source(
            repo,
            "reports/template-performance/latest.json",
            json.dumps({"status": "pass", "summary": {"total": 2, "passed": 2, "warnings": 0, "errors": 0}}) + "\n",
        )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task65-template-quality-scoring-COMPLETED/reports/template-quality-scoring/template-quality-score-2026-05-14-final.json",
        json.dumps({"summary": {"aggregate_status": "pass", "quality_score_pct": 97.0, "quality_grade": "A+"}}) + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task64-cleanup-automation-COMPLETED/reports/cleanup-automation/cleanup-plan-2026-05-14-final.json",
        json.dumps({"summary": {"aggregate_status": "ready", "ready": 6}}) + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task50-security-audit-process-COMPLETED/reports/security-audit-process/security-audit-2026-05-13.json",
        json.dumps(
            {
                "controls": [
                    {"id": "template-security-validator", "status": "available"},
                    {"id": "phase0-security-gate", "status": security_control_status},
                ],
                "dependency_inventory": {
                    "exists": True,
                    "path": "pyproject.toml",
                    "vulnerability_lookup": {"performed": False},
                },
            }
        )
        + "\n",
    )


def test_build_maintenance_plan_summarizes_ready_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_maintenance_plan_state(module, monkeypatch, repo)
    _write_maintenance_plan_sources(repo)

    report = module._build_maintenance_plan(argparse.Namespace(label="task70"))

    assert report["mode"] == "static-non-destructive-long-term-maintenance-plan"
    assert report["executes_mutations"] is False
    assert report["summary"]["aggregate_status"] == "ready"
    assert report["summary"]["maintenance_score_pct"] == 100.0
    assert {domain["id"] for domain in report["domains"]} == {
        "workflow-health",
        "operational-cadence",
        "post-migration-monitoring",
        "performance-baseline",
        "template-quality",
        "cleanup-readiness",
        "security-maintenance",
        "dependency-maintenance",
    }
    assert any(gate["gate"] == "security-maintenance" for gate in report["maintenance_gates"])
    assert "No cron job" in report["non_goals"][0]


def test_build_maintenance_plan_surfaces_review_and_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_maintenance_plan_state(module, monkeypatch, repo)
    _write_maintenance_plan_sources(repo, include_performance=False, monitoring_status="fail")

    report = module._build_maintenance_plan(argparse.Namespace(label="task70"))

    monitoring = next(domain for domain in report["domains"] if domain["id"] == "post-migration-monitoring")
    performance = next(domain for domain in report["domains"] if domain["id"] == "performance-baseline")
    assert monitoring["status"] == "review"
    assert performance["status"] == "missing"
    assert report["summary"]["aggregate_status"] == "needs-review"
    assert any(item["domain"] == "performance-baseline" for item in report["manual_action_queue"])


def test_render_maintenance_plan_lists_domains_gates_actions_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_maintenance_plan_state(module, monkeypatch, repo)
    _write_maintenance_plan_sources(repo, security_control_status="missing-evidence")
    report = module._build_maintenance_plan(argparse.Namespace(label="task70"))

    runbook = module._render_maintenance_plan(report)

    assert "# Long-term Maintenance Plan" in runbook
    assert "Maintenance Domains" in runbook
    assert "Maintenance Gates" in runbook
    assert "Manual Action Queue" in runbook
    assert "No cron job" in runbook
    assert "Executes mutations: True" not in runbook


def test_handle_maintenance_plan_writes_report_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_maintenance_plan_state(module, monkeypatch, repo)
    _write_maintenance_plan_sources(repo)

    module.handle_maintenance_plan(
        argparse.Namespace(
            label="task70",
            report_file="reports/maintenance/latest.json",
            runbook_file="reports/maintenance/latest.md",
            strict=True,
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote long-term maintenance plan to reports/maintenance/latest.json" in output
    assert "Wrote long-term maintenance runbook to reports/maintenance/latest.md" in output
    payload = json.loads((repo / "reports" / "maintenance" / "latest.json").read_text(encoding="utf-8"))
    assert payload["summary"]["aggregate_status"] == "ready"
    assert "Long-term Maintenance Plan" in (repo / "reports" / "maintenance" / "latest.md").read_text(encoding="utf-8")


def test_handle_maintenance_plan_dry_run_outputs_json(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_maintenance_plan_state(module, monkeypatch, repo)
    _write_maintenance_plan_sources(repo)

    module.handle_maintenance_plan(
        argparse.Namespace(label="task70", report_file=None, runbook_file=None, strict=False, dry_run=True)
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "task70"
    assert payload["summary"]["aggregate_status"] == "ready"


def test_handle_maintenance_plan_strict_fails_after_writing(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_maintenance_plan_state(module, monkeypatch, repo)
    _write_maintenance_plan_sources(repo, include_performance=False)

    with pytest.raises(module.TaskError, match="Long-term maintenance aggregate status is not ready"):
        module.handle_maintenance_plan(
            argparse.Namespace(
                label="task70",
                report_file="reports/maintenance/latest.json",
                runbook_file="reports/maintenance/latest.md",
                strict=True,
                dry_run=False,
            )
        )

    assert (repo / "reports" / "maintenance" / "latest.json").exists()


def _patch_deployment_readiness_state(module, monkeypatch, repo: Path) -> None:
    _write_repo_config(repo, "templates")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(module, "REPO_STRUCTURE", module.load_repo_structure(repo))
    monkeypatch.setattr(module, "TASKMASTER_TASKS_JSON", repo / ".taskmaster" / "tasks" / "tasks.json")
    monkeypatch.setattr(module, "TASKMASTER_TASKS_JSON_REL", ".taskmaster/tasks/tasks.json")
    monkeypatch.setattr(module, "datetime", FixedDatetime)

    def fake_git_output(args):
        if args == ["branch", "--show-current"]:
            return "feat/task-80-production-deployment"
        if args == ["rev-parse", "HEAD"]:
            return "deploymentabc"
        if args == ["status", "--short"]:
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(module, "_git_output", fake_git_output)
    monkeypatch.setattr(module, "_git_status_snapshot", lambda: [])
    monkeypatch.setattr(
        module,
        "_workflow_snapshot",
        lambda: {
            "current_session": {"path": "sessions/current", "resolved": "sessions/2026/05/2026-05-15-task80.md"},
            "current_plan": {"path": "plans/current", "resolved": "plans/2026-05-15-task80.md"},
            "active_work_tracking": ["docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE"],
        },
    )
    monkeypatch.setattr(
        module,
        "_taskmaster_snapshot",
        lambda: {
            "path": ".taskmaster/tasks/tasks.json",
            "exists": True,
            "sha256": "abc",
            "tag": "master",
            "summary": {
                "tasks": 108,
                "subtasks": 304,
                "status_counts": {"done": 103, "pending": 4, "in-progress": 1},
                "dependency_refs": 229,
                "invalid_refs": 0,
            },
            "invalid_refs": [],
        },
    )
    monkeypatch.setattr(module, "_serena_memory_snapshot", lambda: {"exists": True, "count": 1, "latest": ["task80.md"]})


def _write_deployment_readiness_sources(
    repo: Path,
    *,
    include_final_validation: bool = True,
    maintenance_status: str = "needs-review",
    stakeholder_status: str = "warn",
) -> None:
    _touch_enhancement_source(repo, ".taskmaster/tasks/tasks.json", json.dumps({"master": {"tasks": []}}) + "\n")
    _touch_enhancement_source(repo, "sessions/2026/05/2026-05-15-task80.md", "# Session\n")
    _touch_enhancement_source(repo, "plans/2026-05-15-task80.md", "# Plan\n")
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE")
    if include_final_validation:
        _touch_enhancement_source(
            repo,
            "docs/ai/work-tracking/archive/20260512-task68-final-validation-suite-COMPLETED/reports/final-validation-suite/20260512-132639-final-validation-suite.json",
            json.dumps({"summary": {"status": "passed", "passed": 12, "failed_required": 0, "total": 12}}) + "\n",
        )
    _touch_enhancement_source(repo, "templates/guides/reference/final-documentation-map.md", "# Final Docs\n")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260515-task78-final-documentation-COMPLETED/reports/final-documentation/taskmaster-health-2026-05-15-final.txt",
        "Taskmaster health: OK\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task70-long-term-maintenance-COMPLETED/reports/long-term-maintenance/maintenance-plan-2026-05-14-final.json",
        json.dumps({"summary": {"aggregate_status": maintenance_status, "maintenance_score_pct": 87.5}}) + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260513-task60-post-migration-monitoring-COMPLETED/reports/post-migration-monitoring/post-migration-monitoring-2026-05-13.json",
        json.dumps({"aggregate_status": "pass", "summary": {"available_inputs": 2, "failures": 0, "warnings": 0}}) + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task73-stakeholder-reporting-COMPLETED/reports/stakeholder-reporting/stakeholder-report-2026-05-14-final.json",
        json.dumps({"summary": {"aggregate_status": stakeholder_status, "stakeholder_signal": "needs-refresh", "warnings": 1, "failures": 0}}) + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task76-celebration-planning-COMPLETED/reports/celebration-planning/celebration-plan-2026-05-14-final.json",
        json.dumps({"summary": {"aggregate_status": "ready", "ready": 5, "needs_evidence": 0, "blocked": 0}}) + "\n",
    )
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/archive/20260514-task64-cleanup-automation-COMPLETED/reports/cleanup-automation/cleanup-plan-2026-05-14-final.json",
        json.dumps({"summary": {"aggregate_status": "ready"}}) + "\n",
    )
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260515-task74-phase-6-cleanup-COMPLETED")
    _touch_enhancement_source(repo, "templates/engine/validation/foundation-adoption-guide.md", "# Adoption\n")
    _touch_enhancement_source(repo, "templates/engine/core/portable-foundation-spec.md", "# Spec\n")
    _touch_enhancement_source(repo, "templates/guides/quickstart/getting-started.md", "# Quickstart\n")
    _mkdir_enhancement_source(repo, "docs/ai/work-tracking/archive/20260424-task102-foundation-migration-adoption-COMPLETED")
    _touch_enhancement_source(
        repo,
        "docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/designs/production-deployment-scope-reconciliation.md",
        "# Scope\n",
    )


def test_build_deployment_readiness_report_summarizes_review_domains(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo)

    report = module._build_deployment_readiness_report(argparse.Namespace(label="task80"))

    assert report["mode"] == "static-production-transition-readiness-packet"
    assert report["executes_actions"] is False
    assert report["summary"]["aggregate_status"] == "review"
    assert report["summary"]["transition_signal"] == "ready-with-review"
    domains = {domain["id"]: domain for domain in report["domains"]}
    assert domains["final-validation"]["status"] == "ready"
    assert domains["maintenance-bau"]["status"] == "review"
    assert domains["stakeholder-communications"]["status"] == "review"
    assert domains["runtime-migration-flags"]["status"] == "not-applicable"
    assert any(command.startswith("python3 scripts/codex-task deployment readiness") for command in report["recommended_refresh_commands"])


def test_build_deployment_readiness_prefers_active_task80_monitoring(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo)
    active_monitoring = (
        "docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/"
        "reports/production-deployment/post-migration-monitoring-2026-05-15-ssot-clean.json"
    )
    _touch_enhancement_source(
        repo,
        active_monitoring,
        json.dumps({"aggregate_status": "warn", "summary": {"available_inputs": 2, "failures": 0, "warnings": 2}}) + "\n",
    )
    os.utime(repo / active_monitoring, (2_000_000_000, 2_000_000_000))

    report = module._build_deployment_readiness_report(argparse.Namespace(label="task80"))

    monitoring = next(domain for domain in report["domains"] if domain["id"] == "post-migration-monitoring")
    assert monitoring["status"] == "review"
    assert monitoring["details"]["source"]["path"] == active_monitoring
    assert monitoring["details"]["status_value"] == "warn"
    assert report["summary"]["aggregate_status"] == "review"


def test_build_deployment_readiness_report_surfaces_missing_final_validation(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo, include_final_validation=False)

    report = module._build_deployment_readiness_report(argparse.Namespace(label="task80"))

    domains = {domain["id"]: domain for domain in report["domains"]}
    assert domains["final-validation"]["status"] == "needs-evidence"
    assert report["summary"]["aggregate_status"] == "needs-evidence"
    assert any(item["status"] == "needs-evidence" for item in report["production_readiness_checklist"])


def test_render_deployment_readiness_report_lists_maps_and_non_goals(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo)
    report = module._build_deployment_readiness_report(argparse.Namespace(label="task80"))

    runbook = module._render_deployment_readiness_report(report)

    assert "# Production Transition Readiness Packet" in runbook
    assert "Production Readiness Checklist" in runbook
    assert "BAU Transition Checklist" in runbook
    assert "Historical Requirement Map" in runbook
    assert "No production application deployment" in runbook
    assert "Executes actions: True" not in runbook


def test_handle_deployment_readiness_writes_packet_and_runbook(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo)

    module.handle_deployment_readiness(
        argparse.Namespace(
            label="task80",
            report_file="reports/production-deployment/latest.json",
            runbook_file="reports/production-deployment/latest.md",
            strict=True,
            dry_run=False,
        )
    )

    output = capsys.readouterr().out
    assert "Wrote production readiness packet to reports/production-deployment/latest.json" in output
    assert "Wrote production readiness runbook to reports/production-deployment/latest.md" in output
    payload = json.loads((repo / "reports" / "production-deployment" / "latest.json").read_text(encoding="utf-8"))
    assert payload["summary"]["aggregate_status"] == "review"
    assert "Production Transition Readiness Packet" in (repo / "reports" / "production-deployment" / "latest.md").read_text(encoding="utf-8")


def test_handle_deployment_readiness_strict_fails_on_missing_evidence(monkeypatch, tmp_path) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo, include_final_validation=False)

    with pytest.raises(module.TaskError, match="Production transition readiness has blocking or missing evidence"):
        module.handle_deployment_readiness(
            argparse.Namespace(
                label="task80",
                report_file="reports/production-deployment/latest.json",
                runbook_file="reports/production-deployment/latest.md",
                strict=True,
                dry_run=False,
            )
        )

    assert (repo / "reports" / "production-deployment" / "latest.json").exists()


def test_handle_deployment_readiness_dry_run_outputs_json(monkeypatch, tmp_path, capsys) -> None:
    module = load_task_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_deployment_readiness_state(module, monkeypatch, repo)
    _write_deployment_readiness_sources(repo)

    module.handle_deployment_readiness(
        argparse.Namespace(label="task80", report_file=None, runbook_file=None, strict=False, dry_run=True)
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "task80"
    assert payload["mode"] == "static-production-transition-readiness-packet"


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
