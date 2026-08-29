"""Fail-closed derivation of completed work for the Aegis source checkout."""

from __future__ import annotations

import json
import hashlib
import os
import re
import runpy
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

SOURCE_MARKERS = (
    Path("schemas/aegis/foundation-manifest.schema.json"),
    Path("scripts/_aegis_installer.py"),
    Path(".claude/scripts/readiness.sh"),
    Path("aegis_foundation/assets/.claude/scripts/readiness.sh"),
    Path("aegis_foundation/assets/scripts/codex-guard"),
)
MANIFEST_RELATIVE = Path(".aegis/foundation-manifest.json")
CURRENT_WORK_RELATIVE = Path(".aegis/state/current-work.json")
TASKS_RELATIVE = Path(".taskmaster/tasks/tasks.json")
ACTIVE_RELATIVE = Path("docs/ai/work-tracking/active")
ARCHIVE_RELATIVE = Path("docs/ai/work-tracking/archive")
DELIVERY_POLICY_RELATIVE = Path("aegis.delivery-policy.json")
PLANS_RELATIVE = Path("plans")
PLANS_CURRENT_RELATIVE = PLANS_RELATIVE / "current"
SESSIONS_RELATIVE = Path("sessions")
SESSIONS_CURRENT_RELATIVE = SESSIONS_RELATIVE / "current"
SOURCE_CLOSEOUT_JOURNAL_RELATIVE = Path(".plan_state/source-closeout-transaction.json")
SOURCE_CLOSEOUT_JOURNAL_SCHEMA = "aegis.source-closeout-transaction.v1"
SOURCE_CLOSEOUT_PHASES = (
    "prepared",
    "bundle_annotated",
    "archive_moved",
    "references_rewritten",
    "plan_synced",
)
LIFECYCLE_IDLE = "IDLE"
LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_CLOSEOUT_PENDING = "CLOSEOUT_PENDING"


class SourceWorkflowStateError(RuntimeError):
    """Raised when source-checkout evidence exists but is contradictory or incomplete."""


@dataclass(frozen=True)
class CompletedSourceWork:
    task_id: str
    task_title: str
    branch: str
    archive_folder: Path
    tracker_path: Path
    work_kind: str = "task"

    @property
    def work_id(self) -> str:
        """Return the lifecycle identity without imposing a legacy authority name."""

        return self.task_id

    @property
    def work_title(self) -> str:
        return self.task_title


@dataclass(frozen=True)
class SourceLifecycle:
    """Derived lifecycle for the uninstalled source checkout.

    Readiness remains an authorization decision.  Lifecycle only answers whether
    the checkout is between tasks, actively tracking one task, or must reconcile
    an interrupted closeout before either state can be trusted.
    """

    state: str
    work_kind: str | None = None
    work_id: str | None = None
    active_folder: Path | None = None
    completed_work: CompletedSourceWork | None = None
    transaction: dict[str, object] | None = None


@dataclass(frozen=True)
class ActiveSourceWork:
    """Validated authorities needed to recover ignored source-checkout runtime state."""

    work_kind: str
    work_id: str
    title: str
    slug: str
    branch: str
    active_folder: Path
    plan_path: Path
    session_path: Path


def task_id_from_branch(branch: str) -> str | None:
    match = re.search(r"(?:^|[-_/])task-?(\d+)(?:[-_/]|$)", branch)
    return match.group(1) if match else None


def bead_id_from_branch(branch: str) -> str | None:
    match = re.fullmatch(r"codex/([a-z][a-z0-9]*-[a-z0-9]+)(?:[-/].*)?", branch)
    return match.group(1) if match else None


def _task_token_pattern(task_id: str) -> re.Pattern[str]:
    return re.compile(rf"(?:^|[-_])task-?{re.escape(task_id)}(?:[-_]|$)", re.IGNORECASE)


def _bead_token_pattern(bead_id: str) -> re.Pattern[str]:
    return re.compile(rf"(?:^|[-_]){re.escape(bead_id)}(?:[-_]|$)", re.IGNORECASE)


def _tracker_references_task(text: str, task_id: str) -> bool:
    patterns = (
        rf"\bTaskmaster\s+Task\s+{re.escape(task_id)}\b",
        rf"\bTask\s+{re.escape(task_id)}\b",
        rf"\btask{re.escape(task_id)}\b",
        rf"\btask-{re.escape(task_id)}\b",
        rf"task_ids:\s*\[[^\]]*\b{re.escape(task_id)}\b[^\]]*\]",
    )
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _tracker_references_bead(text: str, bead_id: str) -> bool:
    return bool(re.search(rf"\b{re.escape(bead_id)}\b", text, flags=re.IGNORECASE))


def _taskmaster_tasks_payload(data: object) -> list[dict[str, object]] | None:
    if not isinstance(data, dict):
        return None
    master = data.get("master")
    if isinstance(master, dict) and isinstance(master.get("tasks"), list):
        return master["tasks"]  # type: ignore[return-value]
    if isinstance(data.get("tasks"), list):
        return data["tasks"]  # type: ignore[return-value]
    for value in data.values():
        if isinstance(value, dict) and isinstance(value.get("tasks"), list):
            return value["tasks"]  # type: ignore[return-value]
    return None


def _find_task(tasks: Iterable[dict[str, object]], task_id: str) -> dict[str, object] | None:
    for task in tasks:
        if str(task.get("id")) == task_id:
            return task
    return None


def _read_delivery_default_branch(root: Path) -> str | None:
    policy_path = root / DELIVERY_POLICY_RELATIVE
    if not policy_path.exists():
        return None
    if not policy_path.is_file() or policy_path.is_symlink():
        raise SourceWorkflowStateError("delivery policy must be a regular file")
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceWorkflowStateError(f"delivery policy is invalid JSON: {exc}") from exc
    if not isinstance(policy, dict):
        raise SourceWorkflowStateError("delivery policy must be a JSON object")
    evaluator_path = root / "scripts" / "aegis-delivery-policy"
    if not evaluator_path.is_file() or evaluator_path.is_symlink():
        raise SourceWorkflowStateError("trusted delivery-policy evaluator is missing")
    try:
        evaluator = runpy.run_path(evaluator_path.as_posix())
        validate_policy = evaluator["validate_policy"]
        policy = validate_policy(policy)
    except Exception as exc:  # noqa: BLE001 - normalize trusted evaluator failures.
        raise SourceWorkflowStateError(f"delivery policy is invalid: {exc}") from exc
    repository = policy.get("repository")
    if not isinstance(repository, dict):
        raise SourceWorkflowStateError("delivery policy repository block is missing")
    default_branch = repository.get("default_branch")
    if not isinstance(default_branch, str) or not re.fullmatch(r"[A-Za-z0-9._/-]+", default_branch):
        raise SourceWorkflowStateError("delivery policy default_branch is invalid")
    authority = policy.get("authority")
    if not isinstance(authority, dict) or authority.get("status") != "active":
        raise SourceWorkflowStateError("delivery policy authority is not active")
    return default_branch


def _resolve_contained_pointer(
    root: Path,
    *,
    pointer_relative: Path,
    container_relative: Path,
    label: str,
) -> Path:
    pointer = root / pointer_relative
    if not pointer.is_symlink():
        raise SourceWorkflowStateError(
            f"{label} pointer must be a symlink: {pointer_relative.as_posix()}"
        )
    try:
        resolved = pointer.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise SourceWorkflowStateError(f"{label} pointer is broken") from exc
    container = (root / container_relative).resolve()
    if not resolved.is_relative_to(container):
        raise SourceWorkflowStateError(
            f"{label} pointer resolves outside {container_relative.as_posix()}"
        )
    if not resolved.is_file() or resolved.is_symlink():
        raise SourceWorkflowStateError(f"{label} pointer target must be a regular file")
    return resolved


def _work_identity_from_current_pointers(root: Path) -> tuple[str, str]:
    plan = _resolve_contained_pointer(
        root,
        pointer_relative=PLANS_CURRENT_RELATIVE,
        container_relative=PLANS_RELATIVE,
        label="current plan",
    )
    plan_text = plan.read_text(encoding="utf-8")
    if not plan_text.startswith("---"):
        raise SourceWorkflowStateError("current plan is missing front matter")
    front_matter_parts = plan_text.split("---", 2)
    if len(front_matter_parts) < 3:
        raise SourceWorkflowStateError("current plan front matter is incomplete")
    task_ids_match = re.search(
        r"^task_ids:\s*\[([^\]]*)\]\s*$",
        front_matter_parts[1],
        flags=re.MULTILINE,
    )
    bead_ids_match = re.search(
        r"^bead_ids:\s*\[([^\]]*)\]\s*$",
        front_matter_parts[1],
        flags=re.MULTILINE,
    )
    if bool(task_ids_match) == bool(bead_ids_match):
        raise SourceWorkflowStateError(
            "current plan must declare exactly one task_ids or bead_ids entry"
        )
    if task_ids_match:
        task_items = [item.strip().strip("'\"") for item in task_ids_match.group(1).split(",")]
        if len(task_items) != 1 or not re.fullmatch(r"\d+", task_items[0]):
            raise SourceWorkflowStateError("current plan must declare exactly one numeric task ID")
        work_kind = "task"
        work_id = task_items[0]
    else:
        assert bead_ids_match is not None
        bead_items = [item.strip().strip("'\"") for item in bead_ids_match.group(1).split(",")]
        if len(bead_items) != 1 or not re.fullmatch(r"[a-z][a-z0-9]*-[a-z0-9]+", bead_items[0]):
            raise SourceWorkflowStateError("current plan must declare exactly one valid bead ID")
        work_kind = "bead"
        work_id = bead_items[0]

    session = _resolve_contained_pointer(
        root,
        pointer_relative=SESSIONS_CURRENT_RELATIVE,
        container_relative=SESSIONS_RELATIVE,
        label="current session",
    )
    session_relative = session.relative_to((root / SESSIONS_RELATIVE).resolve()).as_posix()
    session_text = session.read_text(encoding="utf-8")
    token = _task_token_pattern(work_id) if work_kind == "task" else _bead_token_pattern(work_id)
    label = "Task" if work_kind == "task" else "Bead"
    references = _tracker_references_task if work_kind == "task" else _tracker_references_bead
    if not token.search(session_relative):
        raise SourceWorkflowStateError(f"current session path does not reference {label} {work_id}")
    if not references(session_text, work_id):
        raise SourceWorkflowStateError(
            f"current session content does not reference {label} {work_id}"
        )
    return work_kind, work_id


def _source_work_identity(root: Path, branch: str) -> tuple[str, str] | None:
    task_id = task_id_from_branch(branch)
    if task_id:
        return "task", task_id
    bead_id = bead_id_from_branch(branch)
    if bead_id:
        return "bead", bead_id
    default_branch = _read_delivery_default_branch(root)
    if default_branch is None or branch != default_branch:
        return None
    return _work_identity_from_current_pointers(root)


def _validate_relative_journal_path(root: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SourceWorkflowStateError(f"closeout journal {label} path is invalid")
    relative = Path(value)
    if relative.is_absolute() or relative.as_posix() != value or ".." in relative.parts:
        raise SourceWorkflowStateError(f"closeout journal {label} path is not contained")
    candidate = (root / relative).resolve(strict=False)
    if not candidate.is_relative_to(root.resolve()):
        raise SourceWorkflowStateError(f"closeout journal {label} path escapes the checkout")
    return candidate


def read_source_closeout_transaction(root: Path) -> dict[str, object] | None:
    """Read and validate the write-ahead closeout journal without mutating it."""

    root = root.resolve()
    journal_path = root / SOURCE_CLOSEOUT_JOURNAL_RELATIVE
    if not journal_path.exists():
        return None
    if not journal_path.is_file() or journal_path.is_symlink():
        raise SourceWorkflowStateError("source closeout journal must be a regular file")
    try:
        payload = json.loads(journal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceWorkflowStateError(f"source closeout journal is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != SOURCE_CLOSEOUT_JOURNAL_SCHEMA:
        raise SourceWorkflowStateError("source closeout journal schema is invalid")
    transaction_id = payload.get("transaction_id")
    if not isinstance(transaction_id, str) or not re.fullmatch(r"[0-9a-f]{64}", transaction_id):
        raise SourceWorkflowStateError("source closeout transaction_id is invalid")
    if payload.get("phase") not in SOURCE_CLOSEOUT_PHASES:
        raise SourceWorkflowStateError("source closeout journal phase is invalid")
    work = payload.get("work")
    if not isinstance(work, dict) or work.get("kind") not in {"task", "bead"}:
        raise SourceWorkflowStateError("source closeout journal work identity is invalid")
    work_id = work.get("id")
    work_pattern = r"\d+" if work.get("kind") == "task" else r"[a-z][a-z0-9]*-[a-z0-9-]+"
    if not isinstance(work_id, str) or not re.fullmatch(work_pattern, work_id):
        raise SourceWorkflowStateError("source closeout journal work ID is invalid")
    paths = payload.get("paths")
    if not isinstance(paths, dict) or set(paths) != {"active", "archive", "plan", "session"}:
        raise SourceWorkflowStateError("source closeout journal paths are invalid")
    for label in ("active", "archive", "plan", "session"):
        _validate_relative_journal_path(root, paths[label], label)
    timestamps = payload.get("timestamps")
    required_timestamps = {"created_at", "date", "display", "tracker"}
    if not isinstance(timestamps, dict) or set(timestamps) != required_timestamps:
        raise SourceWorkflowStateError("source closeout journal timestamps are invalid")
    if not all(isinstance(timestamps[key], str) and timestamps[key] for key in required_timestamps):
        raise SourceWorkflowStateError("source closeout journal timestamp value is invalid")
    return payload


def is_uninstalled_aegis_source_checkout(root: Path) -> bool:
    root = root.resolve()
    if (root / MANIFEST_RELATIVE).exists():
        return False
    if not all((root / marker).is_file() for marker in SOURCE_MARKERS):
        return False
    try:
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, tomllib.TOMLDecodeError):
        return False
    project_table = project.get("project") if isinstance(project, dict) else None
    return isinstance(project_table, dict) and project_table.get("name") == "aegis-foundation"


def derive_completed_source_work(
    root: Path,
    branch: str,
    *,
    _identity: tuple[str, str] | None = None,
) -> CompletedSourceWork | None:
    """Return completed source work when every independent authority agrees.

    ``None`` means the source-only fallback is not applicable. Once a checkout is
    positively identified as the uninstalled Aegis source and has no active envelope,
    contradictory evidence raises ``SourceWorkflowStateError`` instead of guessing.
    """

    root = root.resolve()
    if not is_uninstalled_aegis_source_checkout(root):
        return None
    if (root / CURRENT_WORK_RELATIVE).exists():
        return None
    if read_source_closeout_transaction(root) is not None:
        raise SourceWorkflowStateError(
            "source lifecycle is CLOSEOUT_PENDING; run work-tracking reconcile"
        )

    active_root = root / ACTIVE_RELATIVE
    active_folders = (
        sorted(
            path
            for path in active_root.iterdir()
            if path.is_dir() and path.name.endswith("-ACTIVE")
        )
        if active_root.is_dir()
        else []
    )
    if active_folders:
        return None

    identity = _identity if _identity is not None else _source_work_identity(root, branch)
    if identity is None:
        return None
    work_kind, work_id = identity

    if work_kind == "task":
        tasks_path = root / TASKS_RELATIVE
        try:
            payload = json.loads(tasks_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SourceWorkflowStateError("Taskmaster tasks file is missing") from exc
        except json.JSONDecodeError as exc:
            raise SourceWorkflowStateError(f"Taskmaster tasks file is invalid: {exc}") from exc

        tasks = _taskmaster_tasks_payload(payload)
        if tasks is None:
            raise SourceWorkflowStateError("Taskmaster tasks file has an unsupported shape")
        task = _find_task(tasks, work_id)
        if task is None:
            raise SourceWorkflowStateError(f"Taskmaster Task {work_id} is missing")
        if task.get("status") != "done":
            raise SourceWorkflowStateError(
                f"Taskmaster Task {work_id} status is {task.get('status')!r}, expected 'done'"
            )
        work_title = str(task.get("title") or "")
        token = _task_token_pattern(work_id)
        references = _tracker_references_task
        label = "Task"
    else:
        work_title = f"Bead {work_id}"
        token = _bead_token_pattern(work_id)
        references = _tracker_references_bead
        label = "Bead"

    archive_root = root / ARCHIVE_RELATIVE
    if not archive_root.is_dir():
        raise SourceWorkflowStateError(f"archive root is missing: {ARCHIVE_RELATIVE.as_posix()}")
    candidates = sorted(
        path
        for path in archive_root.iterdir()
        if path.name.endswith("-COMPLETED")
        and token.search(path.name)
        and (path.is_dir() or path.is_symlink())
    )
    if len(candidates) != 1:
        names = ", ".join(path.name for path in candidates) or "none"
        raise SourceWorkflowStateError(
            f"expected exactly one completed archive for {label} {work_id}, "
            f"found {len(candidates)} ({names})"
        )

    candidate = candidates[0]
    if candidate.is_symlink():
        raise SourceWorkflowStateError(f"completed archive must not be a symlink: {candidate.name}")
    archive_resolved = archive_root.resolve()
    completed_folder = candidate.resolve()
    if not completed_folder.is_relative_to(archive_resolved):
        raise SourceWorkflowStateError("completed archive resolves outside the archive root")

    tracker_path = completed_folder / "TRACKER.md"
    if not tracker_path.is_file() or tracker_path.is_symlink():
        raise SourceWorkflowStateError(
            f"completed tracker is missing or not a regular file: {tracker_path}"
        )
    tracker_resolved = tracker_path.resolve()
    if not tracker_resolved.is_relative_to(completed_folder):
        raise SourceWorkflowStateError("completed tracker resolves outside its archive folder")
    tracker_text = tracker_path.read_text(encoding="utf-8")
    if not references(tracker_text, work_id):
        raise SourceWorkflowStateError(f"completed tracker does not reference {label} {work_id}")
    if not re.search(r"^\*\*Status\*\*:\s*COMPLETED\s*$", tracker_text, flags=re.MULTILINE):
        raise SourceWorkflowStateError("completed tracker status is not COMPLETED")

    return CompletedSourceWork(
        task_id=work_id,
        task_title=work_title,
        branch=branch,
        archive_folder=completed_folder,
        tracker_path=tracker_resolved,
        work_kind=work_kind,
    )


def derive_source_lifecycle(
    root: Path,
    branch: str,
    *,
    _ignore_current_work: bool = False,
) -> SourceLifecycle:
    """Derive IDLE, ACTIVE, or CLOSEOUT_PENDING for an Aegis source checkout."""

    root = root.resolve()
    if not is_uninstalled_aegis_source_checkout(root):
        raise SourceWorkflowStateError(
            "source lifecycle is only defined for an uninstalled source checkout"
        )
    if (root / CURRENT_WORK_RELATIVE).exists() and not _ignore_current_work:
        raise SourceWorkflowStateError("installed current-work state overrides source lifecycle")

    transaction = read_source_closeout_transaction(root)
    if transaction is not None:
        work = transaction["work"]
        assert isinstance(work, dict)
        paths = transaction["paths"]
        assert isinstance(paths, dict)
        return SourceLifecycle(
            state=LIFECYCLE_CLOSEOUT_PENDING,
            work_kind=str(work["kind"]),
            work_id=str(work["id"]),
            active_folder=_validate_relative_journal_path(root, paths["active"], "active"),
            transaction=transaction,
        )

    active_root = root / ACTIVE_RELATIVE
    active_folders = (
        sorted(
            path.resolve()
            for path in active_root.iterdir()
            if path.is_dir() and not path.is_symlink() and path.name.endswith("-ACTIVE")
        )
        if active_root.is_dir()
        else []
    )
    if len(active_folders) > 1:
        names = ", ".join(path.name for path in active_folders)
        raise SourceWorkflowStateError(f"expected at most one ACTIVE folder, found {names}")
    if active_folders:
        branch_identity = _source_work_identity(root, branch)
        pointer_identity = _work_identity_from_current_pointers(root)
        identity = branch_identity or pointer_identity
        if branch_identity is not None and branch_identity != pointer_identity:
            raise SourceWorkflowStateError(
                "active branch identity disagrees with current plan/session identity"
            )
        if identity is None:
            raise SourceWorkflowStateError("ACTIVE source work has no authoritative identity")
        work_kind, work_id = identity
        active = active_folders[0]
        token = (
            _task_token_pattern(work_id) if work_kind == "task" else _bead_token_pattern(work_id)
        )
        if not token.search(active.name):
            raise SourceWorkflowStateError(
                f"ACTIVE folder {active.name!r} does not match {work_kind} {work_id}"
            )
        tracker = active / "TRACKER.md"
        if not tracker.is_file() or tracker.is_symlink():
            raise SourceWorkflowStateError("ACTIVE tracker is missing or not a regular file")
        tracker_text = tracker.read_text(encoding="utf-8")
        references = _tracker_references_task if work_kind == "task" else _tracker_references_bead
        if not references(tracker_text, work_id):
            raise SourceWorkflowStateError(
                f"ACTIVE tracker does not reference {work_kind} {work_id}"
            )
        if not re.search(r"^\*\*Status\*\*:\s*ACTIVE\s*$", tracker_text, flags=re.MULTILINE):
            raise SourceWorkflowStateError("ACTIVE tracker status is not ACTIVE")
        return SourceLifecycle(
            state=LIFECYCLE_ACTIVE,
            work_kind=work_kind,
            work_id=work_id,
            active_folder=active,
        )

    plan_pointer = root / PLANS_CURRENT_RELATIVE
    session_pointer = root / SESSIONS_CURRENT_RELATIVE
    if (
        not plan_pointer.exists()
        and not plan_pointer.is_symlink()
        and not session_pointer.exists()
        and not session_pointer.is_symlink()
    ):
        return SourceLifecycle(state=LIFECYCLE_IDLE)
    pointer_identity = _work_identity_from_current_pointers(root)
    completed = derive_completed_source_work(root, branch, _identity=pointer_identity)
    if completed is None:
        raise SourceWorkflowStateError("IDLE source pointers do not resolve to completed work")
    return SourceLifecycle(
        state=LIFECYCLE_IDLE,
        work_kind=pointer_identity[0],
        work_id=pointer_identity[1],
        completed_work=completed,
    )


def derive_active_source_work(root: Path, branch: str) -> ActiveSourceWork:
    """Derive recovery inputs only when every tracked ACTIVE authority agrees."""

    root = root.resolve()
    lifecycle = derive_source_lifecycle(root, branch, _ignore_current_work=True)
    if lifecycle.state != LIFECYCLE_ACTIVE:
        raise SourceWorkflowStateError(
            f"source current-work recovery requires ACTIVE lifecycle, found {lifecycle.state}"
        )
    if lifecycle.active_folder is None or lifecycle.work_kind is None or lifecycle.work_id is None:
        raise SourceWorkflowStateError("ACTIVE source lifecycle is missing validated work identity")

    plan_path = _resolve_contained_pointer(
        root,
        pointer_relative=PLANS_CURRENT_RELATIVE,
        container_relative=PLANS_RELATIVE,
        label="current plan",
    )
    session_path = _resolve_contained_pointer(
        root,
        pointer_relative=SESSIONS_CURRENT_RELATIVE,
        container_relative=SESSIONS_RELATIVE,
        label="current session",
    )
    plan_text = plan_path.read_text(encoding="utf-8")
    if not plan_text.startswith("---"):
        raise SourceWorkflowStateError("current plan is missing front matter")
    front_matter_parts = plan_text.split("---", 2)
    if len(front_matter_parts) < 3:
        raise SourceWorkflowStateError("current plan front matter is incomplete")
    front_matter = front_matter_parts[1]

    work_context_match = re.search(
        r"^work_context:\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$",
        front_matter,
        flags=re.MULTILINE,
    )
    if work_context_match is None:
        raise SourceWorkflowStateError("current plan work_context is missing or invalid")
    work_context = work_context_match.group(1)
    context_prefix = (
        f"{lifecycle.work_id}-" if lifecycle.work_kind == "bead" else f"task{lifecycle.work_id}-"
    )
    if not work_context.startswith(context_prefix):
        raise SourceWorkflowStateError(
            f"current plan work_context does not match {lifecycle.work_kind} {lifecycle.work_id}"
        )
    slug = work_context[len(context_prefix) :]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise SourceWorkflowStateError("current plan work_context has an invalid work slug")

    if lifecycle.work_kind == "bead":
        branch_policy_match = re.search(
            r"^branch_policy:\s*([^\s#]+)\s*$",
            front_matter,
            flags=re.MULTILINE,
        )
        if branch_policy_match is None or branch_policy_match.group(1) != branch:
            raise SourceWorkflowStateError(
                "current plan branch_policy does not match the current bead branch"
            )

    work_label = "Bead" if lifecycle.work_kind == "bead" else "Task"
    title_prefix = f"# Plan - {work_label} {lifecycle.work_id}"
    title = ""
    for line in front_matter_parts[2].splitlines():
        if line.startswith(title_prefix):
            title = line[len(title_prefix) :].strip().lstrip("-—:").strip()
            break
    if not title:
        raise SourceWorkflowStateError("current plan title is missing or invalid")

    return ActiveSourceWork(
        work_kind=lifecycle.work_kind,
        work_id=lifecycle.work_id,
        title=title,
        slug=slug,
        branch=branch,
        active_folder=lifecycle.active_folder,
        plan_path=plan_path,
        session_path=session_path,
    )


def _active_source_current_work_payload(
    root: Path,
    active: ActiveSourceWork,
    *,
    schema_version: str,
    recovered_at: str,
) -> dict[str, object]:
    root = root.resolve()
    active_rel = active.active_folder.relative_to(root).as_posix()
    plan_rel = active.plan_path.relative_to(root).as_posix()
    session_rel = active.session_path.relative_to(root).as_posix()
    reports_rel = f"{active_rel}/reports/{active.slug}"
    task: dict[str, object] = {
        "id": active.work_id,
        "slug": active.slug,
        "title": active.title,
        "status": "in-progress",
    }
    if active.work_kind == "bead":
        task["source"] = "gas-city-bead"
    core: dict[str, object] = {
        "schema_version": schema_version,
        "mode": active.work_kind,
        "status": "in-progress",
        "task": task,
        "branch": {
            "before": active.branch,
            "current": active.branch,
            "action": "recovered_source_checkout",
            "created": False,
        },
        "paths": {
            "session": session_rel,
            "session_current": SESSIONS_CURRENT_RELATIVE.as_posix(),
            "plan": plan_rel,
            "plan_current": PLANS_CURRENT_RELATIVE.as_posix(),
            "work_tracking": active_rel,
            "reports": reports_rel,
            "workflow_templates": ".aegis/templates/workflow",
        },
        "integrations": {
            "taskmaster": {
                "required": False,
                "detected": (root / ".taskmaster").exists(),
                **({"mutation_allowed": False} if active.work_kind == "bead" else {}),
            },
            "serena": {
                "required": False,
                "detected": (root / ".serena").exists(),
            },
        },
    }
    if active.work_kind == "bead":
        core["authority"] = {
            "kind": "gas-city-bead",
            "id": active.work_id,
            "mutable": True,
        }
    fingerprint = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        **core,
        "created_at": recovered_at,
        "updated_at": recovered_at,
        "recovery": {
            "kind": "tracked-source-lifecycle",
            "fingerprint": fingerprint,
            "recovered_at": recovered_at,
        },
    }


def recover_source_current_work(
    root: Path,
    branch: str,
    *,
    schema_version: str,
) -> dict[str, object]:
    """Atomically recover ignored runtime state from aligned tracked authorities.

    This is intentionally a mutation helper for explicit workflow commands such as
    ``aegis log``. Readiness continues to derive source lifecycle without writing.
    """

    root = root.resolve()
    active = derive_active_source_work(root, branch)
    current_path = root / CURRENT_WORK_RELATIVE
    existing: object | None = None
    if current_path.exists() or current_path.is_symlink():
        if not current_path.is_file() or current_path.is_symlink():
            raise SourceWorkflowStateError("source current-work state must be a regular file")
        try:
            existing = json.loads(current_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SourceWorkflowStateError(
                f"source current-work state is invalid JSON: {exc}"
            ) from exc

    recovered_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    expected = _active_source_current_work_payload(
        root,
        active,
        schema_version=schema_version,
        recovered_at=recovered_at,
    )
    if existing is not None:
        if not isinstance(existing, dict):
            raise SourceWorkflowStateError("source current-work state must be a JSON object")
        expected_core = {
            key: value
            for key, value in expected.items()
            if key not in {"created_at", "updated_at", "recovery"}
        }
        existing_core = {
            key: value
            for key, value in existing.items()
            if key not in {"created_at", "updated_at", "recovery"}
        }
        if existing_core != expected_core:
            raise SourceWorkflowStateError(
                "source current-work state contradicts the tracked ACTIVE authorities"
            )
        expected_recovery = expected["recovery"]
        existing_recovery = existing.get("recovery")
        if not isinstance(expected_recovery, dict) or not isinstance(existing_recovery, dict):
            raise SourceWorkflowStateError("source current-work recovery metadata is missing")
        if existing_recovery.get("fingerprint") != expected_recovery.get("fingerprint"):
            raise SourceWorkflowStateError(
                "source current-work state contradicts the tracked ACTIVE authorities"
            )
        return existing

    cursor = root
    for part in CURRENT_WORK_RELATIVE.parent.parts:
        cursor /= part
        if cursor.exists() and cursor.is_symlink():
            raise SourceWorkflowStateError("source current-work state directory contains a symlink")
    state_dir = current_path.parent
    state_dir.mkdir(parents=True, exist_ok=True)
    if state_dir.is_symlink() or not state_dir.resolve().is_relative_to(root):
        raise SourceWorkflowStateError("source current-work state directory is not contained")
    encoded = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = state_dir / f".{current_path.name}.{os.getpid()}.tmp"
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, current_path)
    finally:
        temporary.unlink(missing_ok=True)
    written = json.loads(current_path.read_text(encoding="utf-8"))
    if written != expected:
        raise SourceWorkflowStateError("source current-work atomic write readback mismatch")
    return expected
