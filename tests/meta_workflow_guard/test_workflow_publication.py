"""Candidate delivery is not terminal acceptance; use real Git, never a live ledger."""

import copy
import json
import subprocess
from pathlib import Path

import pytest

from tests.meta_workflow_guard.test_gas_city_workflow_transitions import (
    MultiBeadRunner,
    _bead,
    _fixture_project,
    _run,
)
from workflow import _finish, _publish
from workflow_attach import attach
from workflow_begin import begin
from workflow_common import WorkflowError
from workflow_ownership import OWNER_KEY


class PublicationRunner(MultiBeadRunner):
    """Stub signature success only; negative coverage uses real unsigned Git proof."""

    signature_success = True
    after_signature = None
    after_archive = None

    def run(self, argv, *, cwd=None, env=None, check=True):
        args = list(argv)
        if "verify-commit" in args and self.signature_success:
            self.calls.append(args)
            if self.after_signature:
                self.after_signature()
            return subprocess.CompletedProcess(args, 0, "fixture signature verified", "")
        if "work-tracking" in args and "archive" in args:
            self.calls.append(args)
            if self.after_archive:
                self.after_archive()
            return subprocess.CompletedProcess(args, 0, "fixture archived", "")
        return super().run(args, cwd=cwd, env=env, check=check)


def _commit_fixture(root):
    _run(root, "git", "add", ".")
    _run(
        root,
        "git",
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "scaffold fixture",
    )


@pytest.fixture
def lane(tmp_path):
    root, registry = _fixture_project(tmp_path)
    runner = PublicationRunner({"ga-test": _bead(), "ga-fix": _bead(bead_id="ga-fix")}, "ga-test")
    started = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)
    target = Path(started["spec"]["worktree"])
    runner.beads["ga-test"]["dependencies"] = [
        {"id": "ga-fix", "status": "in_progress", "dependency_type": "blocks"}
    ]
    attach(target, "ga-fix", runner, registry=registry)
    _commit_fixture(target)
    runner.calls.clear()
    return target, runner, Path(started["journal"])


def _events(path, action):
    return [item for item in json.loads(path.read_text())["events"] if item["action"] == action]


def _assert_no_ledger_mutation(runner):
    calls = [args for args in runner.calls if args[0].endswith("/gc")]
    assert calls
    assert all(args[args.index("bd") + 1] == "show" for args in calls)


@pytest.mark.parametrize("repair_status", ["in_progress", "closed"])
def test_publish_owned_attached_candidate_without_closing_any_bead(lane, repair_status):
    root, runner, path = lane
    runner.beads["ga-fix"]["status"] = repair_status
    runner.beads["ga-test"]["dependencies"][0]["status"] = repair_status
    before = copy.deepcopy(runner.beads)
    result = _publish(root, runner)
    assert result["action"] == "publish" and result["status"] == "ready"
    assert result["head"] == _run(root, "git", "rev-parse", "HEAD").stdout.strip()
    assert result["tree"] == _run(root, "git", "rev-parse", "HEAD^{tree}").stdout.strip()
    assert [args for args in runner.calls if "verify-commit" in args] == [
        ["git", "-C", str(root), "verify-commit", result["head"]]
    ]
    assert _events(path, "publish")[-1]["head"] == result["head"]
    assert not _events(path, "finish")
    assert runner.beads == before
    assert not _run(root, "git", "status", "--porcelain=v1").stdout
    _assert_no_ledger_mutation(runner)


@pytest.mark.parametrize("bead_id", ["ga-test", "ga-fix"])
@pytest.mark.parametrize("fault", ["assignee", "binding", "native", "route", "reopened"])
def test_publish_still_refuses_primary_and_attached_ownership_drift(lane, bead_id, fault):
    root, runner, path = lane
    bead = runner.beads[bead_id]
    if fault == "assignee":
        bead["assignee"] = "ci-unexpected"
    elif fault == "binding":
        bead["metadata"][OWNER_KEY] = "external-coordinator.v1:" + "0" * 64
    elif fault == "native":
        bead["metadata"]["gc.session_id"] = "ci-unexpected"
    elif fault == "route":
        bead["labels"] = ["route:unexpected"]
    else:
        bead["status"] = "open"
    before = copy.deepcopy(runner.beads)
    with pytest.raises(WorkflowError):
        _publish(root, runner)
    assert not _events(path, "publish")
    assert runner.beads == before
    _assert_no_ledger_mutation(runner)


@pytest.mark.parametrize("bead_id", ["ga-test", "ga-fix"])
def test_publish_does_not_waive_unattached_or_transitive_blockers(lane, bead_id):
    root, runner, path = lane
    runner.beads[bead_id]["dependencies"].append(
        {"id": "ga-unrelated", "status": "in_progress", "dependency_type": "blocks"}
    )
    with pytest.raises(WorkflowError, match="dependencies"):
        _publish(root, runner)
    assert not _events(path, "publish")
    _assert_no_ledger_mutation(runner)


@pytest.mark.parametrize("fault", ["plan", "journal-owner", "branch", "rig"])
def test_publish_retains_worktree_plan_journal_and_project_binding(lane, fault):
    root, runner, path = lane
    if fault == "plan":
        plan = root / "plans/current"
        plan.write_text(
            plan.read_text().replace("attached_bead_ids: [ga-fix]", "attached_bead_ids: []")
        )
    elif fault == "journal-owner":
        journal = json.loads(path.read_text())
        journal["external_ownership"]["ga-fix"]["state"] = "pending"
        path.write_text(json.dumps(journal))
    elif fault == "branch":
        _run(root, "git", "branch", "-m", "codex/ga-test-unbound")
    else:
        descriptor = root / ".gas-city-workflow.json"
        value = json.loads(descriptor.read_text())
        value["rig"] = "wrong-rig"
        descriptor.write_text(json.dumps(value))
    with pytest.raises(WorkflowError):
        _publish(root, runner)
    assert not _events(path, "publish")


@pytest.mark.parametrize("staged", [False, True])
def test_publish_still_requires_clean_git(lane, staged):
    root, runner, path = lane
    (root / "dirty.txt").write_text("uncommitted candidate\n")
    if staged:
        _run(root, "git", "add", "dirty.txt")
    with pytest.raises(WorkflowError, match="clean worktree"):
        _publish(root, runner)
    assert not _events(path, "publish")
    assert not any("verify-commit" in args for args in runner.calls)


def test_publish_rejects_real_unsigned_commit(lane):
    root, runner, path = lane
    runner.signature_success = False
    with pytest.raises(WorkflowError, match="verify-commit"):
        _publish(root, runner)
    assert any("verify-commit" in args for args in runner.calls)
    assert not _events(path, "publish")


@pytest.mark.parametrize("check", ["readiness", "guard"])
def test_publish_still_runs_readiness_and_source_guard(lane, check):
    root, runner, path = lane
    target = root / (
        ".claude/scripts/readiness.sh" if check == "readiness" else "scripts/codex-guard"
    )
    target.write_text(
        "#!/usr/bin/env bash\necho 'STATE: BLOCKED'\nexit 2\n"
        if check == "readiness"
        else "raise SystemExit(2)\n"
    )
    _commit_fixture(root)
    with pytest.raises(WorkflowError):
        _publish(root, runner)
    assert any(str(target) in args for args in runner.calls)
    assert not any("verify-commit" in args for args in runner.calls)
    assert not _events(path, "publish")


def test_publish_cannot_use_closed_primary_or_native_session(lane, monkeypatch):
    root, runner, path = lane
    runner.beads["ga-test"]["status"] = "closed"
    with pytest.raises(WorkflowError, match="in_progress"):
        _publish(root, runner)
    runner.beads["ga-test"]["status"] = "in_progress"
    monkeypatch.setenv("GC_SESSION_ID", "ci-fixture")
    with pytest.raises(WorkflowError, match="native sessions"):
        _publish(root, runner)
    assert not _events(path, "publish")


@pytest.mark.parametrize("fault", ["binding", "unattached-blocker"])
def test_publish_rechecks_live_ownership_after_signature_verification(lane, fault):
    root, runner, path = lane

    def drift():
        if fault == "binding":
            runner.beads["ga-fix"]["metadata"][OWNER_KEY] = "changed"
        else:
            runner.beads["ga-test"]["dependencies"].append(
                {"id": "ga-new", "status": "open", "dependency_type": "blocks"}
            )

    runner.after_signature = drift
    with pytest.raises(WorkflowError):
        _publish(root, runner)
    assert any("verify-commit" in args for args in runner.calls)
    assert not _events(path, "publish")
    _assert_no_ledger_mutation(runner)


@pytest.mark.parametrize("apply", [False, True])
def test_finish_still_requires_attached_repairs_closed_before_archive(lane, apply):
    root, runner, path = lane
    before = path.read_bytes()
    with pytest.raises(WorkflowError, match="dependencies"):
        _finish(root, runner, apply=apply)
    assert path.read_bytes() == before
    assert not any("archive" in args for args in runner.calls)
    _assert_no_ledger_mutation(runner)


def test_finish_closed_dependency_can_plan_but_rechecks_after_archive(lane):
    root, runner, path = lane
    runner.beads["ga-fix"]["status"] = "closed"
    runner.beads["ga-test"]["dependencies"][0]["status"] = "closed"
    assert _finish(root, runner, apply=False)["status"] == "planned"

    def reopen():
        runner.beads["ga-fix"]["status"] = "in_progress"
        runner.beads["ga-test"]["dependencies"][0]["status"] = "in_progress"

    runner.after_archive = reopen
    with pytest.raises(WorkflowError, match="dependencies"):
        _finish(root, runner, apply=True)
    assert [item["status"] for item in _events(path, "finish")] == ["planned"]
    _assert_no_ledger_mutation(runner)
