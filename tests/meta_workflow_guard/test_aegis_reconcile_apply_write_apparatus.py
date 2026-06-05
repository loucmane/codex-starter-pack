"""Default-off reconcile apply write-apparatus tests."""

from __future__ import annotations

import ast
import json
import shutil
import threading
from pathlib import Path
from typing import Any, Iterable

import pytest

from aegis_foundation.reconcile_apply_runtime import (
    FileIdempotencyStore,
    SnapshotRollbackHandle,
    run_reconcile_apply_write_apparatus,
)
from aegis_foundation.reconcile_apply_scaffold import (
    FIRST_APPLY_CLASS_KEY,
    authorization_binding_for,
    idempotency_key_for,
)
from aegis_foundation.reconcile_shadow_apply import (
    _predicted_paths,
    _proof_artifact,
    _write_ci_validation_taskmaster_fixture,
)
from aegis_foundation.taskmaster_toolchain import (
    TASKMASTER_PACKAGE_VERSION,
    build_taskmaster_toolchain_evidence,
)
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree
from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

FIRST_CANDIDATE = {
    "task_id": "42",
    "finding_kind": "merged_but_not_done",
    "proof": "git_ancestor",
    "current_status": "pending",
    "proposed_status": "done",
}
APPROVED_CONTEXT = {
    "context_type": "post_merge_ci",
    "proof_id": "run-153",
    "task_id": "42",
    "proof": "git_ancestor",
    "external_anchor": "github-actions://run/153",
}
ENABLED_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True}},
}
DISABLED_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True, "disabled": True}},
}


class FakeValidation:
    semantic_delta_matches_prediction = True
    semantic_validation = {"passed": True, "reason": "semantic_delta_matches_prediction"}

    def __init__(self, predicted_paths: Iterable[str], actual_paths: Iterable[str] | None = None):
        self.predicted_paths = tuple(sorted(predicted_paths))
        self.actual_delta_paths = tuple(sorted(actual_paths or predicted_paths))

    @property
    def matches_prediction(self) -> bool:
        return self.actual_delta_paths == self.predicted_paths


class SemanticMismatchValidation(FakeValidation):
    semantic_delta_matches_prediction = False
    semantic_validation = {"passed": False, "reason": "tasks_json_semantic_mismatch"}


class SemanticNoneValidation(FakeValidation):
    semantic_delta_matches_prediction = None
    semantic_validation = {"passed": None, "reason": "semantic_delta_missing"}


class MissingSemanticValidation:
    def __init__(self, predicted_paths: Iterable[str], actual_paths: Iterable[str] | None = None):
        self.predicted_paths = tuple(sorted(predicted_paths))
        self.actual_delta_paths = tuple(sorted(actual_paths or predicted_paths))

    @property
    def matches_prediction(self) -> bool:
        return self.actual_delta_paths == self.predicted_paths


class MissingPathPredictionValidation:
    semantic_delta_matches_prediction = True
    semantic_validation = {"passed": True, "reason": "semantic_delta_matches_prediction"}

    def __init__(self, predicted_paths: Iterable[str], actual_paths: Iterable[str] | None = None):
        self.predicted_paths = tuple(sorted(predicted_paths))
        self.actual_delta_paths = tuple(sorted(actual_paths or predicted_paths))


def test_default_config_full_apply_path_has_zero_live_delta(tmp_path: Path) -> None:
    target = _target(tmp_path / "default-off")
    before = snapshot_whole_tree(target)
    validation_calls = 0

    def validation_runner(**_: Any) -> FakeValidation:
        nonlocal validation_calls
        validation_calls += 1
        raise AssertionError("default-off must refuse before fresh validation")

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        audit_log_path=tmp_path / "audit" / "apply.jsonl",
        enable_write_path=False,
        validation_runner=validation_runner,
    )

    assert result.status == "refused"
    assert result.reason == "enable_gate_unsatisfiable"
    assert result.mutated is False
    assert validation_calls == 0
    assert not (tmp_path / "audit" / "apply.jsonl").exists()
    before.assert_matches(snapshot_whole_tree(target))


@pytest.mark.parametrize(
    ("candidate", "context", "kill_switch", "validated_version", "reason"),
    [
        (
            {**FIRST_CANDIDATE, "proof": "github_pr_merged"},
            APPROVED_CONTEXT,
            ENABLED_KILL_SWITCH,
            TASKMASTER_PACKAGE_VERSION,
            "candidate_outside_first_apply_class",
        ),
        (
            FIRST_CANDIDATE,
            None,
            ENABLED_KILL_SWITCH,
            TASKMASTER_PACKAGE_VERSION,
            "approved_context_missing",
        ),
        (
            FIRST_CANDIDATE,
            {**APPROVED_CONTEXT, "task_id": "99"},
            ENABLED_KILL_SWITCH,
            TASKMASTER_PACKAGE_VERSION,
            "approved_context_binding_mismatch",
        ),
        (
            FIRST_CANDIDATE,
            APPROVED_CONTEXT,
            DISABLED_KILL_SWITCH,
            TASKMASTER_PACKAGE_VERSION,
            "kill_switch_class_disabled",
        ),
        (
            FIRST_CANDIDATE,
            APPROVED_CONTEXT,
            ENABLED_KILL_SWITCH,
            "0.99.0",
            "toolchain_evidence_stale",
        ),
    ],
)
def test_remove_one_conjunct_refuses_before_mutation_and_expensive_validation(
    tmp_path: Path,
    candidate: dict[str, Any],
    context: dict[str, Any] | None,
    kill_switch: dict[str, Any],
    validated_version: str,
    reason: str,
) -> None:
    target = _target(tmp_path / "conjunct")
    before = snapshot_whole_tree(target)
    validation_calls = 0

    def validation_runner(**_: Any) -> FakeValidation:
        nonlocal validation_calls
        validation_calls += 1
        raise AssertionError("cheap denials must short-circuit before clone validation")

    result = run_reconcile_apply_write_apparatus(
        candidate,
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=kill_switch,
        validated_toolchain_evidence=_toolchain(version=validated_version),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=validation_runner,
    )

    assert result.status == "refused"
    assert result.reason == reason
    assert validation_calls == 0
    before.assert_matches(snapshot_whole_tree(target))


def test_fresh_validation_is_required_and_recorded_validation_is_not_a_license(
    tmp_path: Path,
) -> None:
    target = _target(tmp_path / "fresh-required")
    before = snapshot_whole_tree(target)

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=lambda **_: None,
    )

    assert result.status == "refused"
    assert result.reason == "fresh_validation_not_run"
    before.assert_matches(snapshot_whole_tree(target))


def test_fresh_validation_semantic_mismatch_refuses_before_write(tmp_path: Path) -> None:
    target = _target(tmp_path / "fresh-semantic")
    before = snapshot_whole_tree(target)

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=lambda **kwargs: SemanticMismatchValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
    )

    assert result.status == "refused"
    assert result.reason == "fresh_validation_semantic_mismatch"
    assert result.semantic_validation["reason"] == "tasks_json_semantic_mismatch"
    before.assert_matches(snapshot_whole_tree(target))


@pytest.mark.parametrize(
    ("validation_factory", "expected_semantic_validation"),
    [
        (MissingSemanticValidation, {}),
        (SemanticNoneValidation, {"passed": None, "reason": "semantic_delta_missing"}),
    ],
)
def test_fresh_validation_semantic_evidence_must_be_present_and_true(
    tmp_path: Path,
    validation_factory: type,
    expected_semantic_validation: dict[str, Any],
) -> None:
    target = _target(tmp_path / "fresh-semantic-missing")
    before = snapshot_whole_tree(target)

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=lambda **kwargs: validation_factory(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
    )

    assert result.status == "refused"
    assert result.reason == "fresh_validation_semantic_mismatch"
    assert result.semantic_validation == expected_semantic_validation
    before.assert_matches(snapshot_whole_tree(target))


def test_fresh_validation_path_delta_does_not_default_allow(tmp_path: Path) -> None:
    target = _target(tmp_path / "fresh-path-missing")
    before = snapshot_whole_tree(target)

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=lambda **kwargs: MissingPathPredictionValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
    )

    assert result.status == "refused"
    assert result.reason == "fresh_validation_delta_mismatch"
    before.assert_matches(snapshot_whole_tree(target))


def test_successful_apply_uses_real_taskmaster_cascade_and_audit(tmp_path: Path) -> None:
    _require_taskmaster_cli()
    target = _target(tmp_path / "apply-success", state_json_present=True)
    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        audit_log_path=tmp_path / "audit" / "apply.jsonl",
        enable_write_path=True,
        validation_runner=lambda **kwargs: FakeValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
    )

    assert result.status == "applied"
    assert result.mutated is True
    assert ".taskmaster/state.json" in result.actual_delta_paths
    assert set(result.actual_delta_paths) == set(
        _predicted_paths(FIRST_CANDIDATE, task_id="42", target_root=target)
    )
    audit_lines = (tmp_path / "audit" / "apply.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2
    after_audit = json.loads(audit_lines[-1])
    assert after_audit["outcome"] == "applied"
    assert after_audit["semantic_validation"]["passed"] is True
    assert after_audit["actual_delta_paths"] == list(result.actual_delta_paths)
    assert after_audit["toolchain_evidence"]["task_master"]["version"] == TASKMASTER_PACKAGE_VERSION


def test_idempotency_claim_makes_second_apply_noop(tmp_path: Path) -> None:
    _require_taskmaster_cli()
    target = _target(tmp_path / "idempotency")
    state_root = tmp_path / "state"
    kwargs = {
        "target_root": target,
        "approved_context_proof": APPROVED_CONTEXT,
        "kill_switch_state": ENABLED_KILL_SWITCH,
        "validated_toolchain_evidence": _toolchain(),
        "current_toolchain_evidence": _toolchain(),
        "state_root": state_root,
        "enable_write_path": True,
        "validation_runner": lambda **params: FakeValidation(
            params["predicted_paths"], params["predicted_paths"]
        ),
    }

    first = run_reconcile_apply_write_apparatus(FIRST_CANDIDATE, **kwargs)
    second = run_reconcile_apply_write_apparatus(FIRST_CANDIDATE, **kwargs)

    assert first.status == "applied"
    assert second.status == "noop"
    assert second.reason == "idempotency_already_claimed"
    assert first.idempotency_key == second.idempotency_key


def test_file_idempotency_claim_is_atomic(tmp_path: Path) -> None:
    store = FileIdempotencyStore(tmp_path / "claims")
    results = []

    def claim() -> None:
        results.append(store.claim("same-key").claimed)

    threads = [threading.Thread(target=claim) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results.count(True) == 1
    assert results.count(False) == 11


def test_successful_path_delta_divergence_rolls_back(tmp_path: Path) -> None:
    target = _target(tmp_path / "divergence")
    before = snapshot_whole_tree(target)

    def writer(*, target_root: Path, **_: Any) -> None:
        (target_root / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        audit_log_path=tmp_path / "audit" / "apply.jsonl",
        enable_write_path=True,
        validation_runner=lambda **kwargs: FakeValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
        write_runner=writer,
    )

    assert result.status == "rolled_back"
    assert result.reason == "live_delta_mismatch"
    assert result.rollback_state["rolled_back"] is True
    before.assert_matches(snapshot_whole_tree(target))
    audit_lines = (tmp_path / "audit" / "apply.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(audit_lines[-1])["outcome"] == "live_delta_mismatch"


def test_successful_path_with_semantic_divergence_rolls_back(tmp_path: Path) -> None:
    target = _target(tmp_path / "semantic-divergence")
    tasks_json_path = target / ".taskmaster" / "tasks" / "tasks.json"
    tasks_payload = json.loads(tasks_json_path.read_text(encoding="utf-8"))
    tasks_payload["master"]["tasks"].append(
        {
            "id": 41,
            "title": "Unrelated",
            "status": "pending",
            "dependencies": [],
            "subtasks": [],
        }
    )
    tasks_json_path.write_text(
        json.dumps(tasks_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    before = snapshot_whole_tree(target)

    def writer(*, target_root: Path, **_: Any) -> None:
        payload = json.loads(
            (target_root / ".taskmaster" / "tasks" / "tasks.json").read_text(encoding="utf-8")
        )
        payload["master"]["tasks"][0]["status"] = "done"
        payload["master"]["tasks"][1]["status"] = "done"
        (target_root / ".taskmaster" / "tasks" / "tasks.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (target_root / ".taskmaster" / "tasks" / "task_042.md").write_text(
            "# Task 42: Shadow CI Cascade Validation\n\n- Status: done\n",
            encoding="utf-8",
        )
        (target_root / ".taskmaster" / "state.json").write_text(
            json.dumps({"tag": "master", "currentTask": "42"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        audit_log_path=tmp_path / "audit" / "apply.jsonl",
        enable_write_path=True,
        validation_runner=lambda **kwargs: FakeValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
        write_runner=writer,
    )

    assert result.status == "rolled_back"
    assert result.reason == "live_semantic_delta_mismatch"
    assert result.semantic_validation["reason"] == "tasks_json_semantic_mismatch"
    before.assert_matches(snapshot_whole_tree(target))


def test_partial_apply_failure_rolls_back_snapshot_restore(tmp_path: Path) -> None:
    target = _target(tmp_path / "partial")
    before = snapshot_whole_tree(target)

    def writer(*, target_root: Path, **_: Any) -> None:
        (target_root / ".taskmaster" / "tasks" / "tasks.json").write_text(
            "partial mutation\n", encoding="utf-8"
        )
        (target_root / ".taskmaster" / "state.json").write_text(
            json.dumps({"tag": "master", "partial": True}) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError("injected after set-status")

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        audit_log_path=tmp_path / "audit" / "apply.jsonl",
        enable_write_path=True,
        validation_runner=lambda **kwargs: FakeValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
        write_runner=writer,
    )

    assert result.status == "rolled_back"
    assert result.reason == "write_failed"
    assert result.rollback_state["rolled_back"] is True
    before.assert_matches(snapshot_whole_tree(target))


def test_rollback_failure_is_terminal_and_engages_kill_switch(tmp_path: Path) -> None:
    target = _target(tmp_path / "terminal")
    kill_switch_path = tmp_path / "state" / "kill-switch.json"

    def writer(*, target_root: Path, **_: Any) -> None:
        (target_root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        raise RuntimeError("write failed")

    def broken_restore(_handle: SnapshotRollbackHandle, _root: Path, _paths: Iterable[str]) -> None:
        raise RuntimeError("disk refused rollback")

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        audit_log_path=tmp_path / "audit" / "apply.jsonl",
        kill_switch_path=kill_switch_path,
        enable_write_path=True,
        validation_runner=lambda **kwargs: FakeValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
        write_runner=writer,
        rollback_restore=broken_restore,
    )

    assert result.status == "terminal_rollback_failed"
    assert result.reason == "rollback_failed"
    assert result.mutated is True
    kill_switch = json.loads(kill_switch_path.read_text(encoding="utf-8"))
    assert kill_switch["global"]["disabled"] is True
    assert kill_switch["classes"][FIRST_APPLY_CLASS_KEY]["disabled"] is True
    terminal = json.loads(
        (tmp_path / "audit" / "apply.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    )
    assert terminal["record_type"] == "reconcile_apply_terminal_rollback_failure"
    assert terminal["operator_resolution_required"] is True
    assert terminal["auto_clear_allowed"] is False

    before = snapshot_whole_tree(target)
    terminal_kill_switch = json.loads(kill_switch_path.read_text(encoding="utf-8"))
    result_after_terminal = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=terminal_kill_switch,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state-2",
        enable_write_path=True,
        validation_runner=lambda **_: (_ for _ in ()).throw(
            AssertionError("terminal state must refuse before validation")
        ),
    )

    assert result_after_terminal.status == "refused"
    assert result_after_terminal.reason == "terminal_rollback_failure_present"
    before.assert_matches(snapshot_whole_tree(target))


def test_test_enabled_apply_refuses_governed_repo_target_before_validation(tmp_path: Path) -> None:
    validation_calls = 0

    def validation_runner(**_: Any) -> FakeValidation:
        nonlocal validation_calls
        validation_calls += 1
        raise AssertionError("governed repo target must refuse before validation")

    result = run_reconcile_apply_write_apparatus(
        FIRST_CANDIDATE,
        target_root=REPO_ROOT,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=validation_runner,
    )

    assert result.status == "refused"
    assert result.reason == "target_not_isolated_temp"
    assert validation_calls == 0


def test_enable_path_requires_agent_excluded_switch_state(tmp_path: Path) -> None:
    candidate = FIRST_CANDIDATE
    proof = _proof_artifact(candidate, APPROVED_CONTEXT)
    idempotency_key = idempotency_key_for(
        task_id="42",
        finding_kind="merged_but_not_done",
        proof="git_ancestor",
        proof_artifact=proof,
    )
    claim_path = tmp_path / "state" / "idempotency" / f"{idempotency_key}.json"
    claim_path.parent.mkdir(parents=True)
    claim_path.write_text("{}\n", encoding="utf-8")
    target = _target(tmp_path / "preclaimed")
    before = snapshot_whole_tree(target)

    result = run_reconcile_apply_write_apparatus(
        candidate,
        target_root=target,
        approved_context_proof=APPROVED_CONTEXT,
        kill_switch_state=ENABLED_KILL_SWITCH,
        validated_toolchain_evidence=_toolchain(),
        current_toolchain_evidence=_toolchain(),
        state_root=tmp_path / "state",
        enable_write_path=True,
        validation_runner=lambda **kwargs: FakeValidation(
            kwargs["predicted_paths"], kwargs["predicted_paths"]
        ),
    )

    assert result.status == "noop"
    assert result.reason == "idempotency_already_claimed"
    before.assert_matches(snapshot_whole_tree(target))


def test_live_write_function_has_single_gated_caller() -> None:
    source = (REPO_ROOT / "aegis_foundation" / "reconcile_apply_runtime.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    references = []
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id == "_perform_taskmaster_done_write":
                current: ast.AST | None = node
                while current is not None and not isinstance(current, ast.FunctionDef):
                    current = parents.get(current)
                references.append(current.name if isinstance(current, ast.FunctionDef) else "")
    assert references == ["run_reconcile_apply_write_apparatus"]


def test_apply_write_apparatus_is_not_reachable_from_agent_surfaces() -> None:
    forbidden = ("reconcile_apply_runtime", "run_reconcile_apply_write_apparatus")
    surfaces = (
        REPO_ROOT / "aegis_foundation" / "cli.py",
        REPO_ROOT / "aegis_mcp" / "server.py",
        REPO_ROOT / "scripts" / "codex-task",
        REPO_ROOT / "aegis_foundation" / "assets" / "scripts" / "_aegis_installer.py",
    )
    for surface in surfaces:
        source = surface.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source


def _target(root: Path, *, state_json_present: bool = False) -> Path:
    _write_ci_validation_taskmaster_fixture(
        root,
        task_id="42",
        state_json_present=state_json_present,
    )
    return root


def _toolchain(*, version: str = TASKMASTER_PACKAGE_VERSION) -> dict[str, Any]:
    return build_taskmaster_toolchain_evidence(
        {
            "GITHUB_ACTIONS": "true",
            "RUNNER_OS": "Linux",
            "RUNNER_ARCH": "X64",
            "GITHUB_WORKFLOW": "CI",
            "GITHUB_RUN_ID": "153",
            "GITHUB_RUN_ATTEMPT": "1",
        },
        task_master_version=version,
        node_version="v22.1.0",
        npm_version="10.0.0",
        python_version="3.12.0",
    )


def _require_taskmaster_cli() -> None:
    if shutil.which("task-master") is None:
        pytest.skip("task-master CLI is not available for the write-apparatus test")


def _binding_for(candidate: dict[str, Any]) -> str:
    apply_candidate = {
        "task_id": candidate["task_id"],
        "finding_kind": candidate["finding_kind"],
        "proof": candidate["proof"],
    }
    return authorization_binding_for(
        **apply_candidate,
        proof_artifact=_proof_artifact(candidate, APPROVED_CONTEXT),
    )
