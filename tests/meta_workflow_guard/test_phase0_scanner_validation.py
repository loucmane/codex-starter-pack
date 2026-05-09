"""Regression tests for Phase 0 scanner validation reports."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_SCANNER_OUTPUTS = (
    "baseline_summary.json",
    "duplicate_analysis.json",
    "fix_recommendations.json",
    "migration_status.json",
    "reference_analysis.json",
    "security_validation.json",
    "template_scan_results.json",
)


def load_phase0_module():
    name = "template_phase0_validation_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/template-phase0-validation")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def _wrapped(scanner: str, data: dict[str, object], stats: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "metadata": {
            "scanner": scanner,
            "output_format_version": "2.0.0",
            "stats": stats or {},
        },
        "data": data,
    }


def _write_scanner_outputs(
    scanner_dir: Path,
    *,
    security_errors: int = 0,
    security_warnings: int = 0,
    broken_references: int = 0,
    duplicate_count: int = 0,
    total_fixes: int = 0,
    omit: str | None = None,
    unwrap: str | None = None,
) -> None:
    scanner_dir.mkdir(parents=True, exist_ok=True)
    baseline_metrics = {
        "total_files": 10,
        "total_lines": 100,
        "total_references": 8,
        "broken_references": broken_references,
        "duplicate_count": duplicate_count,
        "migration_percentage": 100.0,
        "total_fixes": total_fixes,
    }
    severity_counts: dict[str, int] = {}
    if security_errors:
        severity_counts["error"] = security_errors
    if security_warnings:
        severity_counts["warning"] = security_warnings

    payloads = {
        "baseline_summary.json": _wrapped(
            "baseline_summary",
            {"metrics": baseline_metrics},
            stats=baseline_metrics,
        ),
        "security_validation.json": _wrapped(
            "security_validator",
            {"summary": {"severity_counts": severity_counts}},
            stats={"errors": security_errors, "warnings": security_warnings},
        ),
        "duplicate_analysis.json": _wrapped("duplicate_analyzer", {}),
        "fix_recommendations.json": _wrapped("fix_recommender", {}),
        "migration_status.json": _wrapped("migration_status", {}),
        "reference_analysis.json": _wrapped("reference_analyzer", {}),
        "template_scan_results.json": _wrapped("template_scanner", {}),
    }
    for filename in REQUIRED_SCANNER_OUTPUTS:
        if filename == omit:
            continue
        payload = {"legacy": True} if filename == unwrap else payloads[filename]
        (scanner_dir / filename).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_monitoring_report(path: Path, *, status: str = "pass") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": status, "summary": {"errors": 0, "warnings": 0}}) + "\n", encoding="utf-8")


def test_phase0_validation_passes_clean_artifacts(tmp_path: Path) -> None:
    module = load_phase0_module()
    scanner_dir = tmp_path / "scanner-data"
    monitoring = tmp_path / "reports" / "template-monitoring" / "latest.json"
    _write_scanner_outputs(scanner_dir)
    _write_monitoring_report(monitoring)

    report = module.evaluate_phase0(scanner_dir, monitoring, generated_at="2026-05-09T12:00:00+02:00")

    assert report.status == "pass"
    assert report.summary == {"total": 7, "passed": 7, "warnings": 0, "errors": 0}
    assert {check.id for check in report.checks} >= {
        "scanner-output-completeness",
        "baseline-metrics-completeness",
        "security-error-findings",
        "monitoring-status",
    }


def test_phase0_validation_warns_for_known_non_blocking_findings(tmp_path: Path) -> None:
    module = load_phase0_module()
    scanner_dir = tmp_path / "scanner-data"
    monitoring = tmp_path / "reports" / "template-monitoring" / "latest.json"
    _write_scanner_outputs(scanner_dir, security_warnings=1, broken_references=3, duplicate_count=1)
    _write_monitoring_report(monitoring, status="warn")

    report = module.evaluate_phase0(scanner_dir, monitoring)

    assert report.status == "warn"
    warnings = {check.id for check in report.checks if check.status == "warn"}
    assert warnings == {"security-warning-findings", "baseline-known-findings", "monitoring-status"}


def test_phase0_validation_fails_for_missing_and_unwrapped_outputs(tmp_path: Path) -> None:
    module = load_phase0_module()
    scanner_dir = tmp_path / "scanner-data"
    monitoring = tmp_path / "reports" / "template-monitoring" / "latest.json"
    _write_scanner_outputs(scanner_dir, omit="duplicate_analysis.json", unwrap="reference_analysis.json")
    _write_monitoring_report(monitoring)

    report = module.evaluate_phase0(scanner_dir, monitoring)
    checks = {check.id: check for check in report.checks}

    assert report.status == "fail"
    assert checks["scanner-output-completeness"].status == "fail"
    assert checks["scanner-output-format"].status == "fail"
    assert checks["scanner-output-completeness"].details["missing"] == ["duplicate_analysis.json"]


def test_phase0_validation_reports_invalid_json_as_gate_failure(tmp_path: Path) -> None:
    module = load_phase0_module()
    scanner_dir = tmp_path / "scanner-data"
    monitoring = tmp_path / "reports" / "template-monitoring" / "latest.json"
    _write_scanner_outputs(scanner_dir)
    (scanner_dir / "migration_status.json").write_text("{not-json\n", encoding="utf-8")
    monitoring.parent.mkdir(parents=True, exist_ok=True)
    monitoring.write_text("{not-json\n", encoding="utf-8")

    report = module.evaluate_phase0(scanner_dir, monitoring)
    checks = {check.id: check for check in report.checks}

    assert report.status == "fail"
    assert checks["scanner-output-format"].status == "fail"
    assert checks["monitoring-status"].details["status"] == "invalid"


def test_phase0_validation_fails_strict_on_security_errors_and_monitoring_fail(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_phase0_module()
    scanner_dir = tmp_path / "scanner-data"
    monitoring = tmp_path / "reports" / "template-monitoring" / "latest.json"
    _write_scanner_outputs(scanner_dir, security_errors=1)
    _write_monitoring_report(monitoring, status="fail")

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--scanner-data-dir",
            str(scanner_dir),
            "--monitoring-file",
            str(monitoring),
            "--report-dir",
            "reports/phase0-scanner-validation",
            "--strict",
        ]
    )
    output = capsys.readouterr().out

    assert result == 1
    assert "Phase 0 validation status: fail" in output
    payload = json.loads((tmp_path / "reports" / "phase0-scanner-validation" / "latest.json").read_text(encoding="utf-8"))
    assert payload["status"] == "fail"


def test_phase0_validation_strict_allows_warning_only_reports(tmp_path: Path) -> None:
    module = load_phase0_module()
    scanner_dir = tmp_path / "scanner-data"
    monitoring = tmp_path / "reports" / "template-monitoring" / "latest.json"
    _write_scanner_outputs(scanner_dir, security_warnings=1, total_fixes=2)
    _write_monitoring_report(monitoring)

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--scanner-data-dir",
            str(scanner_dir),
            "--monitoring-file",
            str(monitoring),
            "--report-dir",
            "reports/phase0-scanner-validation",
            "--strict",
        ]
    )

    assert result == 0
    markdown = (tmp_path / "reports" / "phase0-scanner-validation" / "latest.md").read_text(encoding="utf-8")
    payload = json.loads((tmp_path / "reports" / "phase0-scanner-validation" / "latest.json").read_text(encoding="utf-8"))
    assert payload["status"] == "warn"
    assert "# Phase 0 Scanner Validation Report" in markdown


def test_guard_workflows_generate_and_upload_phase0_reports() -> None:
    codex_guard = (REPO_ROOT / ".github" / "workflows" / "codex-guard.yml").read_text(encoding="utf-8")
    meta_guard = (REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml").read_text(encoding="utf-8")

    assert "python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci" in codex_guard
    assert "python3 scripts/template-phase0-validation --strict" in codex_guard
    assert "reports/phase0-scanner-validation/" in codex_guard
    assert "python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci" in meta_guard
    assert "python3 scripts/template-phase0-validation --strict" in meta_guard
    assert "reports/phase0-scanner-validation/" in meta_guard
