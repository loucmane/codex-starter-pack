"""Regression tests for the static cost tracking report."""

from __future__ import annotations

import importlib.util
import importlib.machinery
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_cost_module():
    name = "template_cost_report_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/template-cost-report")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def _policy_payload() -> dict:
    return {
        "version": "test",
        "defaults": {
            "warning_ratio": 0.8,
            "critical_ratio": 1.0,
        },
        "categories": [
            {
                "id": "ai_taskmaster_commands",
                "title": "AI Taskmaster",
                "description": "AI calls",
                "unit": "usd",
                "monthly_budget": 100,
                "telemetry": "manual",
                "review_commands": ["task-master models"],
                "notes": ["manual ledger"],
            },
            {
                "id": "github_actions_minutes",
                "title": "GitHub Actions",
                "description": "CI minutes",
                "unit": "minutes",
                "monthly_budget": 1000,
                "telemetry": "external",
            },
            {
                "id": "report_storage",
                "title": "Report storage",
                "description": "Artifact storage",
                "unit": "mb",
                "monthly_budget": 500,
                "telemetry": "local",
            },
            {
                "id": "local_agent_runtime",
                "title": "Local runtime",
                "description": "Local verification time",
                "unit": "hours",
                "monthly_budget": 40,
                "telemetry": "manual",
            },
        ],
        "recommended_review_commands": ["python3 scripts/codex-task report generate --kind all"],
        "non_goals": ["No external billing API is queried."],
    }


def test_cost_policy_evaluates_pass_warn_fail_and_unmeasured() -> None:
    module = load_cost_module()
    policy = module.CostPolicy.from_mapping(_policy_payload())
    usage = {
        "ai_taskmaster_commands": module.UsageEntry(actual_amount=25, source="manual"),
        "github_actions_minutes": module.UsageEntry(projected_monthly_amount=850, source="gh"),
        "report_storage": module.UsageEntry(actual_amount=510, source="du"),
    }

    report = module.evaluate_policy(policy, usage_entries=usage, usage_source="test-ledger.json")

    assert report.status == "fail"
    assert report.summary == {
        "total": 4,
        "passed": 1,
        "warnings": 1,
        "errors": 1,
        "not_measured": 1,
    }
    statuses = {result.id: result.status for result in report.results}
    assert statuses == {
        "ai_taskmaster_commands": "pass",
        "github_actions_minutes": "warn",
        "report_storage": "fail",
        "local_agent_runtime": "not-measured",
    }
    ratios = {result.id: result.budget_ratio for result in report.results}
    assert ratios["github_actions_minutes"] == 0.85
    assert ratios["report_storage"] == 1.02


def test_cost_report_writes_json_and_markdown(tmp_path: Path, capsys) -> None:
    module = load_cost_module()
    policy_path = tmp_path / "templates" / "metadata" / "template-cost-policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(_policy_payload()), encoding="utf-8")
    usage_path = tmp_path / "usage.json"
    usage_path.write_text(
        json.dumps(
            {
                "categories": {
                    "ai_taskmaster_commands": {
                        "actual_amount": 10,
                        "projected_monthly_amount": 50,
                        "source": "manual-ledger",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    report_dir = tmp_path / "reports" / "cost-tracking"

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--policy",
            str(policy_path.relative_to(tmp_path)),
            "--usage-file",
            str(usage_path.relative_to(tmp_path)),
            "--report-dir",
            str(report_dir.relative_to(tmp_path)),
            "--strict",
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "Cost status: warn" in output
    payload = json.loads((report_dir / "latest.json").read_text(encoding="utf-8"))
    markdown = (report_dir / "latest.md").read_text(encoding="utf-8")
    assert payload["status"] == "warn"
    assert payload["executes_external_actions"] is False
    assert payload["usage_source"] == "usage.json"
    assert "# Cost Tracking Report" in markdown
    assert "No external billing query" in markdown


def test_cost_report_strict_fails_only_on_budget_errors(tmp_path: Path) -> None:
    module = load_cost_module()
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy_payload()), encoding="utf-8")
    usage_path = tmp_path / "usage.json"
    usage_path.write_text(
        json.dumps({"categories": {"ai_taskmaster_commands": {"actual_amount": 120}}}),
        encoding="utf-8",
    )

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--usage-file",
            str(usage_path),
            "--report-dir",
            str(tmp_path / "reports"),
            "--strict",
        ]
    )

    assert result == 1


def test_cost_policy_rejects_invalid_thresholds() -> None:
    module = load_cost_module()
    payload = _policy_payload()
    payload["categories"][0]["critical_ratio"] = 0.5

    try:
        module.CostPolicy.from_mapping(payload)
    except module.CostReportError as exc:
        assert "critical_ratio must be >= warning_ratio" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("expected invalid threshold error")


def test_real_cost_policy_loads() -> None:
    module = load_cost_module()
    policy = module.load_cost_policy(REPO_ROOT / "templates" / "metadata" / "template-cost-policy.json")

    assert policy.version == "1.0.0"
    assert {category.id for category in policy.categories} >= {
        "ai_taskmaster_commands",
        "github_actions_minutes",
        "local_agent_runtime",
        "report_storage",
    }


def test_guard_workflows_generate_and_upload_cost_reports() -> None:
    codex_guard = (REPO_ROOT / ".github" / "workflows" / "codex-guard.yml").read_text(encoding="utf-8")
    meta_guard = (REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml").read_text(encoding="utf-8")

    assert "python3 scripts/template-cost-report --strict" in codex_guard
    assert "reports/cost-tracking/" in codex_guard
    assert "python3 scripts/template-cost-report --strict" in meta_guard
    assert "reports/cost-tracking/" in meta_guard
