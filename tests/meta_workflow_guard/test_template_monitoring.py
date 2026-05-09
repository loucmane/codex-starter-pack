"""Regression tests for the static template monitoring evaluator."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.meta_workflow_guard.cross_project_fixtures import REPO_SHAPES, write_repo_config


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_monitoring_module():
    name = "template_monitoring_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/template-monitoring")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def _policy_payload() -> dict[str, object]:
    return {
        "version": "test",
        "checks": [
            {
                "id": "coverage",
                "title": "Coverage",
                "source": "template_metadata.coverage_pct",
                "operator": ">=",
                "threshold": 100,
                "severity": "error",
                "message": "Coverage must be complete.",
            },
            {
                "id": "active",
                "title": "Active folders",
                "source": "work_tracking.active_folder_count",
                "operator": "<=",
                "threshold": 1,
                "severity": "warning",
                "message": "Too many active folders.",
            },
            {
                "id": "missing_optional",
                "title": "Missing optional",
                "source": "missing.value",
                "operator": "==",
                "threshold": 0,
                "severity": "warning",
                "missing_severity": "warning",
                "message": "Missing is warning only.",
            },
        ],
    }


def _write_monitoring_policy(repo: Path, templates_root: str = "custom_templates") -> None:
    policy_path = repo / templates_root / "metadata" / "template-monitoring-policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(_policy_payload(), indent=2) + "\n", encoding="utf-8")


def _metrics_payload(*, coverage: float = 100.0, active_count: int = 1) -> dict[str, object]:
    return {
        "template_metadata": {
            "coverage_pct": coverage,
            "drifted_file_count": 0,
        },
        "drift": {
            "finding_count": 0,
        },
        "work_tracking": {
            "active_folder_count": active_count,
        },
        "taskmaster": {
            "status_counts": {
                "in-progress": 1,
            }
        },
        "plan_sync": {
            "entry_count": 1,
        },
    }


def test_monitoring_policy_loads_from_configured_templates_root(tmp_path: Path) -> None:
    module = load_monitoring_module()
    shape = REPO_SHAPES["product-web"]
    write_repo_config(tmp_path, shape)
    _write_monitoring_policy(tmp_path, shape.roots["templates_root"])

    policy = module.load_monitoring_policy(tmp_path)

    assert policy.version == "test"
    assert [check.id for check in policy.checks] == ["coverage", "active", "missing_optional"]


def test_monitoring_policy_validates_checks() -> None:
    module = load_monitoring_module()
    payload = _policy_payload()
    payload["checks"][0]["operator"] = "around"

    with pytest.raises(module.MonitoringError, match="unsupported operator"):
        module.MonitoringPolicy.from_mapping(payload)


def test_evaluate_snapshot_reports_pass_warning_and_failure() -> None:
    module = load_monitoring_module()
    policy = module.MonitoringPolicy.from_mapping(_policy_payload())

    report = module.evaluate_snapshot(_metrics_payload(coverage=99.0, active_count=2), policy=policy)

    results = {result.id: result for result in report.results}
    assert report.status == "fail"
    assert report.summary == {"total": 3, "passed": 0, "warnings": 2, "errors": 1}
    assert results["coverage"].status == "fail"
    assert results["coverage"].severity == "error"
    assert results["active"].status == "fail"
    assert results["active"].severity == "warning"
    assert results["missing_optional"].status == "missing"
    assert results["missing_optional"].severity == "warning"


def test_evaluate_snapshot_passes_clean_metrics() -> None:
    module = load_monitoring_module()
    payload = _policy_payload()
    payload["checks"] = payload["checks"][:2]
    policy = module.MonitoringPolicy.from_mapping(payload)

    report = module.evaluate_snapshot(_metrics_payload(), policy=policy)

    assert report.status == "pass"
    assert report.summary == {"total": 2, "passed": 2, "warnings": 0, "errors": 0}
    assert all(result.ok for result in report.results)


def test_main_writes_outputs_and_strict_fails_only_on_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    module = load_monitoring_module()
    shape = REPO_SHAPES["product-web"]
    write_repo_config(tmp_path, shape)
    _write_monitoring_policy(tmp_path, shape.roots["templates_root"])
    metrics_path = tmp_path / "reports" / "template-metrics" / "latest.json"
    metrics_path.parent.mkdir(parents=True)
    metrics_path.write_text(json.dumps(_metrics_payload(coverage=99.0, active_count=1)) + "\n", encoding="utf-8")

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--metrics",
            "reports/template-metrics/latest.json",
            "--report-dir",
            "reports/template-monitoring",
            "--strict",
        ]
    )
    output = capsys.readouterr().out

    assert result == 1
    assert "Monitoring status: fail" in output
    payload = json.loads((tmp_path / "reports" / "template-monitoring" / "latest.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "reports" / "template-monitoring" / "latest.md").read_text(encoding="utf-8")
    assert payload["status"] == "fail"
    assert "# Template Monitoring Report" in markdown


def test_main_strict_allows_warning_only_reports(tmp_path: Path) -> None:
    module = load_monitoring_module()
    shape = REPO_SHAPES["product-web"]
    write_repo_config(tmp_path, shape)
    _write_monitoring_policy(tmp_path, shape.roots["templates_root"])
    metrics_path = tmp_path / "reports" / "template-metrics" / "latest.json"
    metrics_path.parent.mkdir(parents=True)
    metrics_path.write_text(json.dumps(_metrics_payload(active_count=2)) + "\n", encoding="utf-8")

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--metrics",
            "reports/template-metrics/latest.json",
            "--report-dir",
            "reports/template-monitoring",
            "--strict",
        ]
    )

    assert result == 0
    payload = json.loads((tmp_path / "reports" / "template-monitoring" / "latest.json").read_text(encoding="utf-8"))
    assert payload["status"] == "warn"


def test_real_monitoring_policy_loads() -> None:
    module = load_monitoring_module()

    policy = module.load_monitoring_policy(REPO_ROOT)

    assert policy.version == "1.0.0"
    assert {check.id for check in policy.checks} >= {
        "template_metadata_coverage",
        "template_metadata_drift",
        "template_drift_findings",
    }


def test_guard_workflows_generate_and_upload_monitoring_reports() -> None:
    codex_guard = (REPO_ROOT / ".github" / "workflows" / "codex-guard.yml").read_text(encoding="utf-8")
    meta_guard = (REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml").read_text(encoding="utf-8")

    assert "python3 scripts/template-monitoring --strict" in codex_guard
    assert "reports/template-monitoring/" in codex_guard
    assert "python3 scripts/template-monitoring --strict" in meta_guard
    assert "reports/template-monitoring/" in meta_guard
