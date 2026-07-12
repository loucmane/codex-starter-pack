"""Security-contract tests for trusted evidence-gated autonomous delivery."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "aegis-autonomous-delivery.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_privileged_workflow_has_narrow_triggers_and_serial_delivery() -> None:
    workflow = _workflow()
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert workflow["name"] == "Aegis Autonomous Delivery"
    assert "workflow_run:" in text
    assert "pull_request_target:" in text
    assert "\n  pull_request:\n" not in text
    assert "types: [opened, reopened, synchronize, ready_for_review, labeled, unlabeled]" in text
    assert "workflows: [CI, Codex Guard, Meta Workflow Guard, aegis-witness]" in text
    assert workflow["concurrency"]["cancel-in-progress"] is False
    assert workflow["concurrency"]["group"] == "aegis-autonomous-delivery-${{ github.repository }}"


def test_privileged_workflow_uses_only_required_permissions() -> None:
    workflow = _workflow()
    job = workflow["jobs"]["delivery"]

    assert workflow["permissions"] == {}
    assert job["permissions"] == {
        "actions": "read",
        "contents": "write",
        "pull-requests": "write",
    }


def test_privileged_workflow_shell_steps_are_syntactically_valid() -> None:
    steps = _workflow()["jobs"]["delivery"]["steps"]

    for step in steps:
        if "run" not in step or step.get("shell", "bash") != "bash":
            continue
        result = subprocess.run(
            ["bash", "-n"],
            input=step["run"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{step.get('name')}: {result.stderr}"


def test_privileged_workflow_executes_only_trusted_default_branch_code() -> None:
    workflow = _workflow()
    steps = workflow["jobs"]["delivery"]["steps"]
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    checkouts = [step for step in steps if step.get("uses", "").startswith("actions/checkout@")]

    assert len(checkouts) == 1
    assert checkouts[0]["uses"] == "actions/checkout@v6"
    assert checkouts[0]["with"] == {
        "ref": "${{ github.event.repository.default_branch }}",
        "path": "trusted",
        "fetch-depth": 1,
        "persist-credentials": False,
    }
    assert "trusted/scripts/aegis-delivery-policy" in text
    assert "actions/download-artifact" not in text
    assert "github.event.pull_request.head.ref" not in text
    assert "github.event.pull_request.head.sha }}" not in checkouts[0]["with"]["ref"]


def test_workflow_collects_complete_current_evidence_before_policy_evaluation() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "commits/${expected_head}/pulls?per_page=100" in text
    assert "pulls/${PR_NUMBER}/files?per_page=100" in text
    assert "actions/runs?event=pull_request&head_sha=${EXPECTED_HEAD}&per_page=100" in text
    assert "gh api graphql --paginate" in text
    assert "reviewThreads(first: 100, after: $endCursor)" in text
    assert "unresolved_threads" in text
    assert "threads_truncated" in text
    assert "git -C trusted rev-parse HEAD" in text
    assert "aegis-delivery-evidence.json" in text


def test_workflow_merges_only_allow_at_unchanged_head_and_base() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "if: steps.policy.outputs.decision == 'allow'" in text
    assert '[[ "$final_head" != "$EXPECTED_HEAD" ]]' in text
    assert '[[ "$final_base" != "$trusted_base" ]]' in text
    assert '"repos/${REPOSITORY}/pulls/${PR_NUMBER}/merge"' in text
    assert "-f merge_method=squash" in text
    assert '-f sha="$EXPECTED_HEAD"' in text
    assert "--admin" not in text
    assert "force-push" not in text
    assert "git reset" not in text
    assert "git rebase" not in text
    assert "git push" not in text


def test_policy_merge_dispatches_exact_merge_sha_to_post_merge_guards() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    guarded_workflows = (
        REPO_ROOT / ".github" / "workflows" / "ci.yml",
        REPO_ROOT / ".github" / "workflows" / "codex-guard.yml",
        REPO_ROOT / ".github" / "workflows" / "meta-workflow-guard.yml",
    )

    assert 'event_type: "aegis-autonomous-delivery"' in text
    assert "merge_sha=\"$(jq -r '.sha'" in text
    assert '"repos/${REPOSITORY}/dispatches"' in text
    assert '--input "$RUNNER_TEMP/post-merge-dispatch.json"' in text
    for path in guarded_workflows:
        workflow_text = path.read_text(encoding="utf-8")
        guarded_workflow = yaml.safe_load(workflow_text)
        job = next(iter(guarded_workflow["jobs"].values()))
        bind_step = next(
            step
            for step in job["steps"]
            if step.get("name") == "Bind repository-dispatch branch identity"
        )
        assert "repository_dispatch:" in workflow_text
        assert "types: [aegis-autonomous-delivery]" in workflow_text
        assert "ref: ${{ github.event.client_payload.merge_sha || github.sha }}" in workflow_text
        assert "Bind repository-dispatch branch identity" in workflow_text
        assert '[[ "$MERGE_SHA" =~ ^[0-9a-f]{40}$ ]]' in workflow_text
        assert 'git switch -C "$DEFAULT_BRANCH" "$MERGE_SHA"' in workflow_text
        syntax = subprocess.run(
            ["bash", "-n"],
            input=bind_step["run"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert syntax.returncode == 0, f"{path.name}: {syntax.stderr}"


def test_bootstrap_and_policy_changes_cannot_self_authorize() -> None:
    policy_text = (REPO_ROOT / "aegis.delivery-policy.json").read_text(encoding="utf-8")

    assert '".github/workflows/**"' in policy_text
    assert '"aegis.delivery-policy.json"' in policy_text
    assert '"scripts/aegis-delivery-policy"' in policy_text
    assert '"scripts/_aegis_installer.py"' in policy_text
    assert '"aegis_foundation/assets/scripts/_aegis_installer.py"' in policy_text
