"""Shadow-mode reconcile apply artifacts.

This module models the first future apply pipeline without enabling live mutation.
It may validate Taskmaster's done cascade inside a sacrificial copy, but it never
calls Taskmaster, Git, GitHub, closeout, or workflow-state writers against the
governed repository.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from aegis_foundation.reconcile_apply_scaffold import (
    FIRST_APPLY_PROOF,
    ApplyCandidate,
    authorization_binding_for,
    build_apply_audit_record,
    evaluate_approved_context,
    evaluate_kill_switch,
)

SHADOW_MODE = "shadow"
SHADOW_REPORT_TYPE = "reconcile_shadow_apply_report"
SHADOW_RECORD_TYPE = "reconcile_shadow_apply"
SHADOW_CI_CONTEXT_TYPE = "post_merge_ci"
SHADOW_ARTIFACT_NAME = "reconcile-shadow-apply"
SHADOW_ELIGIBILITY_VERSION = "task146-v1"
SHADOW_ALLOWED_DECISION_REASON = "enable_gate_unsatisfiable"
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

    @property
    def matches_prediction(self) -> bool:
        return self.actual_delta_paths == self.predicted_paths

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
            "sacrificial_delta_matches_prediction": self.matches_prediction,
            "rollback_baseline_metadata": self.rollback_baseline_metadata,
            "clone_fidelity": self.clone_fidelity,
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
    proof_id = f"github-actions:{run_id}:{run_attempt}" if run_id else ""
    return {
        "context_type": SHADOW_CI_CONTEXT_TYPE,
        "proof_id": proof_id,
        "task_id": str(task_id),
        "proof": str(proof),
        "external_anchor": proof_id,
        "ci": {
            "provider": "github_actions",
            "run_id": run_id,
            "run_attempt": run_attempt,
            "workflow": workflow,
            "repository": repository,
            "sha": sha,
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
    predicted_paths = _predicted_paths(
        candidate_payload,
        task_id=candidate.task_id,
        target_root=target_root,
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
    if not validation.matches_prediction:
        base["decision"] = "shadow_refused"
        base["reason"] = "sacrificial_delta_mismatch"
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
    predicted = tuple(sorted({_normalize_rel_path(path) for path in predicted_paths}))
    if not predicted:
        raise ShadowApplyError("predicted blast-radius paths are required")
    if not (target_root / ".taskmaster" / "tasks" / "tasks.json").exists():
        raise ShadowApplyError("target root does not contain Taskmaster tasks.json")

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

        target_baseline = _metadata_for_paths(target_root, predicted)
        clone_baseline = _metadata_for_paths(clone_root, predicted)
        clone_fidelity = {
            "detached": clone_root.resolve() != target_root,
            "relevant_paths_match": {
                path: target_baseline[path].to_dict() == clone_baseline[path].to_dict()
                for path in predicted
            },
        }
        if not all(clone_fidelity["relevant_paths_match"].values()):
            raise ShadowApplyError("sacrificial clone does not match target baseline paths")

        before = _snapshot_tree(clone_root)
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
        actual = tuple(sorted(_tree_delta_paths(before, after)))
        return SacrificialValidation(
            clone_root=clone_root,
            predicted_paths=predicted,
            actual_delta_paths=actual,
            baseline_metadata=target_baseline,
            clone_fidelity=clone_fidelity,
        )
    finally:
        if clone_context is not None:
            clone_context.cleanup()


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
) -> tuple[str, ...]:
    raw_paths = candidate_payload.get("predicted_blast_radius_paths")
    paths = raw_paths if isinstance(raw_paths, Sequence) and not isinstance(raw_paths, str) else ()
    if not paths:
        paths = (
            ".taskmaster/tasks/tasks.json",
            _taskmaster_generated_task_markdown_rel(task_id),
        )
    normalized = {_normalize_rel_path(str(path)) for path in paths if str(path)}
    if not (target_root / ".taskmaster" / "state.json").exists():
        normalized.add(".taskmaster/state.json")
    return tuple(sorted(normalized))


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
