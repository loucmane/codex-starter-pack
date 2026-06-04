"""Shadow-mode reconcile apply artifacts.

This module models the first future apply pipeline without enabling live mutation.
It may validate Taskmaster's done cascade inside a sacrificial copy, but it never
calls Taskmaster, Git, GitHub, closeout, or workflow-state writers against the
governed repository.
"""

from __future__ import annotations

import copy
import fnmatch
import hashlib
import json
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from aegis_foundation.reconcile_apply_scaffold import (
    FIRST_APPLY_CLASS_KEY,
    FIRST_APPLY_PROOF,
    ApplyCandidate,
    authorization_binding_for,
    build_apply_audit_record,
    evaluate_approved_context,
    evaluate_kill_switch,
)
from aegis_foundation.taskmaster_toolchain import (
    compare_taskmaster_toolchain_evidence,
    capture_taskmaster_toolchain_evidence,
)

SHADOW_MODE = "shadow"
SHADOW_REPORT_TYPE = "reconcile_shadow_apply_report"
SHADOW_RECORD_TYPE = "reconcile_shadow_apply"
SHADOW_ACCUMULATION_REPORT_TYPE = "reconcile_shadow_accumulation"
SHADOW_CI_CONTEXT_TYPE = "post_merge_ci"
SHADOW_PR_CI_CONTEXT_TYPE = "pull_request_ci"
SHADOW_OTHER_CI_CONTEXT_TYPE = "non_post_merge_ci"
SHADOW_ARTIFACT_NAME = "reconcile-shadow-apply"
SHADOW_ELIGIBILITY_VERSION = "merged_but_not_done/git_ancestor-v1"
SHADOW_ALLOWED_DECISION_REASON = "enable_gate_unsatisfiable"
SHADOW_CI_VALIDATION_REPORT_TYPE = "reconcile_shadow_ci_cascade_validation"
SHADOW_CI_VALIDATION_TASK_ID = "42"
TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION = "taskmaster-0.43.1-v1"
OPTIONAL_STATE_JSON_DELTA_PATH = ".taskmaster/state.json"
SHADOW_CI_VALIDATION_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True}},
}
SACRIFICIAL_CLONE_IGNORE_PATTERNS = (
    ".git",
    ".git/**",
    ".pytest_cache",
    ".pytest_cache/**",
    ".ruff_cache",
    ".ruff_cache/**",
    ".mypy_cache",
    ".mypy_cache/**",
    "__pycache__",
    "**/__pycache__",
    "**/*.pyc",
)


class ShadowApplyError(ValueError):
    """Raised when shadow-mode inputs or clone validation are invalid."""


@dataclass(frozen=True)
class PathMetadata:
    kind: str
    mode: int | None = None
    digest: str | None = None
    symlink_target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "mode": self.mode,
            "digest": self.digest,
            "symlink_target": self.symlink_target,
        }


@dataclass(frozen=True)
class SacrificialValidation:
    clone_root: Path
    predicted_paths: tuple[str, ...]
    actual_delta_paths: tuple[str, ...]
    baseline_metadata: dict[str, PathMetadata]
    clone_fidelity: dict[str, Any]
    semantic_delta: "TaskmasterSemanticDelta"

    @property
    def path_delta_matches_prediction(self) -> bool:
        return self.actual_delta_paths == self.predicted_paths

    @property
    def semantic_delta_matches_prediction(self) -> bool:
        return self.semantic_delta.passed

    @property
    def matches_prediction(self) -> bool:
        return self.path_delta_matches_prediction and self.semantic_delta_matches_prediction

    @property
    def rollback_baseline_metadata(self) -> dict[str, dict[str, Any]]:
        return {
            path: metadata.to_dict() for path, metadata in sorted(self.baseline_metadata.items())
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_context": "sacrificial_clone",
            "clone_root": self.clone_root.as_posix(),
            "predicted_blast_radius_paths": list(self.predicted_paths),
            "actual_sacrificial_delta_paths": list(self.actual_delta_paths),
            "sacrificial_delta_matches_prediction": self.path_delta_matches_prediction,
            "semantic_delta_matches_prediction": self.semantic_delta_matches_prediction,
            "taskmaster_semantic_delta": self.semantic_delta.to_dict(),
            "rollback_baseline_metadata": self.rollback_baseline_metadata,
            "clone_fidelity": self.clone_fidelity,
        }


@dataclass(frozen=True)
class TaskmasterSemanticDelta:
    target_task_id: str
    expected_status: str
    canonicalization_version: str
    passed: bool
    reason: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_task_id": self.target_task_id,
            "expected_status": self.expected_status,
            "canonicalization_version": self.canonicalization_version,
            "passed": self.passed,
            "reason": self.reason,
            "details": self.details,
        }


def build_ci_shadow_context_proof(
    env: Mapping[str, str],
    *,
    task_id: str,
    proof: str = FIRST_APPLY_PROOF,
) -> dict[str, Any]:
    """Build a Task-150-compatible approved-context proof from GitHub Actions env."""

    run_id = str(env.get("GITHUB_RUN_ID") or "")
    run_attempt = str(env.get("GITHUB_RUN_ATTEMPT") or "1")
    workflow = str(env.get("GITHUB_WORKFLOW") or "")
    repository = str(env.get("GITHUB_REPOSITORY") or "")
    sha = str(env.get("GITHUB_SHA") or "")
    event_name = str(env.get("GITHUB_EVENT_NAME") or "")
    ref = str(env.get("GITHUB_REF") or "")
    ref_name = str(env.get("GITHUB_REF_NAME") or "")
    proof_id = f"github-actions:{run_id}:{run_attempt}" if run_id else ""
    valid_for_shadow = event_name == "push" and ref == "refs/heads/main"
    if valid_for_shadow:
        context_type = SHADOW_CI_CONTEXT_TYPE
        context_reason = "post_merge_push_main"
    elif event_name == "pull_request":
        context_type = SHADOW_PR_CI_CONTEXT_TYPE
        context_reason = "pull_request_not_post_merge"
    else:
        context_type = SHADOW_OTHER_CI_CONTEXT_TYPE
        context_reason = "not_push_main_post_merge"
    return {
        "context_type": context_type,
        "proof_id": proof_id,
        "task_id": str(task_id),
        "proof": str(proof),
        "external_anchor": proof_id,
        "valid_for_shadow": valid_for_shadow,
        "shadow_context_reason": context_reason,
        "ci": {
            "provider": "github_actions",
            "run_id": run_id,
            "run_attempt": run_attempt,
            "workflow": workflow,
            "repository": repository,
            "sha": sha,
            "event_name": event_name,
            "ref": ref,
            "ref_name": ref_name,
        },
    }


def build_ci_shadow_cascade_validation_report(
    env: Mapping[str, str],
    *,
    work_root: Path,
    toolchain_evidence: Mapping[str, Any] | None = None,
    clone_parent: Path | None = None,
) -> dict[str, Any]:
    """Build CI artifact evidence for both Taskmaster cascade state branches."""

    toolchain = dict(toolchain_evidence or capture_taskmaster_toolchain_evidence(env))
    context = build_ci_shadow_context_proof(
        env,
        task_id=SHADOW_CI_VALIDATION_TASK_ID,
        proof=FIRST_APPLY_PROOF,
    )
    cases = []
    for case_name, state_json_payload in (
        ("state_json_absent", None),
        ("state_json_legacy_tag", {"tag": "master"}),
        (
            "state_json_steady_state",
            {
                "currentTag": "master",
                "lastSwitched": "2025-09-22T11:42:16.191Z",
                "branchTagMapping": {},
                "migrationNoticeShown": True,
            },
        ),
    ):
        target_root = work_root / case_name
        _write_ci_validation_taskmaster_fixture(
            target_root,
            task_id=SHADOW_CI_VALIDATION_TASK_ID,
            state_json_payload=state_json_payload,
        )
        candidate = _ci_validation_candidate(task_id=SHADOW_CI_VALIDATION_TASK_ID)
        report = build_shadow_report(
            [candidate],
            target_root=target_root,
            approved_context_proof=context,
            kill_switch_state=SHADOW_CI_VALIDATION_KILL_SWITCH,
            artifact_mode="ci",
            external_anchor=context["external_anchor"],
            clone_parent=(clone_parent / case_name) if clone_parent else None,
        )
        cases.append(
            {
                "case": case_name,
                "state_json_initially_present": state_json_payload is not None,
                "state_json_initial_payload": state_json_payload,
                "shadow_report": report,
            }
        )

    would_apply_records = [
        record for case in cases for record in case["shadow_report"]["would_apply"]
    ]
    return {
        "record_type": SHADOW_CI_VALIDATION_REPORT_TYPE,
        "mode": SHADOW_MODE,
        "executed": False,
        "mutated_live_repo": False,
        "task_master_toolchain": toolchain,
        "toolchain_binding": {
            "comparison": compare_taskmaster_toolchain_evidence(toolchain, toolchain),
            "stale_if_toolchain_mismatch": True,
        },
        "approved_context_proof": context,
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "would_apply_records": len(would_apply_records),
            "all_sacrificial_deltas_match_prediction": len(would_apply_records) == len(cases)
            and all(
                record["sacrificial_delta_matches_prediction"] for record in would_apply_records
            ),
        },
    }


def build_shadow_report(
    candidates: Sequence[Mapping[str, Any]],
    *,
    target_root: Path,
    approved_context_proof: Mapping[str, Any] | None,
    kill_switch_state: Mapping[str, Any] | None,
    artifact_mode: str = "ci",
    external_anchor: str = "",
    clone_parent: Path | None = None,
) -> dict[str, Any]:
    """Build a shadow report for candidate/refusal records."""

    if artifact_mode not in {"ci", "local"}:
        raise ShadowApplyError("artifact_mode must be ci or local")
    records = [
        build_shadow_record(
            candidate_payload,
            target_root=target_root,
            approved_context_proof=approved_context_proof,
            kill_switch_state=kill_switch_state,
            artifact_mode=artifact_mode,
            external_anchor=external_anchor,
            clone_parent=clone_parent,
        )
        for candidate_payload in candidates
    ]
    return {
        "record_type": SHADOW_REPORT_TYPE,
        "mode": SHADOW_MODE,
        "artifact_mode": artifact_mode,
        "artifact_name": SHADOW_ARTIFACT_NAME if artifact_mode == "ci" else "",
        "repo_file_write_policy": (
            "ci writes zero repo files; local mode may write exactly one declared report path"
        ),
        "would_apply": [record for record in records if record["decision"] == "would_apply"],
        "shadow_refused": [record for record in records if record["decision"] == "shadow_refused"],
        "summary": {
            "would_apply": sum(1 for record in records if record["decision"] == "would_apply"),
            "shadow_refused": sum(
                1 for record in records if record["decision"] == "shadow_refused"
            ),
        },
    }


def build_shadow_accumulation_report(
    candidates: Sequence[Mapping[str, Any]],
    *,
    target_root: Path,
    approved_context_proof: Mapping[str, Any] | None,
    kill_switch_state: Mapping[str, Any] | None,
    artifact_mode: str = "ci",
    external_anchor: str = "",
    clone_parent: Path | None = None,
) -> dict[str, Any]:
    """Build post-merge shadow accumulation evidence without writing repo state."""

    shadow_report = build_shadow_report(
        candidates,
        target_root=target_root,
        approved_context_proof=approved_context_proof,
        kill_switch_state=kill_switch_state,
        artifact_mode=artifact_mode,
        external_anchor=external_anchor,
        clone_parent=clone_parent,
    )
    context = approved_context_proof if isinstance(approved_context_proof, Mapping) else {}
    valid_for_shadow = bool(context.get("valid_for_shadow")) and (
        str(context.get("context_type") or "") == SHADOW_CI_CONTEXT_TYPE
    )
    refused_records = list(shadow_report["shadow_refused"])
    semantic_mismatches = [
        record
        for record in refused_records
        if record.get("reason") == "sacrificial_semantic_delta_mismatch"
    ]
    path_mismatches = [
        record for record in refused_records if record.get("reason") == "sacrificial_delta_mismatch"
    ]
    return {
        "record_type": SHADOW_ACCUMULATION_REPORT_TYPE,
        "mode": SHADOW_MODE,
        "artifact_mode": artifact_mode,
        "artifact_name": SHADOW_ARTIFACT_NAME if artifact_mode == "ci" else "",
        "valid_for_shadow": valid_for_shadow,
        "accepted_context_type": SHADOW_CI_CONTEXT_TYPE,
        "approved_context_proof": dict(context),
        "repo_file_write_policy": (
            "CI may write declared upload artifacts only; no in-repo ledger or workflow state"
        ),
        "shadow_report": shadow_report,
        "triage": {
            "reporting_only": True,
            "auto_extend_canonicalization": False,
            "auto_write_exemptions": False,
            "unexplained_divergence_count": len(path_mismatches),
            "canonicalization_completeness_count": len(semantic_mismatches),
            "benign_normalizations_accepted": 0,
            "path_delta_mismatches": path_mismatches,
            "semantic_delta_mismatches": semantic_mismatches,
        },
        "summary": {
            "candidate_count": len(candidates),
            "would_apply": shadow_report["summary"]["would_apply"],
            "shadow_refused": shadow_report["summary"]["shadow_refused"],
            "valid_for_shadow": valid_for_shadow,
            "zero_unexplained_divergences": len(path_mismatches) == 0,
            "triage_required": bool(path_mismatches or semantic_mismatches),
        },
    }


def write_local_shadow_report(report: Mapping[str, Any], report_path: Path) -> Path:
    """Write the caller-declared local report artifact."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def build_shadow_record(
    candidate_payload: Mapping[str, Any],
    *,
    target_root: Path,
    approved_context_proof: Mapping[str, Any] | None,
    kill_switch_state: Mapping[str, Any] | None,
    artifact_mode: str = "ci",
    external_anchor: str = "",
    clone_parent: Path | None = None,
) -> dict[str, Any]:
    """Build one would-apply or shadow-refused record for a candidate payload."""

    candidate = ApplyCandidate.from_mapping(candidate_payload)
    authority_refusal = _taskmaster_authority_refusal_reason(target_root)
    predicted_paths = _predicted_paths(
        candidate_payload,
        task_id=candidate.task_id,
        target_root=target_root,
        include_optional_state_json=False,
    )
    base = _base_record(candidate, artifact_mode=artifact_mode)
    context = evaluate_approved_context(approved_context_proof, candidate=candidate)
    base["approved_context"] = {
        **context.to_dict(),
        "valid_for_shadow": _decision_is_valid_for_shadow(context.reason),
    }
    kill_switch = evaluate_kill_switch(kill_switch_state, class_key=candidate.class_key)
    base["kill_switch"] = {
        **kill_switch.to_dict(),
        "valid_for_shadow": _decision_is_valid_for_shadow(kill_switch.reason),
    }

    refusal = _shadow_refusal_reason(
        candidate, context_reason=context.reason, kill_reason=kill_switch.reason
    )
    if authority_refusal:
        refusal = authority_refusal
    if refusal:
        base["decision"] = "shadow_refused"
        base["reason"] = refusal
        return base

    validation = validate_sacrificial_taskmaster_done_cascade(
        target_root=target_root,
        task_id=candidate.task_id,
        predicted_paths=predicted_paths,
        clone_parent=clone_parent,
    )
    base.update(validation.to_dict())
    if not validation.path_delta_matches_prediction:
        base["decision"] = "shadow_refused"
        base["reason"] = "sacrificial_delta_mismatch"
        return base
    if not validation.semantic_delta_matches_prediction:
        base["decision"] = "shadow_refused"
        base["reason"] = "sacrificial_semantic_delta_mismatch"
        return base

    proof_artifact = _proof_artifact(candidate_payload, approved_context_proof)
    authorization_binding = authorization_binding_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=proof_artifact,
    )
    audit = build_apply_audit_record(
        phase="before",
        candidate=candidate,
        proof_artifact=proof_artifact,
        allowed_delta_hashes={
            path: json.dumps(metadata.to_dict(), sort_keys=True)
            for path, metadata in validation.baseline_metadata.items()
        },
        approved_context_proof_id=str(
            (approved_context_proof or {}).get("proof_id") or "shadow-context"
        ),
        authorization_binding=authorization_binding,
        rollback_handle_ref=f"shadow://task/{candidate.task_id}/sacrificial-baseline",
        rolled_back=False,
        eligibility_corpus_version=SHADOW_ELIGIBILITY_VERSION,
        external_anchor=external_anchor
        or str((approved_context_proof or {}).get("external_anchor") or ""),
    )
    base.update(
        {
            "decision": "would_apply",
            "target_status": candidate.proposed_status,
            "proof_artifact": proof_artifact,
            "authorization_binding": authorization_binding,
            "idempotency_key": audit["idempotency_key"],
            "chain_hash": audit["chain_hash"],
            "apply_audit": audit,
        }
    )
    return base


def validate_sacrificial_taskmaster_done_cascade(
    *,
    target_root: Path,
    task_id: str,
    predicted_paths: Iterable[str],
    clone_parent: Path | None = None,
) -> SacrificialValidation:
    """Validate Taskmaster's real done cascade inside a detached temp copy."""

    target_root = target_root.resolve()
    required_predicted = tuple(sorted({_normalize_rel_path(path) for path in predicted_paths}))
    if not required_predicted:
        raise ShadowApplyError("predicted blast-radius paths are required")
    if not (target_root / ".taskmaster" / "tasks" / "tasks.json").exists():
        raise ShadowApplyError("target root does not contain Taskmaster tasks.json")
    metadata_paths = tuple(sorted(set(required_predicted) | {OPTIONAL_STATE_JSON_DELTA_PATH}))

    if clone_parent is None:
        clone_context = tempfile.TemporaryDirectory(prefix="aegis-shadow-apply-")
        clone_base = Path(clone_context.name)
    else:
        clone_context = None
        clone_base = clone_parent
        clone_base.mkdir(parents=True, exist_ok=True)
    try:
        clone_root = clone_base / "sacrificial-clone"
        if clone_root.exists():
            shutil.rmtree(clone_root)
        _copy_detached_working_tree(target_root, clone_root)
        if clone_root.resolve() == target_root:
            raise ShadowApplyError("sacrificial clone resolved to the governed target root")

        target_baseline = _metadata_for_paths(target_root, metadata_paths)
        clone_baseline = _metadata_for_paths(clone_root, metadata_paths)
        clone_fidelity = {
            "detached": clone_root.resolve() != target_root,
            "relevant_paths_match": {
                path: target_baseline[path].to_dict() == clone_baseline[path].to_dict()
                for path in metadata_paths
            },
        }
        if not all(clone_fidelity["relevant_paths_match"].values()):
            raise ShadowApplyError("sacrificial clone does not match target baseline paths")

        before = _snapshot_tree(clone_root)
        semantic_before = _read_taskmaster_semantic_inputs(
            clone_root, task_id=task_id, predicted_paths=required_predicted
        )
        _run_clone_command(
            clone_root, "task-master", "set-status", f"--id={task_id}", "--status=done"
        )
        if (clone_root / "scripts" / "codex-task").exists():
            _run_clone_command(
                clone_root,
                "python3",
                "scripts/codex-task",
                "taskmaster",
                "generate-one",
                "--id",
                str(task_id),
            )
        else:
            _run_clone_command(clone_root, "task-master", "generate")
        after = _snapshot_tree(clone_root)
        semantic_after = _read_taskmaster_semantic_inputs(
            clone_root, task_id=task_id, predicted_paths=required_predicted
        )
        actual = tuple(sorted(_tree_delta_paths(before, after)))
        effective_predicted = tuple(
            sorted(
                set(required_predicted)
                | ({OPTIONAL_STATE_JSON_DELTA_PATH} if OPTIONAL_STATE_JSON_DELTA_PATH in actual else set())
            )
        )
        effective_baseline = {
            path: target_baseline[path]
            for path in effective_predicted
        }
        return SacrificialValidation(
            clone_root=clone_root,
            predicted_paths=effective_predicted,
            actual_delta_paths=actual,
            baseline_metadata=effective_baseline,
            clone_fidelity=clone_fidelity,
            semantic_delta=validate_taskmaster_apply_semantic_delta(
                before=semantic_before,
                after=semantic_after,
                task_id=task_id,
                expected_status="done",
            ),
        )
    finally:
        if clone_context is not None:
            clone_context.cleanup()


def validate_taskmaster_apply_semantic_delta(
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    task_id: str,
    expected_status: str = "done",
) -> TaskmasterSemanticDelta:
    """Validate expected Taskmaster apply content changes inside allowed paths."""

    task_id = str(task_id)
    expected_status = str(expected_status)
    try:
        before_tasks = _canonicalize_taskmaster_document(before["tasks_json"])
        after_tasks = _canonicalize_taskmaster_document(after["tasks_json"])
    except KeyError as exc:
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason="tasks_json_missing",
            details={"missing": str(exc)},
        )

    before_match = _find_task_record(before_tasks, task_id)
    after_match = _find_task_record(after_tasks, task_id)
    if before_match is None:
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason="target_task_missing_before",
            details={},
        )
    if after_match is None:
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason="target_task_missing_after",
            details={},
        )

    before_status = str(before_match["record"].get("status") or "")
    after_status = str(after_match["record"].get("status") or "")
    if after_status != expected_status:
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason="target_status_not_done",
            details={"before_status": before_status, "after_status": after_status},
        )

    expected_after = copy.deepcopy(before_tasks)
    expected_match = _find_task_record(expected_after, task_id)
    if expected_match is None:  # pragma: no cover - guarded by before_match.
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason="target_task_missing_expected",
            details={},
        )
    expected_match["record"]["status"] = expected_status
    if expected_after != after_tasks:
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason="tasks_json_semantic_mismatch",
            details={
                "before_status": before_status,
                "after_status": after_status,
                "diff_summary": _semantic_diff_summary(expected_after, after_tasks),
            },
        )

    markdown = _validate_generated_task_markdown(
        before_text=before.get("generated_task_markdown"),
        after_text=after.get("generated_task_markdown"),
        task_id=task_id,
        expected_status=expected_status,
    )
    if not markdown["passed"]:
        return _semantic_failure(
            task_id=task_id,
            expected_status=expected_status,
            reason=str(markdown["reason"]),
            details={"markdown": markdown},
        )

    return TaskmasterSemanticDelta(
        target_task_id=task_id,
        expected_status=expected_status,
        canonicalization_version=TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION,
        passed=True,
        reason="semantic_delta_matches_prediction",
        details={
            "tasks_json": {
                "before_status": before_status,
                "after_status": after_status,
                "target_path": before_match["path"],
            },
            "markdown": markdown,
        },
    )


def _semantic_failure(
    *,
    task_id: str,
    expected_status: str,
    reason: str,
    details: Mapping[str, Any],
) -> TaskmasterSemanticDelta:
    return TaskmasterSemanticDelta(
        target_task_id=task_id,
        expected_status=expected_status,
        canonicalization_version=TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION,
        passed=False,
        reason=reason,
        details=dict(details),
    )


def _read_taskmaster_semantic_inputs(
    root: Path,
    *,
    task_id: str,
    predicted_paths: Iterable[str],
) -> dict[str, Any]:
    predicted = {_normalize_rel_path(path) for path in predicted_paths}
    tasks_json_path = root / ".taskmaster" / "tasks" / "tasks.json"
    generated_rel = _taskmaster_generated_task_markdown_rel(task_id)
    payload: dict[str, Any] = {
        "tasks_json": json.loads(tasks_json_path.read_text(encoding="utf-8")),
    }
    if generated_rel in predicted:
        generated_path = root / generated_rel
        payload["generated_task_markdown"] = (
            generated_path.read_text(encoding="utf-8")
            if generated_path.exists()
            else None
        )
    return payload


def _canonicalize_taskmaster_document(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized = dict(value)
        if "id" in normalized and "status" in normalized and "subtasks" not in normalized:
            normalized["subtasks"] = []
        return {
            str(key): _canonicalize_taskmaster_value(str(key), child)
            for key, child in sorted(normalized.items(), key=lambda item: str(item[0]))
            if _taskmaster_key_is_semantic(str(key), parent=normalized)
        }
    if isinstance(value, list):
        return [_canonicalize_taskmaster_document(item) for item in value]
    return value


def _canonicalize_taskmaster_value(key: str, value: Any) -> Any:
    if key == "id":
        return _canonical_task_id(value)
    if key == "dependencies" and isinstance(value, list):
        return [_canonical_task_id(item) for item in value]
    return _canonicalize_taskmaster_document(value)


def _taskmaster_key_is_semantic(key: str, *, parent: Mapping[str, Any]) -> bool:
    if key == "updatedAt":
        return False
    if key == "metadata" and "tasks" in parent:
        return False
    return True


def _canonical_task_id(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def _find_task_record(document: Any, task_id: str) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            if str(value.get("id") or "") == task_id:
                matches.append({"path": path, "record": value})
            for key, child in value.items():
                visit(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(document, "")
    return matches[0] if len(matches) == 1 else None


def _semantic_diff_summary(expected: Any, actual: Any, *, limit: int = 20) -> list[str]:
    diffs: list[str] = []

    def visit(left: Any, right: Any, path: str) -> None:
        if len(diffs) >= limit:
            return
        if type(left) is not type(right):
            diffs.append(f"{path or '<root>'}: type {type(left).__name__} -> {type(right).__name__}")
            return
        if isinstance(left, Mapping):
            keys = sorted(set(left) | set(right), key=str)
            for key in keys:
                if key not in left:
                    diffs.append(f"{path}.{key}: added")
                elif key not in right:
                    diffs.append(f"{path}.{key}: removed")
                else:
                    visit(left[key], right[key], f"{path}.{key}" if path else str(key))
                if len(diffs) >= limit:
                    return
        elif isinstance(left, list):
            if len(left) != len(right):
                diffs.append(f"{path or '<root>'}: length {len(left)} -> {len(right)}")
                return
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                visit(left_item, right_item, f"{path}[{index}]")
                if len(diffs) >= limit:
                    return
        elif left != right:
            diffs.append(f"{path or '<root>'}: {left!r} -> {right!r}")

    visit(expected, actual, "")
    return diffs


def _validate_generated_task_markdown(
    *,
    before_text: Any,
    after_text: Any,
    task_id: str,
    expected_status: str,
) -> dict[str, Any]:
    if after_text is None:
        return {"passed": False, "reason": "generated_markdown_missing_after"}
    if not isinstance(after_text, str) or not after_text.strip():
        return {"passed": False, "reason": "generated_markdown_empty_after"}
    status_match = re.search(
        r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?status\s*:\s*(?:\*\*)?\s*`?([A-Za-z0-9_-]+)`?\s*$",
        after_text,
    )
    if status_match is None:
        return {"passed": False, "reason": "generated_markdown_status_missing"}
    if status_match.group(1) != expected_status:
        return {
            "passed": False,
            "reason": "generated_markdown_status_mismatch",
            "after_status": status_match.group(1),
        }
    task_id_pattern = re.compile(
        rf"(?im)^\s*#?\s*Task(?:\s+ID)?(?:\s*:\s*|\s+){re.escape(task_id)}\b"
    )
    if task_id_pattern.search(after_text) is None:
        return {"passed": False, "reason": "generated_markdown_task_id_missing"}
    before_status = ""
    if isinstance(before_text, str):
        before_match = re.search(
            r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?status\s*:\s*(?:\*\*)?\s*`?([A-Za-z0-9_-]+)`?\s*$",
            before_text,
        )
        before_status = before_match.group(1) if before_match else ""
    return {
        "passed": True,
        "reason": "generated_markdown_matches_prediction",
        "before_status": before_status,
        "after_status": status_match.group(1),
    }


def _base_record(candidate: ApplyCandidate, *, artifact_mode: str) -> dict[str, Any]:
    return {
        "record_type": SHADOW_RECORD_TYPE,
        "mode": SHADOW_MODE,
        "artifact_mode": artifact_mode,
        "executed": False,
        "mutated_live_repo": False,
        "task_id": candidate.task_id,
        "finding_kind": candidate.finding_kind,
        "proof": candidate.proof,
        "candidate_boundary": "only merged_but_not_done with git_ancestor proof",
        "eligibility_version": SHADOW_ELIGIBILITY_VERSION,
        "eligibility": {
            "finding_kind": candidate.finding_kind,
            "proof_source": candidate.proof,
            "class_key": candidate.class_key,
            "version": SHADOW_ELIGIBILITY_VERSION,
        },
    }


def _shadow_refusal_reason(
    candidate: ApplyCandidate, *, context_reason: str, kill_reason: str
) -> str:
    if not candidate.is_first_apply_class:
        return "candidate_outside_first_apply_class"
    if not _decision_is_valid_for_shadow(context_reason):
        return context_reason
    if not _decision_is_valid_for_shadow(kill_reason):
        return kill_reason
    return ""


def _decision_is_valid_for_shadow(reason: str) -> bool:
    return reason == SHADOW_ALLOWED_DECISION_REASON


def _predicted_paths(
    candidate_payload: Mapping[str, Any],
    *,
    task_id: str,
    target_root: Path,
    include_optional_state_json: bool = True,
) -> tuple[str, ...]:
    raw_paths = candidate_payload.get("predicted_blast_radius_paths")
    paths = raw_paths if isinstance(raw_paths, Sequence) and not isinstance(raw_paths, str) else ()
    if not paths:
        paths = (
            ".taskmaster/tasks/tasks.json",
            _taskmaster_generated_task_markdown_rel(task_id),
        )
    normalized = {_normalize_rel_path(str(path)) for path in paths if str(path)}
    if include_optional_state_json:
        normalized.add(OPTIONAL_STATE_JSON_DELTA_PATH)
    return tuple(sorted(normalized))


def _taskmaster_authority_refusal_reason(target_root: Path) -> str | None:
    tasks_path = target_root / ".taskmaster" / "tasks" / "tasks.json"
    try:
        payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "taskmaster_authority_missing"
    except json.JSONDecodeError:
        return "taskmaster_authority_invalid"
    if not isinstance(payload, Mapping):
        return "taskmaster_authority_invalid"
    task_lists = []
    for tag_payload in payload.values():
        if not isinstance(tag_payload, Mapping):
            return "taskmaster_authority_invalid"
        tasks = tag_payload.get("tasks")
        if not isinstance(tasks, list):
            return "taskmaster_authority_invalid"
        task_lists.append(tasks)
    if not task_lists:
        return "taskmaster_authority_invalid"
    for task_list in task_lists:
        for task in task_list:
            if not isinstance(task, Mapping):
                return "taskmaster_authority_invalid"
    return None


def _proof_artifact(
    candidate_payload: Mapping[str, Any],
    approved_context_proof: Mapping[str, Any] | None,
) -> dict[str, Any]:
    proof_artifact = candidate_payload.get("proof_artifact")
    if not isinstance(proof_artifact, Mapping) or not proof_artifact:
        proof_artifact = {
            "task_id": str(candidate_payload.get("task_id") or ""),
            "finding_kind": str(
                candidate_payload.get("finding_kind") or candidate_payload.get("kind") or ""
            ),
            "proof": str(candidate_payload.get("proof") or ""),
            "context_proof_id": str((approved_context_proof or {}).get("proof_id") or ""),
        }
    return dict(proof_artifact)


def _taskmaster_generated_task_markdown_rel(task_id: str) -> str:
    try:
        suffix = f"{int(task_id):03d}"
    except ValueError:
        suffix = task_id
    return f".taskmaster/tasks/task_{suffix}.md"


def _metadata_for_paths(root: Path, paths: Iterable[str]) -> dict[str, PathMetadata]:
    return {
        _normalize_rel_path(path): _metadata_for_path(root / _normalize_rel_path(path))
        for path in paths
    }


def _metadata_for_path(path: Path) -> PathMetadata:
    if not path.exists() and not path.is_symlink():
        return PathMetadata(kind="missing")
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if path.is_symlink():
        return PathMetadata(kind="symlink", mode=mode, symlink_target=path.readlink().as_posix())
    if path.is_dir():
        return PathMetadata(kind="directory", mode=mode)
    if path.is_file():
        return PathMetadata(
            kind="file",
            mode=mode,
            digest=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return PathMetadata(kind="other", mode=mode)


def _copy_detached_working_tree(source_root: Path, clone_root: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        rel_dir = _normalize_rel_path(Path(directory).relative_to(source_root).as_posix())
        ignored: set[str] = set()
        for name in names:
            rel_path = _normalize_rel_path(f"{rel_dir}/{name}" if rel_dir else name)
            if _matches_any(rel_path, SACRIFICIAL_CLONE_IGNORE_PATTERNS):
                ignored.add(name)
        return ignored

    shutil.copytree(source_root, clone_root, symlinks=True, ignore=ignore)


def _snapshot_tree(root: Path) -> dict[str, PathMetadata]:
    return {
        rel_path: _metadata_for_path(path)
        for rel_path, path in _iter_paths(root)
        if not _matches_any(rel_path, SACRIFICIAL_CLONE_IGNORE_PATTERNS)
    }


def _tree_delta_paths(
    before: Mapping[str, PathMetadata],
    after: Mapping[str, PathMetadata],
) -> list[str]:
    return [
        path for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)
    ]


def _iter_paths(root: Path) -> list[tuple[str, Path]]:
    paths = [root] + sorted(root.rglob("*"), key=lambda path: path.as_posix())
    result: list[tuple[str, Path]] = []
    for path in paths:
        if path == root:
            continue
        rel_path = _normalize_rel_path(path.relative_to(root).as_posix())
        result.append((rel_path, path))
    return result


def _run_clone_command(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    if not cwd.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise ShadowApplyError(f"sacrificial mutation must run under temp dir: {cwd}")
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ShadowApplyError(result.stderr or result.stdout)
    return result


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    path = _normalize_rel_path(path)
    return any(path == pattern or fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _normalize_rel_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _ci_validation_candidate(*, task_id: str) -> dict[str, Any]:
    return {
        "task_id": str(task_id),
        "finding_kind": "merged_but_not_done",
        "proof": FIRST_APPLY_PROOF,
        "proposed_status": "done",
        "class_key": "merged_but_not_done:git_ancestor",
        "predicted_blast_radius_paths": [
            ".taskmaster/tasks/tasks.json",
            _taskmaster_generated_task_markdown_rel(task_id),
        ],
    }


def _write_ci_validation_taskmaster_fixture(
    root: Path,
    *,
    task_id: str,
    state_json_payload: Mapping[str, Any] | None = None,
    state_json_present: bool | None = None,
) -> None:
    if state_json_present is not None and state_json_payload is None:
        state_json_payload = {"tag": "master"} if state_json_present else None
    tasks_dir = root / ".taskmaster" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    task_number = int(task_id)
    tasks_payload = {
        "master": {
            "tasks": [
                {
                    "id": task_number,
                    "title": "Shadow CI Cascade Validation",
                    "description": "Fixture task for validating Taskmaster done cascade.",
                    "details": "Used only inside a detached sacrificial clone.",
                    "testStrategy": "No live repository mutation.",
                    "status": "pending",
                    "dependencies": [],
                    "priority": "medium",
                    "subtasks": [],
                }
            ],
            "metadata": {
                "created": "2026-06-03T00:00:00.000Z",
                "updated": "2026-06-03T00:00:00.000Z",
                "description": "Shadow CI cascade validation fixture",
            },
        }
    }
    (tasks_dir / "tasks.json").write_text(
        json.dumps(tasks_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (tasks_dir / _taskmaster_generated_task_markdown_rel(task_id).rsplit("/", 1)[-1]).write_text(
        "# Task 42: Shadow CI Cascade Validation\n\n"
        "- Status: pending\n"
        "- Scope: fixture task for sacrificial cascade validation.\n",
        encoding="utf-8",
    )
    if state_json_payload is not None:
        (root / ".taskmaster" / "state.json").write_text(
            json.dumps(dict(state_json_payload), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
