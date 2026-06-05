"""Default-off reconcile apply write apparatus.

This module intentionally exposes no CLI or MCP entrypoint. The only write path is
``run_reconcile_apply_write_apparatus`` and it refuses by default. Tests may open
the gate inside temporary fixtures to prove the write, rollback, audit, and
idempotency machinery before any production enablement exists.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from aegis_foundation.reconcile_apply_scaffold import (
    FIRST_APPLY_CLASS_KEY,
    ApplyCandidate,
    ApprovedContextDecision,
    KillSwitchDecision,
    SelectedChannelConfirmationDecision,
    authorization_binding_for,
    build_apply_audit_record,
    evaluate_approved_context,
    evaluate_selected_apply_channel_confirmation,
    evaluate_kill_switch,
    idempotency_key_for,
)
from aegis_foundation.reconcile_shadow_apply import (
    SACRIFICIAL_CLONE_IGNORE_PATTERNS,
    _matches_any,
    _normalize_rel_path,
    _predicted_paths,
    _proof_artifact,
    _taskmaster_generated_task_markdown_rel,
    validate_sacrificial_taskmaster_done_cascade,
    validate_taskmaster_apply_semantic_delta,
)
from aegis_foundation.taskmaster_toolchain import (
    TASKMASTER_NODE_VERSION,
    TASKMASTER_PACKAGE_VERSION,
    TASKMASTER_PROVISIONING_LOCK_ID,
    TASKMASTER_TOOLCHAIN_LOCK_VERSION,
    capture_taskmaster_toolchain_evidence,
    compare_taskmaster_toolchain_evidence,
    taskmaster_install_spec,
)
from scripts._aegis_installer import (
    AegisError,
    _taskmaster_state,
    _taskmaster_tasks_by_id_from_state,
    reconcile,
)

APPLY_ELIGIBILITY_VERSION = "task146-v1"
APPLY_AUDIT_RECORD_TYPE = "reconcile_apply_audit"
TERMINAL_ROLLBACK_RECORD_TYPE = "reconcile_apply_terminal_rollback_failure"
PROCESS_ORACLE_RECORD_TYPE = "reconcile_apply_process_oracle"
CHANNEL_CONFIRMATION_FILENAME = "channel-confirmation.json"
PROCESS_ORACLE_FILENAME = "process-oracle.json"
_MISSING = object()
_DONE_TASKMASTER_STATUSES = {"done", "completed"}


class ReconcileApplyRuntimeError(RuntimeError):
    """Raised for internal apply runtime failures."""


@dataclass(frozen=True)
class SnapshotEntry:
    kind: str
    mode: int | None = None
    digest: str | None = None
    symlink_target: str | None = None
    content: bytes | None = None

    def fingerprint(self) -> str:
        return _digest(
            {
                "kind": self.kind,
                "mode": self.mode,
                "digest": self.digest,
                "symlink_target": self.symlink_target,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "mode": self.mode,
            "digest": self.digest,
            "symlink_target": self.symlink_target,
        }


@dataclass(frozen=True)
class SnapshotRollbackHandle:
    entries: Mapping[str, SnapshotEntry]

    @property
    def ref(self) -> str:
        return (
            f"snapshot://{_digest({path: entry.to_dict() for path, entry in self.entries.items()})}"
        )

    def hashes_for(self, paths: Iterable[str]) -> dict[str, str]:
        return {
            path: self.entries.get(path, SnapshotEntry(kind="missing")).fingerprint()
            for path in sorted({_normalize_rel_path(path) for path in paths})
        }

    def restore(self, root: Path, paths: Iterable[str]) -> None:
        normalized = sorted({_normalize_rel_path(path) for path in paths})
        for rel_path in sorted(normalized, key=lambda item: item.count("/"), reverse=True):
            _remove_existing(root / rel_path)
        for rel_path in sorted(normalized, key=lambda item: item.count("/")):
            entry = self.entries.get(rel_path, SnapshotEntry(kind="missing"))
            _restore_entry(root / rel_path, entry)


@dataclass(frozen=True)
class IdempotencyClaim:
    claimed: bool
    path: str


@dataclass(frozen=True)
class FileIdempotencyStore:
    root: Path

    def claim_path(self, key: str) -> Path:
        safe_key = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in key)
        return self.root / "idempotency" / f"{safe_key}.json"

    def exists(self, key: str) -> bool:
        return self.claim_path(key).exists()

    def claim(self, key: str) -> IdempotencyClaim:
        claims_dir = self.root / "idempotency"
        claims_dir.mkdir(parents=True, exist_ok=True)
        claim_path = self.claim_path(key)
        try:
            with claim_path.open("x", encoding="utf-8") as handle:
                json.dump({"idempotency_key": key, "status": "claimed"}, handle, sort_keys=True)
                handle.write("\n")
        except FileExistsError:
            return IdempotencyClaim(False, claim_path.as_posix())
        return IdempotencyClaim(True, claim_path.as_posix())


@dataclass(frozen=True)
class ReconcileApplyResult:
    status: str
    enabled: bool
    mutated: bool
    reason: str
    candidate: ApplyCandidate
    approved_context: ApprovedContextDecision
    kill_switch: KillSwitchDecision
    predicted_delta_paths: tuple[str, ...] = ()
    actual_delta_paths: tuple[str, ...] = ()
    idempotency_key: str = ""
    audit_records: tuple[dict[str, Any], ...] = ()
    rollback_state: Mapping[str, Any] | None = None
    toolchain_comparison: Mapping[str, Any] | None = None
    semantic_validation: Mapping[str, Any] | None = None
    taskmaster_authority: Mapping[str, Any] | None = None
    freshness_validation: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "enabled": self.enabled,
            "mutated": self.mutated,
            "reason": self.reason,
            "candidate": {
                "task_id": self.candidate.task_id,
                "finding_kind": self.candidate.finding_kind,
                "proof": self.candidate.proof,
                "current_status": self.candidate.current_status,
                "proposed_status": self.candidate.proposed_status,
            },
            "approved_context": self.approved_context.to_dict(),
            "kill_switch": self.kill_switch.to_dict(),
            "predicted_delta_paths": list(self.predicted_delta_paths),
            "actual_delta_paths": list(self.actual_delta_paths),
            "idempotency_key": self.idempotency_key,
            "audit_records": list(self.audit_records),
            "rollback_state": dict(self.rollback_state or {}),
            "toolchain_comparison": dict(self.toolchain_comparison or {}),
            "semantic_validation": dict(self.semantic_validation or {}),
            "taskmaster_authority": dict(self.taskmaster_authority or {}),
            "freshness_validation": dict(self.freshness_validation or {}),
        }


@dataclass(frozen=True)
class SelectedChannelApplyOracleResult:
    status: str
    reason: str
    confirmation: SelectedChannelConfirmationDecision
    process_oracle: Mapping[str, Any]
    apply_result: ReconcileApplyResult | None = None
    audit_destination: str = ""
    external_artifacts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "confirmation": self.confirmation.to_dict(),
            "process_oracle": dict(self.process_oracle),
            "apply_result": self.apply_result.to_dict() if self.apply_result else {},
            "audit_destination": self.audit_destination,
            "external_artifacts": list(self.external_artifacts),
        }


def run_reconcile_apply_write_apparatus(
    candidate_payload: Mapping[str, Any],
    *,
    target_root: Path,
    approved_context_proof: Mapping[str, Any] | None = None,
    kill_switch_state: Mapping[str, Any] | None = None,
    validated_toolchain_evidence: Mapping[str, Any] | None = None,
    current_toolchain_evidence: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
    audit_log_path: Path | None = None,
    kill_switch_path: Path | None = None,
    enable_write_path: bool = False,
    validation_runner: Callable[..., Any] | None = None,
    write_runner: Callable[..., None] | None = None,
    rollback_restore: Callable[[SnapshotRollbackHandle, Path, Iterable[str]], None] | None = None,
    inject_failure_after: str = "",
) -> ReconcileApplyResult:
    """Run the default-off apply apparatus.

    ``enable_write_path`` exists only for isolated tests. With the default value,
    the function refuses before validation, idempotency, audit, or Taskmaster writes.
    """

    target_root = target_root.resolve()
    candidate = ApplyCandidate.from_mapping(candidate_payload)
    context = evaluate_approved_context(
        approved_context_proof,
        candidate=candidate,
        enable_gate_open=enable_write_path,
    )
    kill_switch = evaluate_kill_switch(
        kill_switch_state,
        class_key=candidate.class_key,
        enable_gate_open=enable_write_path,
    )
    base_kwargs: dict[str, Any] = {
        "candidate": candidate,
        "approved_context": context,
        "kill_switch": kill_switch,
    }
    if not candidate.is_first_apply_class:
        return ReconcileApplyResult(
            status="refused",
            enabled=False,
            mutated=False,
            reason="candidate_outside_first_apply_class",
            **base_kwargs,
        )
    if not context.approved:
        return ReconcileApplyResult(
            status="refused",
            enabled=False,
            mutated=False,
            reason=context.reason,
            **base_kwargs,
        )
    if _terminal_rollback_failure_present(kill_switch_state):
        return ReconcileApplyResult(
            status="refused",
            enabled=False,
            mutated=False,
            reason="terminal_rollback_failure_present",
            **base_kwargs,
        )
    if not kill_switch.enabled:
        return ReconcileApplyResult(
            status="refused",
            enabled=False,
            mutated=False,
            reason=kill_switch.reason,
            **base_kwargs,
        )
    if not _is_under_temp(target_root):
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="target_not_isolated_temp",
            **base_kwargs,
        )
    if state_root is None or not _is_under_temp(state_root.resolve()):
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="state_root_not_isolated_temp",
            **base_kwargs,
        )
    authority, taskmaster_state = _taskmaster_authority_decision(target_root)
    if not authority["passed"]:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason=str(authority["reason"]),
            taskmaster_authority=authority,
            **base_kwargs,
        )
    if validated_toolchain_evidence is None:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="validated_toolchain_evidence_missing",
            **base_kwargs,
        )
    baseline_reason = _validated_toolchain_baseline_refusal_reason(validated_toolchain_evidence)
    if baseline_reason:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason=baseline_reason,
            **base_kwargs,
        )

    current_toolchain_evidence = (
        current_toolchain_evidence or capture_taskmaster_toolchain_evidence()
    )
    toolchain_comparison = compare_taskmaster_toolchain_evidence(
        validated_toolchain_evidence, current_toolchain_evidence
    )
    if not toolchain_comparison.get("matches"):
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="toolchain_evidence_stale",
            toolchain_comparison=toolchain_comparison,
            **base_kwargs,
        )

    predicted_paths = tuple(
        _predicted_paths(candidate_payload, task_id=candidate.task_id, target_root=target_root)
    )
    proof_artifact = _proof_artifact(candidate_payload, approved_context_proof)
    idempotency_key = idempotency_key_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=proof_artifact,
    )
    idempotency_store = FileIdempotencyStore(state_root)
    if idempotency_store.exists(idempotency_key):
        return ReconcileApplyResult(
            status="noop",
            enabled=True,
            mutated=False,
            reason="idempotency_already_claimed",
            predicted_delta_paths=predicted_paths,
            idempotency_key=idempotency_key,
            toolchain_comparison=toolchain_comparison,
            taskmaster_authority=authority,
            **base_kwargs,
        )

    freshness = _candidate_freshness_decision(
        candidate,
        target_root=target_root,
        taskmaster_state=taskmaster_state,
    )
    if not freshness["passed"]:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason=str(freshness["reason"]),
            taskmaster_authority=authority,
            freshness_validation=freshness,
            toolchain_comparison=toolchain_comparison,
            **base_kwargs,
        )

    validation_call = validation_runner or validate_sacrificial_taskmaster_done_cascade
    validation = validation_call(
        target_root=target_root,
        task_id=candidate.task_id,
        predicted_paths=predicted_paths,
    )
    if validation is None:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="fresh_validation_not_run",
            predicted_delta_paths=predicted_paths,
            toolchain_comparison=toolchain_comparison,
            taskmaster_authority=authority,
            freshness_validation=freshness,
            **base_kwargs,
        )
    path_delta_result = getattr(validation, "path_delta_matches_prediction", _MISSING)
    if path_delta_result is _MISSING:
        path_delta_result = getattr(validation, "matches_prediction", _MISSING)
    path_delta_matches_prediction = path_delta_result is True
    semantic_delta = getattr(validation, "semantic_delta", None)
    semantic_validation = (
        semantic_delta.to_dict()
        if hasattr(semantic_delta, "to_dict")
        else dict(getattr(validation, "semantic_validation", {}) or {})
    )
    semantic_delta_result = getattr(validation, "semantic_delta_matches_prediction", _MISSING)
    semantic_delta_matches_prediction = semantic_delta_result is True
    if not path_delta_matches_prediction:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="fresh_validation_delta_mismatch",
            predicted_delta_paths=predicted_paths,
            actual_delta_paths=tuple(validation.actual_delta_paths),
            toolchain_comparison=toolchain_comparison,
            semantic_validation=semantic_validation,
            taskmaster_authority=authority,
            freshness_validation=freshness,
            **base_kwargs,
        )
    if not semantic_delta_matches_prediction:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="fresh_validation_semantic_mismatch",
            predicted_delta_paths=predicted_paths,
            actual_delta_paths=tuple(validation.actual_delta_paths),
            toolchain_comparison=toolchain_comparison,
            semantic_validation=semantic_validation,
            taskmaster_authority=authority,
            freshness_validation=freshness,
            **base_kwargs,
        )

    claim = idempotency_store.claim(idempotency_key)
    if not claim.claimed:
        return ReconcileApplyResult(
            status="noop",
            enabled=True,
            mutated=False,
            reason="idempotency_already_claimed",
            predicted_delta_paths=predicted_paths,
            idempotency_key=idempotency_key,
            toolchain_comparison=toolchain_comparison,
            taskmaster_authority=authority,
            freshness_validation=freshness,
            **base_kwargs,
        )

    before = _capture_tree_snapshot(target_root)
    rollback_handle = SnapshotRollbackHandle(before)
    authorization_binding = authorization_binding_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=proof_artifact,
    )
    audit_records: list[dict[str, Any]] = []
    before_audit = _build_runtime_audit(
        phase="before",
        candidate=candidate,
        proof_artifact=proof_artifact,
        authorization_binding=authorization_binding,
        rollback_handle_ref=rollback_handle.ref,
        rolled_back=False,
        approved_context_proof=approved_context_proof,
        toolchain_evidence=current_toolchain_evidence,
        predicted_paths=predicted_paths,
        actual_paths=(),
        before_hashes=rollback_handle.hashes_for(predicted_paths),
        after_hashes={},
        outcome="started",
        semantic_validation=semantic_validation,
    )
    audit_records.append(before_audit)
    _append_audit(audit_log_path, before_audit)

    writer = write_runner or _perform_taskmaster_done_write
    try:
        writer(
            target_root=target_root,
            task_id=candidate.task_id,
            inject_failure_after=inject_failure_after,
        )
    except Exception as exc:  # noqa: BLE001 - rollback must run for all write failures.
        return _rollback_after_failure(
            target_root=target_root,
            changed_paths=_delta_paths(before, _capture_tree_snapshot(target_root)),
            rollback_handle=rollback_handle,
            rollback_restore=rollback_restore,
            reason="write_failed",
            error=str(exc),
            candidate=candidate,
            approved_context=context,
            kill_switch=kill_switch,
            proof_artifact=proof_artifact,
            authorization_binding=authorization_binding,
            approved_context_proof=approved_context_proof,
            toolchain_evidence=current_toolchain_evidence,
            predicted_paths=predicted_paths,
            idempotency_key=idempotency_key,
            audit_log_path=audit_log_path,
            audit_records=audit_records,
            kill_switch_path=kill_switch_path,
            toolchain_comparison=toolchain_comparison,
        )

    after = _capture_tree_snapshot(target_root)
    actual_paths = tuple(_delta_paths(before, after))
    if actual_paths != predicted_paths:
        return _rollback_after_failure(
            target_root=target_root,
            changed_paths=actual_paths,
            rollback_handle=rollback_handle,
            rollback_restore=rollback_restore,
            reason="live_delta_mismatch",
            error="actual live delta did not match fresh validation prediction",
            candidate=candidate,
            approved_context=context,
            kill_switch=kill_switch,
            proof_artifact=proof_artifact,
            authorization_binding=authorization_binding,
            approved_context_proof=approved_context_proof,
            toolchain_evidence=current_toolchain_evidence,
            predicted_paths=predicted_paths,
            idempotency_key=idempotency_key,
            audit_log_path=audit_log_path,
            audit_records=audit_records,
            kill_switch_path=kill_switch_path,
            toolchain_comparison=toolchain_comparison,
        )
    live_semantic_validation = validate_taskmaster_apply_semantic_delta(
        before=_semantic_inputs_from_snapshot(
            before, task_id=candidate.task_id, predicted_paths=predicted_paths
        ),
        after=_semantic_inputs_from_snapshot(
            after, task_id=candidate.task_id, predicted_paths=predicted_paths
        ),
        task_id=candidate.task_id,
        expected_status=candidate.proposed_status,
    ).to_dict()
    if live_semantic_validation.get("passed") is not True:
        return _rollback_after_failure(
            target_root=target_root,
            changed_paths=actual_paths,
            rollback_handle=rollback_handle,
            rollback_restore=rollback_restore,
            reason="live_semantic_delta_mismatch",
            error=str(live_semantic_validation.get("reason") or "semantic validation failed"),
            candidate=candidate,
            approved_context=context,
            kill_switch=kill_switch,
            proof_artifact=proof_artifact,
            authorization_binding=authorization_binding,
            approved_context_proof=approved_context_proof,
            toolchain_evidence=current_toolchain_evidence,
            predicted_paths=predicted_paths,
            idempotency_key=idempotency_key,
            audit_log_path=audit_log_path,
            audit_records=audit_records,
            kill_switch_path=kill_switch_path,
            toolchain_comparison=toolchain_comparison,
            semantic_validation=live_semantic_validation,
        )

    after_audit = _build_runtime_audit(
        phase="after",
        candidate=candidate,
        proof_artifact=proof_artifact,
        authorization_binding=authorization_binding,
        rollback_handle_ref=rollback_handle.ref,
        rolled_back=False,
        approved_context_proof=approved_context_proof,
        toolchain_evidence=current_toolchain_evidence,
        predicted_paths=predicted_paths,
        actual_paths=actual_paths,
        before_hashes=rollback_handle.hashes_for(actual_paths),
        after_hashes={path: after[path].fingerprint() for path in actual_paths},
        outcome="applied",
        semantic_validation=live_semantic_validation,
        previous_hash=before_audit["chain_hash"],
    )
    audit_records.append(after_audit)
    _append_audit(audit_log_path, after_audit)
    return ReconcileApplyResult(
        status="applied",
        enabled=True,
        mutated=True,
        reason="applied",
        predicted_delta_paths=predicted_paths,
        actual_delta_paths=actual_paths,
        idempotency_key=idempotency_key,
        audit_records=tuple(audit_records),
        rollback_state={"rolled_back": False},
        toolchain_comparison=toolchain_comparison,
        semantic_validation=live_semantic_validation,
        taskmaster_authority=authority,
        freshness_validation=freshness,
        **base_kwargs,
    )


def run_selected_channel_apply_with_process_oracle(
    candidate_payload: Mapping[str, Any],
    *,
    target_root: Path,
    selected_channel_confirmation: Mapping[str, Any] | None,
    kill_switch_state: Mapping[str, Any] | None = None,
    validated_toolchain_evidence: Mapping[str, Any] | None = None,
    current_toolchain_evidence: Mapping[str, Any] | None = None,
    state_root: Path | None = None,
    kill_switch_path: Path | None = None,
    enable_write_path: bool = False,
    validation_runner: Callable[..., Any] | None = None,
    write_runner: Callable[..., None] | None = None,
    rollback_restore: Callable[[SnapshotRollbackHandle, Path, Iterable[str]], None] | None = None,
    inject_failure_after: str = "",
) -> SelectedChannelApplyOracleResult:
    """Run the selected-channel internal apply attempt under a process oracle.

    This is still not a CLI, MCP tool, workflow, or enablement path. It exists so
    the selected future channel has one audited execution wrapper to test before
    any production channel can be made satisfiable.
    """

    target_root = target_root.resolve()
    candidate = ApplyCandidate.from_mapping(candidate_payload)
    confirmation = evaluate_selected_apply_channel_confirmation(
        selected_channel_confirmation,
        candidate=candidate,
        enable_gate_open=enable_write_path,
    )
    process_before = _capture_tree_snapshot(target_root)
    process_handle = SnapshotRollbackHandle(process_before)
    if not confirmation.approved:
        process_oracle = _build_process_oracle_report(
            candidate=candidate,
            confirmation=confirmation,
            before=process_before,
            after=_capture_tree_snapshot(target_root),
            allowed_paths=(),
            status="refused",
            reason=confirmation.reason,
        )
        return SelectedChannelApplyOracleResult(
            status="refused",
            reason=confirmation.reason,
            confirmation=confirmation,
            process_oracle=process_oracle,
            audit_destination=confirmation.audit_destination,
        )

    audit_destination = _resolve_selected_channel_audit_destination(
        confirmation.audit_destination,
        target_root=target_root,
    )
    if audit_destination is None:
        process_oracle = _build_process_oracle_report(
            candidate=candidate,
            confirmation=confirmation,
            before=process_before,
            after=_capture_tree_snapshot(target_root),
            allowed_paths=(),
            status="refused",
            reason="selected_channel_audit_destination_invalid",
        )
        return SelectedChannelApplyOracleResult(
            status="refused",
            reason="selected_channel_audit_destination_invalid",
            confirmation=confirmation,
            process_oracle=process_oracle,
            audit_destination=confirmation.audit_destination,
        )

    external_artifacts = (
        (audit_destination / CHANNEL_CONFIRMATION_FILENAME).as_posix(),
        (audit_destination / "apply-audit.jsonl").as_posix(),
        (audit_destination / PROCESS_ORACLE_FILENAME).as_posix(),
    )
    try:
        _write_json_artifact(
            audit_destination / CHANNEL_CONFIRMATION_FILENAME,
            dict(selected_channel_confirmation or {}),
        )
    except OSError as exc:
        process_oracle = _build_process_oracle_report(
            candidate=candidate,
            confirmation=confirmation,
            before=process_before,
            after=_capture_tree_snapshot(target_root),
            allowed_paths=(),
            status="refused",
            reason="selected_channel_confirmation_artifact_write_failed",
            error=str(exc),
            external_artifacts=external_artifacts,
        )
        return SelectedChannelApplyOracleResult(
            status="refused",
            reason="selected_channel_confirmation_artifact_write_failed",
            confirmation=confirmation,
            process_oracle=process_oracle,
            audit_destination=audit_destination.as_posix(),
            external_artifacts=external_artifacts,
        )

    apply_result: ReconcileApplyResult | None = None
    runtime_error = ""
    try:
        apply_result = run_reconcile_apply_write_apparatus(
            candidate_payload,
            target_root=target_root,
            approved_context_proof=selected_channel_confirmation,
            kill_switch_state=kill_switch_state,
            validated_toolchain_evidence=validated_toolchain_evidence,
            current_toolchain_evidence=current_toolchain_evidence,
            state_root=state_root,
            audit_log_path=audit_destination / "apply-audit.jsonl",
            kill_switch_path=kill_switch_path,
            enable_write_path=enable_write_path,
            validation_runner=validation_runner,
            write_runner=write_runner,
            rollback_restore=rollback_restore,
            inject_failure_after=inject_failure_after,
        )
    except Exception as exc:  # noqa: BLE001 - oracle must report runtime failures.
        runtime_error = str(exc)

    process_after = _capture_tree_snapshot(target_root)
    allowed_paths = (
        apply_result.actual_delta_paths
        if apply_result is not None and apply_result.status == "applied"
        else ()
    )
    process_delta = tuple(_delta_paths(process_before, process_after))
    unexpected = tuple(path for path in process_delta if path not in set(allowed_paths))
    missing = tuple(path for path in allowed_paths if path not in set(process_delta))
    if runtime_error:
        oracle_status = "failed" if process_delta else "refused"
        oracle_reason = "selected_channel_runtime_error"
    elif unexpected or missing:
        oracle_status = "failed"
        oracle_reason = "process_oracle_delta_mismatch"
    else:
        oracle_status = "passed"
        oracle_reason = apply_result.reason if apply_result else "selected_channel_runtime_error"

    process_oracle = _build_process_oracle_report(
        candidate=candidate,
        confirmation=confirmation,
        before=process_before,
        after=process_after,
        allowed_paths=allowed_paths,
        status=oracle_status,
        reason=oracle_reason,
        error=runtime_error,
        external_artifacts=external_artifacts,
    )

    if oracle_status == "failed" and process_delta:
        terminal = _rollback_process_oracle_delta(
            target_root=target_root,
            process_handle=process_handle,
            process_delta=process_delta,
            rollback_restore=rollback_restore,
            candidate=candidate,
            confirmation=confirmation,
            reason=oracle_reason,
            error=runtime_error or "process-level oracle delta did not match allowed paths",
            audit_log_path=audit_destination / "apply-audit.jsonl",
            kill_switch_path=kill_switch_path,
        )
        process_oracle["rollback_state"] = terminal["rollback_state"]
        if terminal["status"] == "terminal_rollback_failed":
            _safe_write_process_oracle(audit_destination, process_oracle)
            return SelectedChannelApplyOracleResult(
                status="terminal_rollback_failed",
                reason="rollback_failed",
                confirmation=confirmation,
                process_oracle=process_oracle,
                apply_result=apply_result,
                audit_destination=audit_destination.as_posix(),
                external_artifacts=external_artifacts,
            )
        process_oracle["actual_delta_paths_after_rollback"] = list(
            _delta_paths(process_before, _capture_tree_snapshot(target_root))
        )
        _safe_write_process_oracle(audit_destination, process_oracle)
        return SelectedChannelApplyOracleResult(
            status="rolled_back",
            reason=oracle_reason,
            confirmation=confirmation,
            process_oracle=process_oracle,
            apply_result=apply_result,
            audit_destination=audit_destination.as_posix(),
            external_artifacts=external_artifacts,
        )

    _safe_write_process_oracle(audit_destination, process_oracle)
    if apply_result is None:
        return SelectedChannelApplyOracleResult(
            status="refused",
            reason=oracle_reason,
            confirmation=confirmation,
            process_oracle=process_oracle,
            audit_destination=audit_destination.as_posix(),
            external_artifacts=external_artifacts,
        )
    return SelectedChannelApplyOracleResult(
        status=apply_result.status,
        reason=apply_result.reason,
        confirmation=confirmation,
        process_oracle=process_oracle,
        apply_result=apply_result,
        audit_destination=audit_destination.as_posix(),
        external_artifacts=external_artifacts,
    )


def _taskmaster_authority_decision(target_root: Path) -> tuple[dict[str, Any], Any]:
    state = _taskmaster_state(target_root)
    details = dict(state.details())
    if "reason" in details:
        details["authority_reason"] = details.pop("reason")
    if state.state == "absent":
        return (
            {
                **details,
                "passed": False,
                "reason": "taskmaster_authority_missing",
            },
            state,
        )
    if state.state != "valid":
        return (
            {
                **details,
                "passed": False,
                "reason": "taskmaster_authority_invalid",
            },
            state,
        )
    return (
        {
            **details,
            "passed": True,
            "reason": "taskmaster_authority_valid",
        },
        state,
    )


def _candidate_freshness_decision(
    candidate: ApplyCandidate,
    *,
    target_root: Path,
    taskmaster_state: Any,
) -> dict[str, Any]:
    tasks = _taskmaster_tasks_by_id_from_state(taskmaster_state)
    task = tasks.get(candidate.task_id)
    if task is None:
        return {
            "passed": False,
            "reason": "candidate_task_missing",
            "task_id": candidate.task_id,
        }

    live_status = _normalize_taskmaster_status(task.get("status"))
    recorded_status = _normalize_taskmaster_status(candidate.current_status)
    base: dict[str, Any] = {
        "task_id": candidate.task_id,
        "live_status": live_status,
        "recorded_status": recorded_status,
        "expected_class_key": FIRST_APPLY_CLASS_KEY,
    }
    if live_status in _DONE_TASKMASTER_STATUSES:
        return {
            "passed": False,
            "reason": "candidate_already_done",
            **base,
        }
    if recorded_status and recorded_status != live_status:
        return {
            "passed": False,
            "reason": "candidate_status_changed",
            **base,
        }

    try:
        report = reconcile(
            target_root,
            base_ref=None,
            use_github=False,
            preview_candidates=True,
        )
    except AegisError as exc:
        return {
            "passed": False,
            "reason": "candidate_freshness_unavailable",
            "message": str(exc),
            **base,
        }

    preview = (
        report.get("mutation_candidate_preview")
        if isinstance(report.get("mutation_candidate_preview"), Mapping)
        else {}
    )
    live_candidates = (
        preview.get("candidates") if isinstance(preview.get("candidates"), list) else []
    )
    for item in live_candidates:
        if not isinstance(item, Mapping):
            continue
        if (
            str(item.get("task_id") or "") == candidate.task_id
            and str(item.get("finding_kind") or item.get("kind") or "") == candidate.finding_kind
            and str(item.get("proof") or "") == candidate.proof
        ):
            return {
                "passed": True,
                "reason": "candidate_fresh",
                "live_candidate": dict(item),
                **base,
            }

    task_report = _reconcile_task_report(report, candidate.task_id)
    merge_truth = (
        task_report.get("merge_truth")
        if isinstance(task_report.get("merge_truth"), Mapping)
        else {}
    )
    merge_status = str(merge_truth.get("status") or "")
    merge_proof = str(merge_truth.get("proof") or "")
    reason = (
        "candidate_not_merged"
        if merge_status != "merged"
        else "candidate_not_git_ancestor"
        if merge_proof != "git_ancestor"
        else "candidate_no_longer_auto_eligible"
    )
    return {
        "passed": False,
        "reason": reason,
        "merge_truth": dict(merge_truth),
        "live_candidate_count": len(live_candidates),
        **base,
    }


def _reconcile_task_report(report: Mapping[str, Any], task_id: str) -> Mapping[str, Any]:
    tasks = report.get("tasks") if isinstance(report.get("tasks"), list) else []
    for item in tasks:
        if isinstance(item, Mapping) and str(item.get("task_id") or "") == task_id:
            return item
    return {}


def _normalize_taskmaster_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _rollback_after_failure(
    *,
    target_root: Path,
    changed_paths: Iterable[str],
    rollback_handle: SnapshotRollbackHandle,
    rollback_restore: Callable[[SnapshotRollbackHandle, Path, Iterable[str]], None] | None,
    reason: str,
    error: str,
    candidate: ApplyCandidate,
    approved_context: ApprovedContextDecision,
    kill_switch: KillSwitchDecision,
    proof_artifact: Mapping[str, Any],
    authorization_binding: str,
    approved_context_proof: Mapping[str, Any] | None,
    toolchain_evidence: Mapping[str, Any],
    predicted_paths: tuple[str, ...],
    idempotency_key: str,
    audit_log_path: Path | None,
    audit_records: list[dict[str, Any]],
    kill_switch_path: Path | None,
    toolchain_comparison: Mapping[str, Any],
    semantic_validation: Mapping[str, Any] | None = None,
) -> ReconcileApplyResult:
    actual_paths = tuple(sorted({_normalize_rel_path(path) for path in changed_paths}))
    before_hashes = rollback_handle.hashes_for(actual_paths)
    try:
        if rollback_restore is None:
            rollback_handle.restore(target_root, actual_paths)
        else:
            rollback_restore(rollback_handle, target_root, actual_paths)
    except Exception as exc:  # noqa: BLE001 - terminal state must capture every rollback failure.
        terminal = _terminal_rollback_failure_record(
            candidate=candidate,
            idempotency_key=idempotency_key,
            reason=reason,
            write_error=error,
            rollback_error=str(exc),
            changed_paths=actual_paths,
            kill_switch_path=kill_switch_path,
            audit_log_path=audit_log_path,
        )
        _engage_terminal_kill_switch(kill_switch_path, terminal)
        _append_audit(audit_log_path, terminal)
        return ReconcileApplyResult(
            status="terminal_rollback_failed",
            enabled=True,
            mutated=True,
            reason="rollback_failed",
            candidate=candidate,
            approved_context=approved_context,
            kill_switch=kill_switch,
            predicted_delta_paths=predicted_paths,
            actual_delta_paths=actual_paths,
            idempotency_key=idempotency_key,
            audit_records=tuple([*audit_records, terminal]),
            rollback_state={"rolled_back": False, "terminal_failure": True},
            toolchain_comparison=toolchain_comparison,
            semantic_validation=semantic_validation,
        )

    after = _capture_tree_snapshot(target_root)
    after_hashes = {
        path: after.get(path, SnapshotEntry(kind="missing")).fingerprint() for path in actual_paths
    }
    rolled_back = all(after_hashes.get(path) == before_hashes.get(path) for path in actual_paths)
    audit = _build_runtime_audit(
        phase="after",
        candidate=candidate,
        proof_artifact=proof_artifact,
        authorization_binding=authorization_binding,
        rollback_handle_ref=rollback_handle.ref,
        rolled_back=rolled_back,
        approved_context_proof=approved_context_proof,
        toolchain_evidence=toolchain_evidence,
        predicted_paths=predicted_paths,
        actual_paths=actual_paths,
        before_hashes=before_hashes,
        after_hashes=after_hashes,
        outcome=reason,
        rollback_state={"rolled_back": rolled_back, "error": error},
        semantic_validation=semantic_validation,
        previous_hash=audit_records[-1]["chain_hash"] if audit_records else "",
    )
    audit_records.append(audit)
    _append_audit(audit_log_path, audit)
    return ReconcileApplyResult(
        status="rolled_back",
        enabled=True,
        mutated=False,
        reason=reason,
        candidate=candidate,
        approved_context=approved_context,
        kill_switch=kill_switch,
        predicted_delta_paths=predicted_paths,
        actual_delta_paths=actual_paths,
        idempotency_key=idempotency_key,
        audit_records=tuple(audit_records),
        rollback_state={"rolled_back": rolled_back, "error": error},
        toolchain_comparison=toolchain_comparison,
        semantic_validation=semantic_validation,
    )


def _build_runtime_audit(
    *,
    phase: str,
    candidate: ApplyCandidate,
    proof_artifact: Mapping[str, Any],
    authorization_binding: str,
    rollback_handle_ref: str,
    rolled_back: bool,
    approved_context_proof: Mapping[str, Any] | None,
    toolchain_evidence: Mapping[str, Any],
    predicted_paths: Iterable[str],
    actual_paths: Iterable[str],
    before_hashes: Mapping[str, str],
    after_hashes: Mapping[str, str],
    outcome: str,
    rollback_state: Mapping[str, Any] | None = None,
    semantic_validation: Mapping[str, Any] | None = None,
    previous_hash: str = "",
) -> dict[str, Any]:
    return build_apply_audit_record(
        phase=phase,
        candidate=candidate,
        proof_artifact=proof_artifact,
        allowed_delta_hashes=before_hashes,
        approved_context_proof_id=str((approved_context_proof or {}).get("proof_id") or ""),
        authorization_binding=authorization_binding,
        rollback_handle_ref=rollback_handle_ref,
        rolled_back=rolled_back,
        eligibility_corpus_version=APPLY_ELIGIBILITY_VERSION,
        previous_hash=previous_hash,
        external_anchor=str((approved_context_proof or {}).get("external_anchor") or ""),
        toolchain_evidence=toolchain_evidence,
        predicted_delta_paths=tuple(predicted_paths),
        actual_delta_paths=tuple(actual_paths),
        before_hashes=before_hashes,
        after_hashes=after_hashes,
        outcome=outcome,
        rollback_state=rollback_state or {},
        semantic_validation=semantic_validation or {},
        channel_identity=_channel_identity_from_context(approved_context_proof),
        audit_destination=str((approved_context_proof or {}).get("audit_destination") or ""),
    )


def _validated_toolchain_baseline_refusal_reason(evidence: Mapping[str, Any]) -> str:
    if not isinstance(evidence, Mapping):
        return "validated_toolchain_evidence_malformed"
    if evidence.get("evidence_role") != "validated_ci_baseline":
        return "validated_toolchain_baseline_missing"
    baseline_source = evidence.get("baseline_source")
    if not isinstance(baseline_source, Mapping):
        return "validated_toolchain_baseline_missing"
    expected = {
        "type": "source_controlled_constants",
        "task_master_package_version": TASKMASTER_PACKAGE_VERSION,
        "task_master_install_spec": taskmaster_install_spec(),
        "task_master_node_version": TASKMASTER_NODE_VERSION,
        "lock_id": TASKMASTER_PROVISIONING_LOCK_ID,
        "lock_version": TASKMASTER_TOOLCHAIN_LOCK_VERSION,
    }
    for key, expected_value in expected.items():
        if baseline_source.get(key) != expected_value:
            return "validated_toolchain_baseline_mismatch"
    return ""


def _channel_identity_from_context(
    approved_context_proof: Mapping[str, Any] | None,
) -> dict[str, Any]:
    proof = dict(approved_context_proof or {})
    ci = proof.get("ci") if isinstance(proof.get("ci"), Mapping) else {}
    return {
        "selected_channel": str(proof.get("selected_channel") or proof.get("context_type") or ""),
        "proof_id": str(proof.get("proof_id") or ""),
        "operator_identity": str(proof.get("operator_identity") or ""),
        "external_anchor": str(proof.get("external_anchor") or ""),
        "ci": dict(ci),
    }


def _resolve_selected_channel_audit_destination(
    audit_destination: str,
    *,
    target_root: Path,
) -> Path | None:
    if not audit_destination:
        return None
    try:
        destination = Path(audit_destination).expanduser().resolve()
    except (OSError, ValueError):
        return None
    if _path_is_relative_to(destination, target_root.resolve()):
        return None
    return destination


def _build_process_oracle_report(
    *,
    candidate: ApplyCandidate,
    confirmation: SelectedChannelConfirmationDecision,
    before: Mapping[str, SnapshotEntry],
    after: Mapping[str, SnapshotEntry],
    allowed_paths: Iterable[str],
    status: str,
    reason: str,
    error: str = "",
    external_artifacts: Iterable[str] = (),
) -> dict[str, Any]:
    actual_paths = tuple(_delta_paths(before, after))
    allowed = tuple(sorted({_normalize_rel_path(path) for path in allowed_paths}))
    unexpected = tuple(path for path in actual_paths if path not in set(allowed))
    missing = tuple(path for path in allowed if path not in set(actual_paths))
    payload: dict[str, Any] = {
        "record_type": PROCESS_ORACLE_RECORD_TYPE,
        "selected_channel": confirmation.channel,
        "status": status,
        "reason": reason,
        "task_id": candidate.task_id,
        "finding_kind": candidate.finding_kind,
        "proof": candidate.proof,
        "proof_id": confirmation.proof_id,
        "idempotency_key": confirmation.idempotency_key,
        "audit_destination": confirmation.audit_destination,
        "external_anchor": confirmation.external_anchor,
        "allowed_delta_paths": list(allowed),
        "actual_delta_paths": list(actual_paths),
        "unexpected_delta_paths": list(unexpected),
        "missing_delta_paths": list(missing),
        "before_ref": SnapshotRollbackHandle(before).ref,
        "after_ref": SnapshotRollbackHandle(after).ref,
        "oracle_backed_mutation_time_blast_radius": status == "passed",
        "allowed_external_artifacts": list(external_artifacts),
        "error": error,
    }
    payload["chain_hash"] = _digest(payload)
    return payload


def _rollback_process_oracle_delta(
    *,
    target_root: Path,
    process_handle: SnapshotRollbackHandle,
    process_delta: Iterable[str],
    rollback_restore: Callable[[SnapshotRollbackHandle, Path, Iterable[str]], None] | None,
    candidate: ApplyCandidate,
    confirmation: SelectedChannelConfirmationDecision,
    reason: str,
    error: str,
    audit_log_path: Path | None,
    kill_switch_path: Path | None,
) -> dict[str, Any]:
    changed_paths = tuple(sorted({_normalize_rel_path(path) for path in process_delta}))
    try:
        if rollback_restore is None:
            process_handle.restore(target_root, changed_paths)
        else:
            rollback_restore(process_handle, target_root, changed_paths)
    except Exception as exc:  # noqa: BLE001 - terminal state must capture rollback failure.
        terminal = _terminal_rollback_failure_record(
            candidate=candidate,
            idempotency_key=confirmation.idempotency_key,
            reason=reason,
            write_error=error,
            rollback_error=str(exc),
            changed_paths=changed_paths,
            kill_switch_path=kill_switch_path,
            audit_log_path=audit_log_path,
        )
        _engage_terminal_kill_switch(kill_switch_path, terminal)
        _append_audit(audit_log_path, terminal)
        return {
            "status": "terminal_rollback_failed",
            "rollback_state": {"rolled_back": False, "terminal_failure": True},
        }
    return {
        "status": "rolled_back",
        "rollback_state": {"rolled_back": True, "error": error},
    }


def _write_json_artifact(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_write_process_oracle(audit_destination: Path, payload: Mapping[str, Any]) -> None:
    try:
        _write_json_artifact(audit_destination / PROCESS_ORACLE_FILENAME, payload)
    except OSError:
        # The process oracle result is still returned to the caller. A future
        # production channel can choose to treat report persistence failure as
        # terminal once G2/G3 define the production enable mechanism.
        return


def _path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _perform_taskmaster_done_write(
    *,
    target_root: Path,
    task_id: str,
    inject_failure_after: str = "",
) -> None:
    if not _is_under_temp(target_root.resolve()):
        raise ReconcileApplyRuntimeError(
            f"live apply target must be isolated under temp: {target_root}"
        )
    _run_target_command(
        target_root, "task-master", "set-status", f"--id={task_id}", "--status=done"
    )
    if inject_failure_after == "set-status":
        raise ReconcileApplyRuntimeError("injected failure after set-status")
    if (target_root / "scripts" / "codex-task").exists():
        _run_target_command(
            target_root,
            "python3",
            "scripts/codex-task",
            "taskmaster",
            "generate-one",
            "--id",
            str(task_id),
        )
    else:
        _run_target_command(target_root, "task-master", "generate")


def _run_target_command(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ReconcileApplyRuntimeError(result.stderr or result.stdout)
    return result


def _capture_tree_snapshot(root: Path) -> dict[str, SnapshotEntry]:
    return {
        rel_path: _snapshot_entry_for(path)
        for rel_path, path in _iter_paths(root)
        if not _matches_any(rel_path, SACRIFICIAL_CLONE_IGNORE_PATTERNS)
    }


def _snapshot_entry_for(path: Path) -> SnapshotEntry:
    if not path.exists() and not path.is_symlink():
        return SnapshotEntry(kind="missing")
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if path.is_symlink():
        return SnapshotEntry(kind="symlink", mode=mode, symlink_target=path.readlink().as_posix())
    if path.is_dir():
        return SnapshotEntry(kind="directory", mode=mode)
    if path.is_file():
        content = path.read_bytes()
        return SnapshotEntry(
            kind="file",
            mode=mode,
            digest=hashlib.sha256(content).hexdigest(),
            content=content,
        )
    return SnapshotEntry(kind="other", mode=mode)


def _delta_paths(
    before: Mapping[str, SnapshotEntry],
    after: Mapping[str, SnapshotEntry],
) -> list[str]:
    return [
        path for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)
    ]


def _semantic_inputs_from_snapshot(
    snapshot: Mapping[str, SnapshotEntry],
    *,
    task_id: str,
    predicted_paths: Iterable[str],
) -> dict[str, Any]:
    tasks_json_text = _text_from_snapshot(snapshot, ".taskmaster/tasks/tasks.json")
    payload: dict[str, Any] = {"tasks_json": json.loads(tasks_json_text)}
    generated_rel = _taskmaster_generated_task_markdown_rel(task_id)
    if generated_rel in {_normalize_rel_path(path) for path in predicted_paths}:
        payload["generated_task_markdown"] = _text_from_snapshot(
            snapshot, generated_rel, missing_ok=True
        )
    return payload


def _text_from_snapshot(
    snapshot: Mapping[str, SnapshotEntry],
    rel_path: str,
    *,
    missing_ok: bool = False,
) -> str | None:
    entry = snapshot.get(_normalize_rel_path(rel_path))
    if entry is None or entry.kind == "missing":
        if missing_ok:
            return None
        raise ReconcileApplyRuntimeError(f"semantic snapshot path is missing: {rel_path}")
    if entry.kind != "file" or entry.content is None:
        raise ReconcileApplyRuntimeError(f"semantic snapshot path is not a file: {rel_path}")
    return entry.content.decode("utf-8")


def _terminal_rollback_failure_present(state: Mapping[str, Any] | None) -> bool:
    if not isinstance(state, Mapping):
        return False
    terminal = state.get("terminal_failure")
    return (
        isinstance(terminal, Mapping)
        and terminal.get("record_type") == TERMINAL_ROLLBACK_RECORD_TYPE
        and terminal.get("auto_clear_allowed") is False
    )


def _iter_paths(root: Path) -> list[tuple[str, Path]]:
    paths = [root] + sorted(root.rglob("*"), key=lambda path: path.as_posix())
    result: list[tuple[str, Path]] = []
    for path in paths:
        if path == root:
            continue
        rel_path = _normalize_rel_path(path.relative_to(root).as_posix())
        result.append((rel_path, path))
    return result


def _restore_entry(path: Path, entry: SnapshotEntry) -> None:
    if entry.kind == "missing":
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if entry.kind == "directory":
        path.mkdir(exist_ok=True)
    elif entry.kind == "symlink":
        path.symlink_to(entry.symlink_target or "")
    elif entry.kind == "file":
        path.write_bytes(entry.content or b"")
    else:
        raise ReconcileApplyRuntimeError(f"unsupported rollback entry kind: {entry.kind}")
    if entry.mode is not None and not path.is_symlink():
        path.chmod(entry.mode)


def _remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _append_audit(path: Path | None, record: Mapping[str, Any]) -> None:
    if path is None:
        return
    if not _is_under_temp(path.resolve().parent):
        raise ReconcileApplyRuntimeError(f"apply audit path must be isolated under temp: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True)
        handle.write("\n")


def _terminal_rollback_failure_record(
    *,
    candidate: ApplyCandidate,
    idempotency_key: str,
    reason: str,
    write_error: str,
    rollback_error: str,
    changed_paths: Iterable[str],
    kill_switch_path: Path | None,
    audit_log_path: Path | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_type": TERMINAL_ROLLBACK_RECORD_TYPE,
        "task_id": candidate.task_id,
        "finding_kind": candidate.finding_kind,
        "proof": candidate.proof,
        "idempotency_key": idempotency_key,
        "reason": reason,
        "write_error": write_error,
        "rollback_error": rollback_error,
        "changed_paths": list(changed_paths),
        "kill_switch_engaged": kill_switch_path.as_posix() if kill_switch_path else "",
        "audit_log_path": audit_log_path.as_posix() if audit_log_path else "",
        "audit_linked": audit_log_path is not None,
        "operator_resolution_required": True,
        "auto_clear_allowed": False,
        "auto_retry_allowed": False,
    }
    payload["chain_hash"] = _digest(payload)
    return payload


def _engage_terminal_kill_switch(path: Path | None, terminal_record: Mapping[str, Any]) -> None:
    if path is None:
        return
    if not _is_under_temp(path.resolve().parent):
        raise ReconcileApplyRuntimeError(
            f"terminal kill-switch path must be isolated under temp: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "global": {"enabled": False, "disabled": True},
        "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": False, "disabled": True}},
        "terminal_failure": dict(terminal_record),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_under_temp(path: Path) -> bool:
    try:
        path.resolve().relative_to(Path(tempfile.gettempdir()).resolve())
    except ValueError:
        return False
    return True


def _digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
