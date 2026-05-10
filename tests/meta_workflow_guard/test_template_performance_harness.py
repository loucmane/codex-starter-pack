"""Regression tests for the template performance harness."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_performance_module():
    name = "template_performance_harness_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/template-performance-harness")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def _policy(module, checks: list[dict[str, object]]):
    return module.PerformancePolicy.from_mapping(
        {
            "version": "test",
            "defaults": {"regression_warning_pct": 20, "regression_critical_pct": 50},
            "checks": checks,
        }
    )


def test_evaluate_policy_classifies_duration_and_regression(monkeypatch, tmp_path: Path) -> None:
    module = load_performance_module()
    policy = _policy(
        module,
        [
            {
                "id": "fast",
                "title": "Fast",
                "probe": "template_registry_records",
                "warning_seconds": 0.1,
                "critical_seconds": 0.5,
            },
            {
                "id": "duration_warn",
                "title": "Duration warn",
                "probe": "template_registry_records",
                "warning_seconds": 0.1,
                "critical_seconds": 0.5,
            },
            {
                "id": "regression_fail",
                "title": "Regression fail",
                "probe": "template_registry_records",
                "warning_seconds": 1.0,
                "critical_seconds": 2.0,
            },
        ],
    )
    outcomes = {
        "fast": module.ProbeOutcome(elapsed_seconds=0.01, message="ok"),
        "duration_warn": module.ProbeOutcome(elapsed_seconds=0.2, message="slow"),
        "regression_fail": module.ProbeOutcome(elapsed_seconds=0.8, message="regressed"),
    }

    monkeypatch.setattr(module, "_run_probe", lambda check, repo_root, temp_dir: outcomes[check.id])

    report = module.evaluate_policy(policy, repo_root=tmp_path, baseline={"regression_fail": 0.4})
    statuses = {result.id: result.status for result in report.results}
    messages = {result.id: result.message for result in report.results}

    assert report.status == "fail"
    assert statuses == {"fast": "pass", "duration_warn": "warn", "regression_fail": "fail"}
    assert "warning threshold" in messages["duration_warn"]
    assert "critical threshold" in messages["regression_fail"]


def test_load_baseline_accepts_compact_baseline_and_report_payload(tmp_path: Path) -> None:
    module = load_performance_module()
    compact = tmp_path / "baseline.json"
    compact.write_text(
        json.dumps({"checks": {"alpha": {"elapsed_seconds": 0.25}, "beta": {"elapsed_seconds": 0.5}}}),
        encoding="utf-8",
    )
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps({"results": [{"id": "gamma", "elapsed_seconds": 1.25}]}),
        encoding="utf-8",
    )

    assert module.load_baseline(compact) == {"alpha": 0.25, "beta": 0.5}
    assert module.load_baseline(report) == {"gamma": 1.25}


def test_main_writes_performance_outputs(tmp_path: Path, capsys) -> None:
    module = load_performance_module()
    policy = tmp_path / "policy.json"
    report_dir = tmp_path / "reports" / "template-performance"
    policy.write_text(
        json.dumps(
            {
                "version": "test",
                "checks": [
                    {
                        "id": "command_probe",
                        "title": "Command probe",
                        "probe": "command",
                        "command": ["{python}", "-c", "print('performance-ok')"],
                        "warning_seconds": 5,
                        "critical_seconds": 10,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.main(["--repo-root", str(tmp_path), "--policy", str(policy), "--report-dir", str(report_dir)])
    output = capsys.readouterr().out

    assert result == 0
    assert "Performance status: pass" in output
    payload = json.loads((report_dir / "latest.json").read_text(encoding="utf-8"))
    markdown = (report_dir / "latest.md").read_text(encoding="utf-8")
    assert payload["status"] == "pass"
    assert payload["results"][0]["id"] == "command_probe"
    assert "# Template Performance Report" in markdown


def test_performance_policy_rejects_invalid_thresholds() -> None:
    module = load_performance_module()

    try:
        _policy(
            module,
            [
                {
                    "id": "invalid",
                    "title": "Invalid",
                    "probe": "template_registry_records",
                    "warning_seconds": 2,
                    "critical_seconds": 1,
                }
            ],
        )
    except module.PerformanceHarnessError as exc:
        assert "critical_seconds" in str(exc)
    else:  # pragma: no cover - defensive assertion branch
        raise AssertionError("invalid threshold policy should fail")


def test_guard_workflows_generate_and_upload_performance_reports() -> None:
    codex_guard = (REPO_ROOT / ".github" / "workflows" / "codex-guard.yml").read_text(encoding="utf-8")
    meta_guard = (REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml").read_text(encoding="utf-8")

    assert "python3 scripts/template-performance-harness --strict" in codex_guard
    assert "reports/template-performance/" in codex_guard
    assert "python3 scripts/template-performance-harness --strict" in meta_guard
    assert "reports/template-performance/" in meta_guard
