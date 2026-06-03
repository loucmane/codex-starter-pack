"""Disabled reconcile apply scaffold primitives.

This module intentionally does not expose a CLI, MCP tool, Taskmaster writer, or
workflow-state writer. It models the safety gates a future apply path must pass
while returning only refusal data in the current scaffold.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Mapping

FIRST_APPLY_KIND = "merged_but_not_done"
FIRST_APPLY_PROOF = "git_ancestor"
FIRST_APPLY_CLASS_KEY = f"{FIRST_APPLY_KIND}/{FIRST_APPLY_PROOF}"
APPROVED_CONTEXT_TYPES = frozenset({"post_merge_ci", "operator_controlled_local"})
ZERO_HASH = "0" * 64


@dataclass(frozen=True)
class ApplyCandidate:
    task_id: str
    finding_kind: str
    proof: str
    current_status: str = ""
    proposed_status: str = "done"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ApplyCandidate":
        return cls(
            task_id=str(payload.get("task_id") or ""),
            finding_kind=str(payload.get("finding_kind") or payload.get("kind") or ""),
            proof=str(payload.get("proof") or ""),
            current_status=str(payload.get("current_status") or ""),
            proposed_status=str(payload.get("proposed_status") or "done"),
        )

    @property
    def class_key(self) -> str:
        return f"{self.finding_kind}/{self.proof}"

    @property
    def is_first_apply_class(self) -> bool:
        return self.finding_kind == FIRST_APPLY_KIND and self.proof == FIRST_APPLY_PROOF


@dataclass(frozen=True)
class ApprovedContextDecision:
    approved: bool
    reason: str
    context_type: str = ""
    proof_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "reason": self.reason,
            "context_type": self.context_type,
            "proof_id": self.proof_id,
        }


@dataclass(frozen=True)
class LoadedKillSwitchState:
    raw: Mapping[str, Any] | None
    load_status: str
    path: str = ""

    @property
    def usable(self) -> bool:
        return self.load_status == "loaded" and isinstance(self.raw, Mapping)


@dataclass(frozen=True)
class KillSwitchDecision:
    enabled: bool
    reason: str
    class_key: str

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "reason": self.reason, "class_key": self.class_key}


@dataclass(frozen=True)
class DisabledApplyResult:
    status: str
    enabled: bool
    mutated: bool
    reason: str
    candidate: ApplyCandidate
    approved_context: ApprovedContextDecision
    kill_switch: KillSwitchDecision

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
        }


class ApplyScaffoldError(ValueError):
    """Raised when scaffold model inputs are internally inconsistent."""


def evaluate_approved_context(
    proof: Mapping[str, Any] | None,
    *,
    candidate: ApplyCandidate | None = None,
    enable_gate_open: bool = False,
) -> ApprovedContextDecision:
    """Evaluate a future approved-context proof.

    The public Task 150 scaffold intentionally has no satisfiable enable gate.
    Task 153's internal runtime may pass ``enable_gate_open=True`` in isolated
    test contexts to prove write, rollback, audit, and idempotency machinery
    while keeping the default scaffold refused.
    """

    if proof is None:
        return ApprovedContextDecision(False, "approved_context_missing")
    if not isinstance(proof, Mapping):
        return ApprovedContextDecision(False, "approved_context_malformed")
    context_type = str(proof.get("context_type") or "")
    proof_id = str(proof.get("proof_id") or "")
    if context_type not in APPROVED_CONTEXT_TYPES:
        return ApprovedContextDecision(False, "approved_context_unknown", context_type, proof_id)
    if not proof_id:
        return ApprovedContextDecision(False, "approved_context_malformed", context_type, proof_id)
    if candidate is not None:
        bound_task_id = str(proof.get("task_id") or "")
        bound_proof = str(proof.get("proof") or "")
        if bound_task_id != candidate.task_id or bound_proof != candidate.proof:
            return ApprovedContextDecision(
                False, "approved_context_binding_mismatch", context_type, proof_id
            )
    if not enable_gate_open:
        return ApprovedContextDecision(False, "enable_gate_unsatisfiable", context_type, proof_id)
    return ApprovedContextDecision(True, "approved_context_verified", context_type, proof_id)


def load_kill_switch_state(path: Path | None) -> LoadedKillSwitchState:
    if path is None:
        return LoadedKillSwitchState(raw=None, load_status="missing")
    path = path.resolve()
    if not path.exists():
        return LoadedKillSwitchState(raw=None, load_status="missing", path=path.as_posix())
    if not path.is_file():
        return LoadedKillSwitchState(raw=None, load_status="unreadable", path=path.as_posix())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return LoadedKillSwitchState(raw=None, load_status="unreadable", path=path.as_posix())
    except JSONDecodeError:
        return LoadedKillSwitchState(raw=None, load_status="corrupt", path=path.as_posix())
    if not isinstance(payload, Mapping):
        return LoadedKillSwitchState(raw=None, load_status="corrupt", path=path.as_posix())
    return LoadedKillSwitchState(raw=payload, load_status="loaded", path=path.as_posix())


def evaluate_kill_switch(
    state: Mapping[str, Any] | LoadedKillSwitchState | None,
    *,
    class_key: str = FIRST_APPLY_CLASS_KEY,
    enable_gate_open: bool = False,
) -> KillSwitchDecision:
    if isinstance(state, LoadedKillSwitchState):
        if not state.usable:
            return KillSwitchDecision(False, f"kill_switch_{state.load_status}", class_key)
        state = state.raw
    if state is None:
        return KillSwitchDecision(False, "kill_switch_missing", class_key)
    if not isinstance(state, Mapping):
        return KillSwitchDecision(False, "kill_switch_corrupt", class_key)
    global_state = state.get("global")
    classes = state.get("classes")
    if global_state is None:
        return KillSwitchDecision(False, "kill_switch_default_disabled", class_key)
    if not isinstance(global_state, Mapping) or (
        classes is not None and not isinstance(classes, Mapping)
    ):
        return KillSwitchDecision(False, "kill_switch_corrupt", class_key)
    if global_state.get("disabled") is True:
        return KillSwitchDecision(False, "kill_switch_global_disabled", class_key)
    class_state = classes.get(class_key, {}) if isinstance(classes, Mapping) else {}
    if not isinstance(class_state, Mapping):
        return KillSwitchDecision(False, "kill_switch_corrupt", class_key)
    if class_state.get("disabled") is True:
        return KillSwitchDecision(False, "kill_switch_class_disabled", class_key)
    if global_state.get("enabled") is not True:
        return KillSwitchDecision(False, "kill_switch_default_disabled", class_key)
    if class_state.get("enabled") is not True:
        return KillSwitchDecision(False, "kill_switch_class_default_disabled", class_key)
    if not enable_gate_open:
        return KillSwitchDecision(False, "enable_gate_unsatisfiable", class_key)
    return KillSwitchDecision(True, "kill_switch_enabled", class_key)


def authorization_binding_for(
    *,
    task_id: str,
    finding_kind: str,
    proof: str,
    proof_artifact: Mapping[str, Any],
) -> str:
    return _digest(
        {
            "task_id": str(task_id),
            "finding_kind": str(finding_kind),
            "proof": str(proof),
            "proof_artifact": proof_artifact,
        }
    )


def idempotency_key_for(
    *,
    task_id: str,
    finding_kind: str,
    proof: str,
    proof_artifact: Mapping[str, Any],
) -> str:
    return _digest(
        {
            "version": "task150-disabled-apply-scaffold-v1",
            "task_id": str(task_id),
            "finding_kind": str(finding_kind),
            "proof": str(proof),
            "proof_artifact": proof_artifact,
        }
    )


def build_apply_audit_record(
    *,
    phase: str,
    candidate: ApplyCandidate,
    proof_artifact: Mapping[str, Any],
    allowed_delta_hashes: Mapping[str, str],
    approved_context_proof_id: str,
    authorization_binding: str,
    rollback_handle_ref: str,
    rolled_back: bool,
    eligibility_corpus_version: str,
    previous_hash: str = ZERO_HASH,
    external_anchor: str = "",
    toolchain_evidence: Mapping[str, Any] | None = None,
    predicted_delta_paths: list[str] | tuple[str, ...] = (),
    actual_delta_paths: list[str] | tuple[str, ...] = (),
    before_hashes: Mapping[str, str] | None = None,
    after_hashes: Mapping[str, str] | None = None,
    outcome: str = "",
    rollback_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if phase not in {"before", "after"}:
        raise ApplyScaffoldError("audit phase must be before or after")
    if not candidate.is_first_apply_class:
        raise ApplyScaffoldError("audit candidate is outside the first apply class")
    if not isinstance(proof_artifact, Mapping) or not proof_artifact:
        raise ApplyScaffoldError("proof artifact is required")
    if not isinstance(allowed_delta_hashes, Mapping) or not allowed_delta_hashes:
        raise ApplyScaffoldError("allowed-delta hashes are required")
    required_text = {
        "approved_context_proof_id": approved_context_proof_id,
        "rollback_handle_ref": rollback_handle_ref,
        "eligibility_corpus_version": eligibility_corpus_version,
    }
    missing = [name for name, value in required_text.items() if not str(value)]
    if missing:
        raise ApplyScaffoldError(f"missing audit fields: {', '.join(missing)}")
    expected_binding = authorization_binding_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=proof_artifact,
    )
    if authorization_binding != expected_binding:
        raise ApplyScaffoldError("authorization binding does not match task id and proof")
    idempotency_key = idempotency_key_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=proof_artifact,
    )
    payload: dict[str, Any] = {
        "record_type": "reconcile_apply_audit",
        "phase": phase,
        "task_id": candidate.task_id,
        "finding_kind": candidate.finding_kind,
        "proof": candidate.proof,
        "proof_artifact": dict(proof_artifact),
        "allowed_delta_hashes": dict(allowed_delta_hashes),
        "approved_context_proof_id": approved_context_proof_id,
        "authorization_binding": authorization_binding,
        "rollback_handle_ref": rollback_handle_ref,
        "rolled_back": bool(rolled_back),
        "eligibility_corpus_version": eligibility_corpus_version,
        "idempotency_key": idempotency_key,
        "previous_hash": previous_hash or ZERO_HASH,
        "external_anchor": external_anchor,
        "toolchain_evidence": dict(toolchain_evidence or {}),
        "predicted_delta_paths": list(predicted_delta_paths),
        "actual_delta_paths": list(actual_delta_paths),
        "before_hashes": dict(before_hashes or {}),
        "after_hashes": dict(after_hashes or {}),
        "outcome": outcome,
        "rollback_state": dict(rollback_state or {}),
    }
    payload["chain_hash"] = _digest(payload)
    return payload


def run_disabled_apply_scaffold(
    candidate_payload: Mapping[str, Any],
    *,
    approved_context_proof: Mapping[str, Any] | None = None,
    kill_switch_state: Mapping[str, Any] | LoadedKillSwitchState | None = None,
) -> DisabledApplyResult:
    candidate = ApplyCandidate.from_mapping(candidate_payload)
    context = evaluate_approved_context(approved_context_proof, candidate=candidate)
    kill_switch = evaluate_kill_switch(kill_switch_state, class_key=candidate.class_key)
    if not candidate.is_first_apply_class:
        reason = "candidate_outside_first_apply_class"
    elif not context.approved:
        reason = context.reason
    elif not kill_switch.enabled:
        reason = kill_switch.reason
    else:
        reason = "enable_gate_unsatisfiable"
    return DisabledApplyResult(
        status="refused",
        enabled=False,
        mutated=False,
        reason=reason,
        candidate=candidate,
        approved_context=context,
        kill_switch=kill_switch,
    )


def _digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
