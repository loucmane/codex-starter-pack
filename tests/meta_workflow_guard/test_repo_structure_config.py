"""Tests for repo-structure configuration loading."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def load_repo_structure_module():
    name = "repo_structure_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/_repo_structure.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.loader.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_repo_structure_uses_defaults_without_config(tmp_path) -> None:
    module = load_repo_structure_module()
    structure = module.load_repo_structure(tmp_path)

    assert structure.sessions_root == (tmp_path / "sessions").resolve()
    assert structure.current_session_link == (tmp_path / "sessions" / "current").resolve()
    assert structure.work_tracking_active_root == (tmp_path / "docs" / "ai" / "work-tracking" / "active").resolve()
    assert structure.taskmaster_tasks_json == (tmp_path / ".taskmaster" / "tasks" / "tasks.json").resolve()


def test_load_repo_structure_reads_repo_local_overrides(tmp_path) -> None:
    module = load_repo_structure_module()
    config_dir = tmp_path / ".codex"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        """
[repo_structure]
templates_root = "template-system"
sessions_root = "state/sessions"
plans_root = "state/plans"
plan_state_dir = "state/plan-sync"
taskmaster_root = "ops/taskmaster"
work_tracking_root = "state/work-tracking"
reports_root = "state/reports"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    structure = module.load_repo_structure(tmp_path)

    assert structure.templates_root == (tmp_path / "template-system").resolve()
    assert structure.sessions_root == (tmp_path / "state" / "sessions").resolve()
    assert structure.current_plan_link == (tmp_path / "state" / "plans" / "current").resolve()
    assert structure.taskmaster_tasks_dir == (tmp_path / "ops" / "taskmaster" / "tasks").resolve()
    assert structure.work_tracking_archive_root == (tmp_path / "state" / "work-tracking" / "archive").resolve()
    assert structure.metrics_report_dir == (tmp_path / "state" / "reports" / "template-metrics").resolve()
