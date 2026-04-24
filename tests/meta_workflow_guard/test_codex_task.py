"""Unit tests for codex-task wizard helpers."""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


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
    assert ["task-master", "generate"] in commands


def test_build_parser_accepts_bootstrap_init() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["bootstrap", "init", "--target-dir", "/tmp/bootstrap-target", "--templates-root", "ops/templates"])
    assert args.command == "bootstrap"
    assert args.subcommand == "init"
    assert args.target_dir == "/tmp/bootstrap-target"
    assert args.templates_root == "ops/templates"


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
    setup_path = target / ".codex" / "bootstrap" / "FOUNDATION-SETUP.md"

    assert config_path.exists()
    assert policy_path.exists()
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
    assert (target / "reports" / "session-continuation").is_dir()


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
