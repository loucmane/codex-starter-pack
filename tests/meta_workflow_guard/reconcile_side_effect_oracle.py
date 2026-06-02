"""Filesystem side-effect oracle for Aegis reconcile tests."""

from __future__ import annotations

import fnmatch
import hashlib
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_WHOLE_TREE_IGNORE_PATTERNS = (
    ".git/FETCH_HEAD",
    ".git/logs",
    ".git/logs/**",
)
CONTROL_PLANE_REL_PATHS = (
    ".aegis",
    ".taskmaster",
    "docs/ai/work-tracking",
    "sessions",
    "plans",
    ".git/HEAD",
    ".git/refs",
    ".git/packed-refs",
)


@dataclass(frozen=True)
class SnapshotEntry:
    kind: str
    mode: int | None = None
    digest: str | None = None
    symlink_target: str | None = None


@dataclass(frozen=True)
class SnapshotDelta:
    path: str
    before: SnapshotEntry | None
    after: SnapshotEntry | None


@dataclass(frozen=True)
class FileSystemSnapshot:
    root: Path
    entries: dict[str, SnapshotEntry]

    def diff(self, other: "FileSystemSnapshot") -> list[SnapshotDelta]:
        paths = sorted(set(self.entries) | set(other.entries))
        return [
            SnapshotDelta(path, self.entries.get(path), other.entries.get(path))
            for path in paths
            if self.entries.get(path) != other.entries.get(path)
        ]

    def assert_matches(self, other: "FileSystemSnapshot", *, allowed_deltas: Iterable[str] = ()) -> None:
        allowed = {_normalize_rel_path(path) for path in allowed_deltas}
        unexpected = [delta for delta in self.diff(other) if delta.path not in allowed]
        if unexpected:
            details = "\n".join(
                f"{delta.path}: {delta.before!r} -> {delta.after!r}" for delta in unexpected
            )
            raise AssertionError(f"unexpected filesystem deltas:\n{details}")


def snapshot_whole_tree(
    root: Path,
    *,
    ignore_patterns: Iterable[str] = DEFAULT_WHOLE_TREE_IGNORE_PATTERNS,
    require_tmp_root: bool = True,
) -> FileSystemSnapshot:
    """Snapshot an isolated fixture tree.

    Whole-tree mode is intentionally guarded to pytest/tmp fixtures so noisy real repos do not
    produce false positives from build tooling, editor state, or unrelated test runner writes.
    """

    root = root.resolve()
    if require_tmp_root and not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise ValueError(f"whole-tree side-effect snapshots must use isolated temp roots: {root}")
    ignored = tuple(_normalize_rel_path(pattern) for pattern in ignore_patterns)
    entries = {
        rel_path: _entry_for(path)
        for rel_path, path in _iter_existing_paths(root)
        if not _matches_any(rel_path, ignored)
    }
    return FileSystemSnapshot(root=root, entries=entries)


def snapshot_control_plane(root: Path) -> FileSystemSnapshot:
    """Snapshot known mutation-sensitive workflow/control-plane surfaces."""

    root = root.resolve()
    entries: dict[str, SnapshotEntry] = {}
    for rel_path in CONTROL_PLANE_REL_PATHS:
        rel_path = _normalize_rel_path(rel_path)
        path = root / rel_path
        if path.exists() or path.is_symlink():
            if path.is_dir() and not path.is_symlink():
                for child_rel_path, child in _iter_existing_paths(root, start=path):
                    entries[child_rel_path] = _entry_for(child)
            else:
                entries[rel_path] = _entry_for(path)
        else:
            entries[rel_path] = SnapshotEntry(kind="missing")
    return FileSystemSnapshot(root=root, entries=dict(sorted(entries.items())))


def assert_no_side_effects(
    before: FileSystemSnapshot,
    root: Path,
    *,
    allowed_deltas: Iterable[str] = (),
    whole_tree: bool = True,
) -> None:
    after = snapshot_whole_tree(root) if whole_tree else snapshot_control_plane(root)
    before.assert_matches(after, allowed_deltas=allowed_deltas)


def _iter_existing_paths(root: Path, *, start: Path | None = None) -> list[tuple[str, Path]]:
    start = start or root
    paths = [start] + sorted(start.rglob("*"), key=lambda path: path.as_posix())
    result: list[tuple[str, Path]] = []
    for path in paths:
        if path == root:
            continue
        rel_path = _normalize_rel_path(path.relative_to(root).as_posix())
        result.append((rel_path, path))
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
        return SnapshotEntry(kind="file", mode=mode, digest=hashlib.sha256(path.read_bytes()).hexdigest())
    return SnapshotEntry(kind="other", mode=mode)


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(path == pattern or fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _normalize_rel_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")
