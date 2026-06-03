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
    authorization_binding_for,
    build_apply_audit_record,
    evaluate_approved_context,
    evaluate_kill_switch,
    idempotency_key_for,
)
from aegis_foundation.reconcile_shadow_apply import (
    SACRIFICIAL_CLONE_IGNORE_PATTERNS,
    _matches_any,
    _normalize_rel_path,
    _predicted_paths,
    _proof_artifact,
    validate_sacrificial_taskmaster_done_cascade,
)
from aegis_foundation.taskmaster_toolchain import (
    capture_taskmaster_toolchain_evidence,
    compare_taskmaster_toolchain_evidence,
)

APPLY_ELIGIBILITY_VERSION = "task146-v1"
APPLY_AUDIT_RECORD_TYPE = "reconcile_apply_audit"
TERMINAL_ROLLBACK_RECORD_TYPE = "reconcile_apply_terminal_rollback_failure"


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

    def claim(self, key: str) -> IdempotencyClaim:
        safe_key = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in key)
        claims_dir = self.root / "idempotency"
        claims_dir.mkdir(parents=True, exist_ok=True)
        claim_path = claims_dir / f"{safe_key}.json"
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
    if validated_toolchain_evidence is None:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="validated_toolchain_evidence_missing",
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
            **base_kwargs,
        )
    if not validation.matches_prediction:
        return ReconcileApplyResult(
            status="refused",
            enabled=True,
            mutated=False,
            reason="fresh_validation_delta_mismatch",
            predicted_delta_paths=predicted_paths,
            actual_delta_paths=tuple(validation.actual_delta_paths),
            toolchain_comparison=toolchain_comparison,
            **base_kwargs,
        )

    proof_artifact = _proof_artifact(candidate_payload, approved_context_proof)
    idempotency_key = idempotency_key_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=proof_artifact,
    )
    claim = FileIdempotencyStore(state_root).claim(idempotency_key)
    if not claim.claimed:
        return ReconcileApplyResult(
            status="noop",
            enabled=True,
            mutated=False,
            reason="idempotency_already_claimed",
            predicted_delta_paths=predicted_paths,
            idempotency_key=idempotency_key,
            toolchain_comparison=toolchain_comparison,
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
        **base_kwargs,
    )


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
    )


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
        "operator_resolution_required": True,
        "auto_clear_allowed": False,
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
