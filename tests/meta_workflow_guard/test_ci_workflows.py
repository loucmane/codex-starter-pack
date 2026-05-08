"""Regression tests for GitHub Actions CI workflow contracts."""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))


def test_python_test_workflow_has_version_matrix() -> None:
    workflow = _load_workflow()
    matrix = workflow["jobs"]["python-tests"]["strategy"]["matrix"]

    assert matrix["python-version"] == ["3.11", "3.12"]
    assert workflow["jobs"]["python-tests"]["strategy"]["fail-fast"] is False


def test_python_test_workflow_runs_full_pytest_and_taskmaster_health() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "python3 scripts/codex-task taskmaster health" in text
    assert "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest" in text
    assert "scripts/template-ssot-scanner" not in text, "pytest config should own test discovery"


def test_python_test_workflow_installs_runtime_and_dev_dependencies() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert 'data["project"]["dependencies"]' in text
    assert 'data.get("dependency-groups", {}).get("dev", [])' in text
    assert "python3 -m pip install -r /tmp/codex-ci-dependencies.txt" in text


def test_python_test_workflow_uploads_matrix_artifacts() -> None:
    workflow = _load_workflow()
    steps = workflow["jobs"]["python-tests"]["steps"]

    assert any(step.get("uses") == "actions/upload-artifact@v4" for step in steps)
    assert "reports/ci/" in CI_WORKFLOW.read_text(encoding="utf-8")
