"""Regression tests for the static migration health dashboard."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

from tests.meta_workflow_guard.cross_project_fixtures import REPO_SHAPES, write_repo_config


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_migration_health_module():
    name = "template_migration_health_dashboard_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/template-migration-health-dashboard")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_component_reports(repo: Path, reports_root: str = "reports", *, cost_status: str = "warn") -> None:
    reports = repo / reports_root
    _write_json(
        reports / "template-metrics" / "latest.json",
        {"generated_at": "2026-05-12T12:00:00+02:00", "taskmaster": {"total_tasks": 1}},
    )
    _write_json(
        reports / "template-monitoring" / "latest.json",
        {"generated_at": "2026-05-12T12:01:00+02:00", "status": "pass", "summary": {"errors": 0}},
    )
    _write_json(
        reports / "phase0-scanner-validation" / "latest.json",
        {"generated_at": "2026-05-12T12:02:00+02:00", "status": "pass", "summary": {"errors": 0}},
    )
    _write_json(
        reports / "template-performance" / "latest.json",
        {"generated_at": "2026-05-12T12:03:00+02:00", "status": "pass", "summary": {"errors": 0}},
    )
    _write_json(
        reports / "cost-tracking" / "latest.json",
        {"generated_at": "2026-05-12T12:04:00+02:00", "status": cost_status, "summary": {"not_measured": 1}},
    )


def test_build_report_warns_when_optional_component_is_missing(tmp_path: Path) -> None:
    module = load_migration_health_module()
    _seed_component_reports(tmp_path)
    (tmp_path / "reports" / "cost-tracking" / "latest.json").unlink()

    report = module.build_report(repo_root=tmp_path, generated_at="2026-05-12T13:00:00+02:00")

    components = {component.id: component for component in report.components}
    assert report.status == "warn"
    assert components["cost"].status == "missing"
    assert components["cost"].severity == "warning"
    assert report.summary["missing"] == 1


def test_build_report_fails_on_malformed_component(tmp_path: Path) -> None:
    module = load_migration_health_module()
    _seed_component_reports(tmp_path)
    (tmp_path / "reports" / "template-monitoring" / "latest.json").write_text("{not-json\n", encoding="utf-8")

    report = module.build_report(repo_root=tmp_path)

    components = {component.id: component for component in report.components}
    assert report.status == "fail"
    assert components["monitoring"].status == "fail"
    assert components["monitoring"].source_status == "invalid-json"


def test_build_report_maps_source_statuses_to_aggregate_health(tmp_path: Path) -> None:
    module = load_migration_health_module()
    _seed_component_reports(tmp_path, cost_status="pass")

    report = module.build_report(repo_root=tmp_path)

    assert report.status == "pass"
    assert report.summary == {"total": 5, "passed": 5, "warnings": 0, "errors": 0, "missing": 0}

    _write_json(
        tmp_path / "reports" / "template-performance" / "latest.json",
        {"generated_at": "2026-05-12T12:03:00+02:00", "status": "fail", "summary": {"errors": 1}},
    )
    failed = module.build_report(repo_root=tmp_path)
    assert failed.status == "fail"
    assert failed.summary["errors"] == 1


def test_main_writes_markdown_and_json_outputs(tmp_path: Path, capsys) -> None:
    module = load_migration_health_module()
    _seed_component_reports(tmp_path)

    result = module.main(["--repo-root", str(tmp_path), "--report-dir", "reports/migration-health"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Wrote migration health dashboard to reports/migration-health/latest.md" in output
    payload = json.loads((tmp_path / "reports" / "migration-health" / "latest.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "reports" / "migration-health" / "latest.md").read_text(encoding="utf-8")
    assert payload["status"] == "warn"
    assert "# Migration Health Dashboard" in markdown
    assert "No live dashboard, WebSocket" in markdown


def test_default_component_specs_follow_configured_reports_root(tmp_path: Path) -> None:
    module = load_migration_health_module()
    shape = REPO_SHAPES["product-web"]
    write_repo_config(tmp_path, shape)

    specs = module.default_component_specs(tmp_path)

    assert {spec.id for spec in specs} == {"metrics", "monitoring", "phase0", "performance", "cost"}
    for spec in specs:
        assert spec.path.is_relative_to(tmp_path / shape.roots["reports_root"])


def test_guard_workflows_generate_and_upload_migration_health_reports() -> None:
    codex_guard = (REPO_ROOT / ".github" / "workflows" / "codex-guard.yml").read_text(encoding="utf-8")
    meta_guard = (REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml").read_text(encoding="utf-8")

    assert "python3 scripts/template-migration-health-dashboard --strict" in codex_guard
    assert "reports/migration-health/" in codex_guard
    assert "python3 scripts/template-migration-health-dashboard --strict" in meta_guard
    assert "reports/migration-health/" in meta_guard
