"""Regression tests for GitHub Actions CI workflow contracts."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
CODEX_GUARD_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "codex-guard.yml"
META_GUARD_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml"


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


def test_python_test_workflow_provisions_pinned_taskmaster_before_pytest() -> None:
    workflow = _load_workflow()
    steps = workflow["jobs"]["python-tests"]["steps"]
    step_names = [step.get("name") for step in steps]
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "Set up Node for Taskmaster CLI" in step_names
    assert "Provision pinned Taskmaster CLI" in step_names
    assert "Run pytest" in step_names
    assert step_names.index("Provision pinned Taskmaster CLI") < step_names.index("Run pytest")
    assert "python3 -m aegis_foundation.taskmaster_toolchain install-spec" in text
    assert 'npm install -g "$TASKMASTER_INSTALL_SPEC"' in text
    assert "taskmaster-toolchain.json" in text


def test_python_test_workflow_captures_shadow_cascade_validation_artifact() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "Capture reconcile shadow cascade validation" in text
    assert "build_ci_shadow_cascade_validation_report" in text
    assert "capture_taskmaster_toolchain_evidence" in text
    assert "reconcile-shadow-cascade-validation.json" in text
    assert "task-master set-status" not in text
    assert "--apply" not in text


def test_python_test_workflow_captures_shadow_accumulation_with_side_effect_oracle() -> None:
    workflow = _load_workflow()
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    steps = workflow["jobs"]["python-tests"]["steps"]
    step_names = [step.get("name") for step in steps]

    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["python-tests"]["permissions"] == {"contents": "read"}
    assert all(
        job.get("permissions", {"contents": "read"}).get("contents") != "write"
        for job in workflow["jobs"].values()
    )
    assert "Capture post-merge reconcile shadow accumulation" in step_names
    assert "build_shadow_accumulation_report" in text
    assert "reconcile-shadow-accumulation.json" in text
    assert "PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'" in text
    assert "snapshot_whole_tree(repo, require_tmp_root=False)" in text
    assert "before.assert_matches" in text
    assert 'report_dir = Path(os.environ["RUNNER_TEMP"]) / "aegis-shadow"' in text
    assert "before.assert_matches(snapshot_whole_tree(repo, require_tmp_root=False))" in text
    assert '"valid_for_shadow": context["valid_for_shadow"]' in text
    assert "if context[\"valid_for_shadow\"]:" in text
    assert "reports/ci/" in text
    assert "${{ runner.temp }}/aegis-shadow/" in text
    assert "task-master set-status" not in text
    assert "--apply" not in text


def test_python_test_workflow_uploads_matrix_artifacts() -> None:
    workflow = _load_workflow()
    steps = workflow["jobs"]["python-tests"]["steps"]

    assert any(step.get("uses") == "actions/upload-artifact@v4" for step in steps)
    assert "reports/ci/" in CI_WORKFLOW.read_text(encoding="utf-8")


def test_guard_workflows_fail_when_automatic_reference_fixes_are_pending() -> None:
    codex_guard = CODEX_GUARD_WORKFLOW.read_text(encoding="utf-8")
    meta_guard = META_GUARD_WORKFLOW.read_text(encoding="utf-8")

    for workflow_text in (codex_guard, meta_guard):
        assert "Verify no automatic reference fixes are pending" in workflow_text
        assert "python3 scripts/template-ssot-scanner/apply_reference_fixes.py" in workflow_text
        assert "--dry-run" in workflow_text
        assert "--fail-on-changes" in workflow_text
        assert "--log-file reports/reference-fix-gate/latest.json" in workflow_text
        assert "reports/reference-fix-gate/" in workflow_text
