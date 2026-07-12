"""Fail-closed derivation of completed work for the Aegis source checkout."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
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


class SourceWorkflowStateError(RuntimeError):
    """Raised when source-checkout evidence exists but is contradictory or incomplete."""


@dataclass(frozen=True)
class CompletedSourceWork:
    task_id: str
    task_title: str
    branch: str
    archive_folder: Path
    tracker_path: Path


def task_id_from_branch(branch: str) -> str | None:
    match = re.search(r"(?:^|[-_/])task-?(\d+)(?:[-_/]|$)", branch)
    return match.group(1) if match else None


def _task_token_pattern(task_id: str) -> re.Pattern[str]:
    return re.compile(rf"(?:^|[-_])task-?{re.escape(task_id)}(?:[-_]|$)", re.IGNORECASE)


def _tracker_references_task(text: str, task_id: str) -> bool:
    patterns = (
        rf"\bTaskmaster\s+Task\s+{re.escape(task_id)}\b",
        rf"\bTask\s+{re.escape(task_id)}\b",
        rf"\btask{re.escape(task_id)}\b",
        rf"\btask-{re.escape(task_id)}\b",
        rf"task_ids:\s*\[[^\]]*\b{re.escape(task_id)}\b[^\]]*\]",
    )
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


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


def derive_completed_source_work(root: Path, branch: str) -> CompletedSourceWork | None:
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

    active_root = root / ACTIVE_RELATIVE
    active_folders = (
        sorted(path for path in active_root.iterdir() if path.is_dir() and path.name.endswith("-ACTIVE"))
        if active_root.is_dir()
        else []
    )
    if active_folders:
        return None

    task_id = task_id_from_branch(branch)
    if not task_id:
        return None

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
    task = _find_task(tasks, task_id)
    if task is None:
        raise SourceWorkflowStateError(f"Taskmaster Task {task_id} is missing")
    if task.get("status") != "done":
        raise SourceWorkflowStateError(
            f"Taskmaster Task {task_id} status is {task.get('status')!r}, expected 'done'"
        )

    archive_root = root / ARCHIVE_RELATIVE
    if not archive_root.is_dir():
        raise SourceWorkflowStateError(f"archive root is missing: {ARCHIVE_RELATIVE.as_posix()}")
    token = _task_token_pattern(task_id)
    candidates = sorted(
        path
        for path in archive_root.iterdir()
        if path.name.endswith("-COMPLETED") and token.search(path.name) and (path.is_dir() or path.is_symlink())
    )
    if len(candidates) != 1:
        names = ", ".join(path.name for path in candidates) or "none"
        raise SourceWorkflowStateError(
            f"expected exactly one completed archive for Task {task_id}, found {len(candidates)} ({names})"
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
        raise SourceWorkflowStateError(f"completed tracker is missing or not a regular file: {tracker_path}")
    tracker_resolved = tracker_path.resolve()
    if not tracker_resolved.is_relative_to(completed_folder):
        raise SourceWorkflowStateError("completed tracker resolves outside its archive folder")
    tracker_text = tracker_path.read_text(encoding="utf-8")
    if not _tracker_references_task(tracker_text, task_id):
        raise SourceWorkflowStateError(f"completed tracker does not reference Task {task_id}")
    if not re.search(r"^\*\*Status\*\*:\s*COMPLETED\s*$", tracker_text, flags=re.MULTILINE):
        raise SourceWorkflowStateError("completed tracker status is not COMPLETED")

    return CompletedSourceWork(
        task_id=task_id,
        task_title=str(task.get("title") or ""),
        branch=branch,
        archive_folder=completed_folder,
        tracker_path=tracker_resolved,
    )
