"""Regression tests for the template metrics dashboard generator."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

from tests.meta_workflow_guard.cross_project_fixtures import REPO_SHAPES, seed_workflow_state, write_repo_config


def load_metrics_module():
    name = "template_metrics_dashboard_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/template-metrics-dashboard")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def test_load_codex_guard_imports_real_module() -> None:
    module = load_metrics_module()
    guard = module.load_codex_guard()
    assert hasattr(guard, "collect_template_metadata_drift")
    assert hasattr(guard, "iter_repo_markdown_files")


def test_collect_drift_metrics_reads_latest_report(monkeypatch, tmp_path) -> None:
    module = load_metrics_module()
    report_dir = tmp_path / "reports" / "template-drift"
    report_dir.mkdir(parents=True)
    (report_dir / "summary-20260424-140000.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-24T14:00:00+02:00",
                "finding_count": 1,
                "categories": ["template-metadata"],
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "summary-20260424-150000.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-24T15:00:00+02:00",
                "finding_count": 0,
                "categories": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "DRIFT_REPORT_DIR", report_dir)

    metrics = module.collect_drift_metrics()

    assert metrics["latest_report"] == "reports/template-drift/summary-20260424-150000.json"
    assert metrics["finding_count"] == 0
    assert metrics["categories"] == []


def test_main_writes_dashboard_outputs(monkeypatch, tmp_path, capsys) -> None:
    module = load_metrics_module()
    report_dir = tmp_path / "reports" / "template-metrics"
    snapshot = module.MetricsSnapshot(
        generated_at="2026-04-24T16:00:00+02:00",
        taskmaster={
            "total_tasks": 3,
            "status_counts": {"done": 2, "pending": 1},
            "focus_chain": [{"id": 97, "title": "Create Template Metrics Dashboard", "status": "in-progress"}],
        },
        template_metadata={
            "governed_file_count": 10,
            "drifted_file_count": 1,
            "compliant_file_count": 9,
            "coverage_pct": 90.0,
        },
        drift={
            "latest_report": "reports/template-drift/summary-20260424-150000.json",
            "generated_at": "2026-04-24T15:00:00+02:00",
            "finding_count": 0,
            "categories": [],
        },
        work_tracking={
            "active_folder_count": 1,
            "active_folders": ["20260424-task97-template-metrics-dashboard-ACTIVE"],
            "archived_folder_count": 4,
            "completed_archive_count": 4,
        },
        plan_sync={
            "entry_count": 12,
            "latest_plan": "plans/2026-04-24-task97-template-metrics-dashboard.md",
            "latest_synced_at": "2026-04-24T15:39:12+02:00",
        },
        wizard={
            "kickoff_session_count": 2,
            "kickoff_sessions": [
                "sessions/2026/04/2026-04-24-003-task96-interactive-template-wizard.md",
                "sessions/2026/04/2026-04-24-004-task97-template-metrics-dashboard.md",
            ],
        },
    )
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "build_snapshot", lambda: snapshot)

    result = module.main(["--report-dir", "reports/template-metrics"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Wrote metrics dashboard to reports/template-metrics/latest.md" in captured.out
    assert "Wrote metrics JSON to reports/template-metrics/latest.json" in captured.out

    json_payload = json.loads((report_dir / "latest.json").read_text(encoding="utf-8"))
    assert json_payload["taskmaster"]["total_tasks"] == 3
    markdown = (report_dir / "latest.md").read_text(encoding="utf-8")
    assert "# Template Metrics Dashboard" in markdown
    assert "Task 97: Create Template Metrics Dashboard — in-progress" in markdown


def test_collect_workflow_metrics_supports_cross_project_roots(monkeypatch, tmp_path) -> None:
    module = load_metrics_module()

    for name, shape in REPO_SHAPES.items():
        repo_root = tmp_path / name
        write_repo_config(repo_root, shape)
        seed_workflow_state(repo_root, shape)

        monkeypatch.setattr(module, "REPO_ROOT", repo_root)
        monkeypatch.setattr(module, "WORK_TRACKING_ACTIVE", repo_root / shape.work_tracking_root / "active")
        monkeypatch.setattr(module, "WORK_TRACKING_ARCHIVE", repo_root / shape.work_tracking_root / "archive")
        monkeypatch.setattr(module, "SESSIONS_DIR", repo_root / shape.session_dir)

        work_tracking = module.collect_work_tracking_metrics()
        wizard = module.collect_wizard_metrics()

        assert work_tracking["active_folder_count"] == 1
        assert work_tracking["archived_folder_count"] == 1
        assert wizard["kickoff_session_count"] == 1
