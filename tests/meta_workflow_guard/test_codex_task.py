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


def test_build_parser_accepts_taskmaster_generate_one() -> None:
    module = load_task_module()
    parser = module.build_parser()
    args = parser.parse_args(["taskmaster", "generate-one", "--id", "104"])
    assert args.command == "taskmaster"
    assert args.subcommand == "generate-one"
    assert args.task_id == "104"


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
        strict_drift=True,
        dry_run=False,
    )

    module.handle_report_generate(args)

    assert len(commands) == 2
    assert Path(commands[0][1]).name == "codex-guard"
    assert commands[0][2:] == ["drift-check", "--report-dir", "reports/template-drift", "--strict"]
    assert Path(commands[1][1]).name == "template-metrics-dashboard"
    assert commands[1][2:] == ["--report-dir", "reports/template-metrics"]


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
        strict_drift=False,
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
        assert (target / shape.roots["sessions_root"]).is_dir()
        assert (target / shape.roots["plans_root"]).is_dir()
        assert (target / shape.roots["taskmaster_root"] / "tasks").is_dir()
        assert (target / shape.roots["work_tracking_root"] / "active").is_dir()
        assert (target / shape.roots["reports_root"] / "template-metrics").is_dir()
