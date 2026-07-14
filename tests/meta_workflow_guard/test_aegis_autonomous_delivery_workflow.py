"""Security-contract tests for trusted evidence-gated autonomous delivery."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "aegis-autonomous-delivery.yml"
PR269_REVIEW_PAGES_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "aegis" / "pr269-review-pages.jsonl"
)


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _review_aggregation_filters() -> list[str]:
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    filters = re.findall(
        r"jq -s '(\{\n\s+unresolved_threads:.*?\n\s+\})' "
        r'"\$RUNNER_TEMP/(?:final-)?review-pages\.jsonl"',
        workflow_text,
        flags=re.DOTALL,
    )
    assert len(filters) == 3
    return filters


def _run_review_filter(filter_text: str, payload: str) -> dict:
    result = subprocess.run(
        ["jq", "-s", filter_text],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


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
    evaluator = workflow["jobs"]["delivery"]
    executor = workflow["jobs"]["merge"]

    assert workflow["permissions"] == {}
    assert evaluator["permissions"] == {
        "actions": "read",
        "contents": "read",
        "pull-requests": "read",
    }
    assert executor["permissions"] == {
        "actions": "read",
        "checks": "read",
        "contents": "write",
        "pull-requests": "write",
    }


def test_privileged_workflow_shell_steps_are_syntactically_valid() -> None:
    for job_name, job in _workflow()["jobs"].items():
        for step in job["steps"]:
            if "run" not in step or step.get("shell", "bash") != "bash":
                continue
            result = subprocess.run(
                ["bash", "-n"],
                input=step["run"],
                text=True,
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0, f"{job_name}/{step.get('name')}: {result.stderr}"


def test_privileged_workflow_executes_only_trusted_default_branch_code() -> None:
    workflow = _workflow()
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    checkouts = [
        step
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    ]

    assert len(checkouts) == 2
    for checkout in checkouts:
        assert checkout["uses"] == "actions/checkout@v6"
        assert checkout["with"] == {
            "ref": "${{ github.event.repository.default_branch }}",
            "path": "trusted",
            "fetch-depth": 1,
            "persist-credentials": False,
        }
    assert "trusted/scripts/aegis-delivery-policy" in text
    assert "actions/download-artifact" not in text
    assert "github.event.pull_request.head.ref" not in text
    assert all(
        "github.event.pull_request.head.sha }}" not in checkout["with"]["ref"]
        for checkout in checkouts
    )


def test_required_evaluator_is_read_only_and_executor_waits_for_it() -> None:
    workflow = _workflow()
    evaluator = workflow["jobs"]["delivery"]
    executor = workflow["jobs"]["merge"]
    evaluator_text = "\n".join(str(step.get("run", "")) for step in evaluator["steps"])

    assert evaluator["name"] == "evidence-gated delivery"
    assert evaluator["outputs"] == {
        "candidate_eligible": "${{ steps.candidate.outputs.eligible }}",
        "pr_number": "${{ steps.candidate.outputs.number }}",
        "expected_head": "${{ steps.candidate.outputs.expected_head }}",
        "decision": "${{ steps.policy.outputs.decision }}",
    }
    assert executor["needs"] == "delivery"
    assert "needs.delivery.outputs.candidate_eligible == 'true'" in executor["if"]
    assert "needs.delivery.outputs.decision == 'allow'" in executor["if"]
    assert "needs.delivery.outputs.decision == 'provisional'" in executor["if"]
    assert "pulls/${PR_NUMBER}/merge" not in evaluator_text
    assert "repos/${REPOSITORY}/dispatches" not in evaluator_text


def test_each_policy_decision_uses_complete_current_evidence() -> None:
    workflow = _workflow()
    evaluator_text = "\n".join(
        str(step.get("run", "")) for step in workflow["jobs"]["delivery"]["steps"]
    )
    executor_text = "\n".join(
        str(step.get("run", "")) for step in workflow["jobs"]["merge"]["steps"]
    )

    assert "commits/${expected_head}/pulls?per_page=100" in evaluator_text
    for text in (evaluator_text, executor_text):
        assert "pulls/${PR_NUMBER}/files?per_page=100" in text
        assert "actions/runs?event=pull_request&head_sha=${EXPECTED_HEAD}&per_page=100" in text
        assert "gh api graphql --paginate" in text
        assert "reviewThreads(first: 100, after: $endCursor)" in text
        assert "unresolved_threads" in text
        assert "threads_truncated" in text
        assert "git -C trusted rev-parse HEAD" in text
        assert "aegis-delivery-evidence.json" in text
    assert "commits/${EXPECTED_HEAD}/check-runs?" not in evaluator_text
    assert executor_text.count("commits/${EXPECTED_HEAD}/check-runs?") == 2
    assert executor_text.count("commits/${EXPECTED_HEAD}/statuses?") == 2
    assert executor_text.count('"repos/${REPOSITORY}/actions/runs/${EXECUTOR_RUN_ID}"') == 2
    assert executor_text.count('"repos/${REPOSITORY}/actions/runs/${EXECUTOR_RUN_ID}/jobs?') == 2
    assert executor_text.count("--phase executor") == 2
    assert executor_text.count('--executor-run-id "$EXECUTOR_RUN_ID"') == 2
    assert "check_runs_complete: true" in executor_text
    assert "status_contexts_complete: true" in executor_text
    assert executor_text.count("executor_jobs_complete") == 2
    assert "executor_run: $executor_run[0]" in executor_text
    assert ".executor_run = $executor_run[0]" in executor_text
    assert "executor_jobs: $executor_jobs[0]" in executor_text
    assert ".executor_jobs = $executor_jobs[0]" in executor_text
    assert "final-aegis-delivery-evidence.json" in executor_text


def test_executor_identity_comes_from_its_trusted_run_not_candidate_checks() -> None:
    workflow = _workflow()
    executor = workflow["jobs"]["merge"]
    text = "\n".join(str(step.get("run", "")) for step in executor["steps"])
    recollect = next(
        step
        for step in executor["steps"]
        if step.get("name") == "Recollect exact-head repository evidence after required check"
    )
    merge = next(
        step
        for step in executor["steps"]
        if step.get("name") == "Squash-merge freshly authorized exact head"
    )

    assert executor["permissions"]["actions"] == "read"
    assert recollect["env"]["EXECUTOR_RUN_ID"] == "${{ github.run_id }}"
    assert merge["env"]["EXECUTOR_RUN_ID"] == "${{ github.run_id }}"
    assert "actions/runs/${EXECUTOR_RUN_ID}/jobs?per_page=100&filter=latest" in text
    assert "--jq '.jobs | map({" in text
    assert "head_repository: {full_name: .head_repository.full_name}" in text
    assert "executor_jobs_complete: true" in text
    assert "commits/${EXPECTED_HEAD}/check-runs?" in text


def test_review_pagination_uses_the_real_final_page_in_both_jobs() -> None:
    payload = PR269_REVIEW_PAGES_FIXTURE_PATH.read_text(encoding="utf-8")

    for filter_text in _review_aggregation_filters():
        assert "last.data" not in filter_text
        assert ".[-1].data" in filter_text
        assert "// true" not in filter_text
        assert _run_review_filter(filter_text, payload) == {
            "unresolved_threads": 0,
            "threads_truncated": False,
            "decision": "",
        }


def test_review_pagination_fails_closed_when_no_page_was_returned() -> None:
    for filter_text in _review_aggregation_filters():
        assert _run_review_filter(filter_text, "") == {
            "unresolved_threads": 0,
            "threads_truncated": True,
            "decision": "",
        }


def test_provisional_result_cannot_authorize_a_merge() -> None:
    workflow = _workflow()
    evaluator_text = "\n".join(
        str(step.get("run", "")) for step in workflow["jobs"]["delivery"]["steps"]
    )
    executor_text = "\n".join(
        str(step.get("run", "")) for step in workflow["jobs"]["merge"]["steps"]
    )

    assert "allow|provisional|attended|defer|deny" in evaluator_text
    assert "jq -c '.reasons'" in evaluator_text
    assert 'if [[ "$decision" != "allow" ]]' in executor_text
    assert "Fresh executor decision was ${decision}; refusing merge." in executor_text
    assert "Final executor decision was ${final_decision}; refusing merge." in executor_text
    assert executor_text.count("aegis-delivery-policy evaluate") == 2
    assert executor_text.index("aegis-delivery-policy evaluate") < executor_text.index(
        'if [[ "$decision" != "allow" ]]'
    )
    assert executor_text.index('if [[ "$decision" != "allow" ]]') < executor_text.index(
        '"repos/${REPOSITORY}/pulls/${PR_NUMBER}/merge"'
    )


def test_workflow_merges_only_allow_at_unchanged_head_and_base() -> None:
    workflow = _workflow()
    evaluator_text = "\n".join(
        str(step.get("run", "")) for step in workflow["jobs"]["delivery"]["steps"]
    )
    text = "\n".join(str(step.get("run", "")) for step in workflow["jobs"]["merge"]["steps"])

    assert "pulls/${PR_NUMBER}/merge" not in evaluator_text
    assert 'if [[ "$decision" != "allow" ]]' in text
    assert '[[ "$final_head" != "$EXPECTED_HEAD" ]]' in text
    assert '[[ "$final_base" != "$trusted_base" ]]' in text
    assert '.state == "open"' in text
    assert "(.draft | not)" in text
    assert ".mergeable == true" in text
    assert '.mergeable_state == "clean"' in text
    assert '.mergeable_state == "blocked"' in text
    assert '.mergeable_state == "unstable"' in text
    assert 'if [[ "$final_decision" != "allow" ]]' in text
    assert text.rindex('if [[ "$final_decision" != "allow" ]]') < text.index(
        '"repos/${REPOSITORY}/pulls/${PR_NUMBER}/merge"'
    )
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
