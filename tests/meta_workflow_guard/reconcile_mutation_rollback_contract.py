"""Report-only rollback contract helpers for future Aegis reconcile mutation.

These helpers intentionally do not call or extend ``aegis reconcile``. They model the
preconditions a later, separate mutation task would need before reconcile could propose
even the first narrow mutation class.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tests.meta_workflow_guard.reconcile_precision_corpus import FindingKey, bucket_for_finding
from tests.meta_workflow_guard.reconcile_side_effect_oracle import (
    FileSystemSnapshot,
    SnapshotEntry,
    snapshot_whole_tree,
)


FIRST_MUTATION_CANDIDATE = FindingKey("merged_but_not_done", "42", "git_ancestor")
FIRST_MUTATION_KIND = "merged_but_not_done"
FIRST_MUTATION_PROOF = "git_ancestor"
TASKMASTER_DONE_REGISTERED_PATHS = (
    ".taskmaster/tasks/task_042.md",
    ".taskmaster/tasks/tasks.json",
)


class MutationContractError(AssertionError):
    """Raised when a future mutation proposal violates the report-only contract."""


@dataclass(frozen=True)
class AuditBreadcrumb:
    phase: str
    task_id: str
    finding: FindingKey
    handler: str
    proof: str
    outcome: str | None = None


@dataclass(frozen=True)
class BlastRadiusContract:
    registered_paths: tuple[str, ...]

    def assert_exact_delta(self, before: FileSystemSnapshot, after: FileSystemSnapshot) -> tuple[str, ...]:
        expected = set(self.registered_paths)
        actual = {delta.path for delta in before.diff(after)}
        unexpected = sorted(actual - expected)
        missing = sorted(expected - actual)
        if unexpected or missing:
            raise MutationContractError(
                "blast-radius contract mismatch: "
                f"unexpected={unexpected!r} missing={missing!r} actual={sorted(actual)!r}"
            )
        return tuple(sorted(actual))


@dataclass(frozen=True)
class RestorationStep:
    path: str
    method: str


@dataclass(frozen=True)
class RollbackContract:
    blast_radius: BlastRadiusContract
    restoration_steps: tuple[RestorationStep, ...]

    def assert_complete(self, blast_radius: BlastRadiusContract | None = None) -> None:
        blast_radius = blast_radius or self.blast_radius
        planned = {step.path for step in self.restoration_steps}
        expected = set(blast_radius.registered_paths)
        missing = sorted(expected - planned)
        extra = sorted(planned - expected)
        if missing or extra:
            raise MutationContractError(
                "rollback restoration plan must cover exactly the registered paths: "
                f"missing={missing!r} extra={extra!r}"
            )


@dataclass(frozen=True)
class MutationProposal:
    finding: FindingKey
    operator_confirmed: bool
    audit_before: AuditBreadcrumb
    audit_after: AuditBreadcrumb
    blast_radius: BlastRadiusContract
    rollback: RollbackContract


@dataclass(frozen=True)
class _CapturedPath:
    path: str
    entry: SnapshotEntry
    content: bytes | None = None


@dataclass(frozen=True)
class RollbackHandle:
    captured_paths: tuple[_CapturedPath, ...]

    @classmethod
    def capture(cls, root: Path, paths: Iterable[str]) -> "RollbackHandle":
        captured: list[_CapturedPath] = []
        for rel_path in paths:
            rel_path = _normalize_rel_path(rel_path)
            path = root / rel_path
            entry = _entry_for(path)
            content = path.read_bytes() if entry.kind == "file" else None
            captured.append(_CapturedPath(path=rel_path, entry=entry, content=content))
        return cls(captured_paths=tuple(captured))

    def restore(self, root: Path) -> None:
        for captured in self.captured_paths:
            path = root / captured.path
            _remove_existing(path)
            if captured.entry.kind == "missing":
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if captured.entry.kind == "directory":
                path.mkdir(exist_ok=True)
            elif captured.entry.kind == "symlink":
                path.symlink_to(captured.entry.symlink_target or "")
            elif captured.entry.kind == "file":
                path.write_bytes(captured.content or b"")
            else:  # pragma: no cover - unknown file types are not in the contract fixture.
                raise MutationContractError(f"unsupported rollback entry kind: {captured.entry.kind}")
            if captured.entry.mode is not None and not path.is_symlink():
                path.chmod(captured.entry.mode)


@dataclass(frozen=True)
class TaskmasterDoneCascade:
    root: Path
    before: FileSystemSnapshot
    after: FileSystemSnapshot
    blast_radius: BlastRadiusContract
    rollback_handle: RollbackHandle

    @property
    def changed_paths(self) -> tuple[str, ...]:
        return self.blast_radius.assert_exact_delta(self.before, self.after)


def build_mutation_proposal(
    *,
    finding: FindingKey,
    operator_confirmed: bool,
    audit_before: AuditBreadcrumb | None,
    audit_after: AuditBreadcrumb | None,
    blast_radius: BlastRadiusContract,
    rollback: RollbackContract,
) -> MutationProposal:
    _assert_first_candidate(finding)
    if not operator_confirmed:
        raise MutationContractError("operator confirmation is required")
    if audit_before is None or audit_after is None:
        raise MutationContractError("before and after audit breadcrumbs are required")
    _assert_audit(audit_before, phase="before", finding=finding)
    _assert_audit(audit_after, phase="after", finding=finding)
    rollback.assert_complete(blast_radius)
    return MutationProposal(
        finding=finding,
        operator_confirmed=operator_confirmed,
        audit_before=audit_before,
        audit_after=audit_after,
        blast_radius=blast_radius,
        rollback=rollback,
    )


def run_taskmaster_done_cascade_fixture(root: Path, *, task_id: int = 42) -> TaskmasterDoneCascade:
    """Run the real Taskmaster done path in an isolated fixture.

    The repo-specific ``scripts/codex-task taskmaster generate-one`` helper resolves to this
    checkout and is not an isolated-fixture primitive, so this contract uses Taskmaster's
    native generated-file refresh inside the fixture.
    """

    if shutil.which("task-master") is None:
        raise RuntimeError("task-master CLI is required for the real cascade inventory")
    root.mkdir(parents=True, exist_ok=True)
    _write_minimal_taskmaster_fixture(root, task_id=task_id, status="pending")
    _run(root, "task-master", "generate")

    registered_paths = (
        f".taskmaster/tasks/task_{task_id:03d}.md",
        ".taskmaster/tasks/tasks.json",
    )
    before = snapshot_whole_tree(root)
    rollback_handle = RollbackHandle.capture(root, registered_paths)

    _run(root, "task-master", "set-status", f"--id={task_id}", "--status=done")
    _run(root, "task-master", "generate")
    after = snapshot_whole_tree(root)
    blast_radius = BlastRadiusContract(registered_paths=registered_paths)
    blast_radius.assert_exact_delta(before, after)
    return TaskmasterDoneCascade(
        root=root,
        before=before,
        after=after,
        blast_radius=blast_radius,
        rollback_handle=rollback_handle,
    )


def default_rollback_contract(blast_radius: BlastRadiusContract) -> RollbackContract:
    return RollbackContract(
        blast_radius=blast_radius,
        restoration_steps=tuple(
            RestorationStep(path=path, method="restore from before snapshot")
            for path in blast_radius.registered_paths
        ),
    )


def audit_breadcrumb(phase: str, finding: FindingKey = FIRST_MUTATION_CANDIDATE) -> AuditBreadcrumb:
    return AuditBreadcrumb(
        phase=phase,
        task_id=finding.task_id,
        finding=finding,
        handler="aegis:reconcile-proposal-contract",
        proof=finding.proof or "",
        outcome="proposed" if phase == "before" else "completed",
    )


def _assert_first_candidate(finding: FindingKey) -> None:
    if bucket_for_finding(finding) != "auto_eligible":
        raise MutationContractError(f"finding is not auto-eligible: {finding!r}")
    if finding.kind != FIRST_MUTATION_KIND or finding.proof != FIRST_MUTATION_PROOF:
        raise MutationContractError(
            "Task 147 only registers merged_but_not_done with git_ancestor as the first "
            f"future mutation candidate: {finding!r}"
        )


def _assert_audit(audit: AuditBreadcrumb, *, phase: str, finding: FindingKey) -> None:
    if audit.phase != phase:
        raise MutationContractError(f"expected {phase!r} audit breadcrumb, got {audit.phase!r}")
    if audit.finding != finding or audit.task_id != finding.task_id or audit.proof != (finding.proof or ""):
        raise MutationContractError("audit breadcrumb does not match the proposed finding")


def _write_minimal_taskmaster_fixture(root: Path, *, task_id: int, status: str) -> None:
    task_dir = root / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "tasks.json").write_text(
        (
            "{\n"
            '  "master": {\n'
            '    "tasks": [\n'
            "      {\n"
            f'        "id": {task_id},\n'
            '        "title": "Cart Button",\n'
            '        "description": "Add a visible Add to cart button.",\n'
            f'        "status": "{status}",\n'
            '        "priority": "medium",\n'
            '        "dependencies": [],\n'
            '        "details": "Create, label, and attach a button.",\n'
            '        "testStrategy": "Taskmaster cascade inventory fixture.",\n'
            '        "subtasks": []\n'
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n"
        ),
        encoding="utf-8",
    )


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def _entry_for(path: Path) -> SnapshotEntry:
    if not path.exists() and not path.is_symlink():
        return SnapshotEntry(kind="missing")
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if path.is_symlink():
        return SnapshotEntry(kind="symlink", mode=mode, symlink_target=path.readlink().as_posix())
    if path.is_dir():
        return SnapshotEntry(kind="directory", mode=mode)
    if path.is_file():
        return SnapshotEntry(kind="file", mode=mode)
    return SnapshotEntry(kind="other", mode=mode)


def _remove_existing(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _normalize_rel_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")
