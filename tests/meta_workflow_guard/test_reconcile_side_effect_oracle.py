"""Tests for the Aegis reconcile side-effect snapshot oracle."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.meta_workflow_guard.reconcile_side_effect_oracle import (
    snapshot_control_plane,
    snapshot_whole_tree,
)


def assert_delta_detected(before, root: Path) -> None:
    with pytest.raises(AssertionError, match="unexpected filesystem deltas"):
        before.assert_matches(snapshot_whole_tree(root))


def test_whole_tree_snapshot_detects_content_edit(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    path = target / "state.json"
    path.write_text("{}\n", encoding="utf-8")
    before = snapshot_whole_tree(target)

    path.write_text('{"mutated": true}\n', encoding="utf-8")

    assert_delta_detected(before, target)


def test_whole_tree_snapshot_detects_file_creation_and_deletion(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    before_create = snapshot_whole_tree(target)

    path = target / "created.txt"
    path.write_text("created\n", encoding="utf-8")

    assert_delta_detected(before_create, target)
    before_delete = snapshot_whole_tree(target)

    path.unlink()

    assert_delta_detected(before_delete, target)


def test_whole_tree_snapshot_detects_mode_change(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    path = target / "script.sh"
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o600)
    before = snapshot_whole_tree(target)

    path.chmod(0o755)

    assert_delta_detected(before, target)


def test_whole_tree_snapshot_detects_symlink_target_change(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    (target / "a.txt").write_text("a\n", encoding="utf-8")
    (target / "b.txt").write_text("b\n", encoding="utf-8")
    link = target / "current"
    link.symlink_to("a.txt")
    before = snapshot_whole_tree(target)

    link.unlink()
    link.symlink_to("b.txt")

    assert_delta_detected(before, target)


@pytest.mark.parametrize(
    ("before_kind", "after_kind"),
    [
        ("file", "directory"),
        ("directory", "file"),
        ("file", "symlink"),
        ("symlink", "file"),
    ],
)
def test_whole_tree_snapshot_detects_type_swaps(tmp_path: Path, before_kind: str, after_kind: str) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    path = target / "swap"
    _create_kind(path, before_kind)
    before = snapshot_whole_tree(target)

    _remove_kind(path, before_kind)
    _create_kind(path, after_kind)

    assert_delta_detected(before, target)


def test_whole_tree_snapshot_allows_only_exact_declared_delta(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    report_dir = target / ".aegis" / "reports"
    report_dir.mkdir(parents=True)
    before = snapshot_whole_tree(target)

    (report_dir / "reconcile.json").write_text("{}\n", encoding="utf-8")

    before.assert_matches(snapshot_whole_tree(target), allowed_deltas=[".aegis/reports/reconcile.json"])
    before_with_report = snapshot_whole_tree(target)

    (report_dir / "other.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(AssertionError, match=".aegis/reports/other.json"):
        before_with_report.assert_matches(
            snapshot_whole_tree(target),
            allowed_deltas=[".aegis/reports/reconcile.json"],
        )


def test_whole_tree_snapshot_tolerates_only_declared_git_discovery_churn(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    (target / ".git" / "refs" / "heads").mkdir(parents=True)
    (target / ".git" / "logs").mkdir(parents=True)
    (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (target / ".git" / "refs" / "heads" / "main").write_text("0" * 40 + "\n", encoding="utf-8")
    (target / ".git" / "packed-refs").write_text("# pack-refs\n", encoding="utf-8")
    before = snapshot_whole_tree(target)

    (target / ".git" / "FETCH_HEAD").write_text("fetch metadata\n", encoding="utf-8")
    (target / ".git" / "logs" / "HEAD").write_text("log metadata\n", encoding="utf-8")

    before.assert_matches(snapshot_whole_tree(target))
    before_refs = snapshot_whole_tree(target)

    (target / ".git" / "HEAD").write_text("ref: refs/heads/other\n", encoding="utf-8")
    with pytest.raises(AssertionError, match=".git/HEAD"):
        before_refs.assert_matches(snapshot_whole_tree(target))
    (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    before_refs = snapshot_whole_tree(target)

    (target / ".git" / "refs" / "heads" / "main").write_text("1" * 40 + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match=".git/refs/heads/main"):
        before_refs.assert_matches(snapshot_whole_tree(target))
    (target / ".git" / "refs" / "heads" / "main").write_text("0" * 40 + "\n", encoding="utf-8")
    before_refs = snapshot_whole_tree(target)

    (target / ".git" / "packed-refs").write_text("1" * 40 + " refs/heads/main\n", encoding="utf-8")
    with pytest.raises(AssertionError, match=".git/packed-refs"):
        before_refs.assert_matches(snapshot_whole_tree(target))


def test_whole_tree_snapshot_is_guarded_to_temp_roots(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="isolated temp roots"):
        snapshot_whole_tree(Path("/"))


def test_focused_control_plane_snapshot_detects_missing_path_creation(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    target.mkdir()
    before = snapshot_control_plane(target)

    (target / ".taskmaster").mkdir()
    (target / ".taskmaster" / "state.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(AssertionError, match=".taskmaster"):
        before.assert_matches(snapshot_control_plane(target))


def test_focused_control_plane_snapshot_detects_git_ref_mutation(tmp_path: Path) -> None:
    target = tmp_path / "fixture"
    (target / ".git" / "refs" / "heads").mkdir(parents=True)
    (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (target / ".git" / "refs" / "heads" / "main").write_text("0" * 40 + "\n", encoding="utf-8")
    before = snapshot_control_plane(target)

    (target / ".git" / "refs" / "heads" / "main").write_text("1" * 40 + "\n", encoding="utf-8")

    with pytest.raises(AssertionError, match=".git/refs/heads/main"):
        before.assert_matches(snapshot_control_plane(target))


def _create_kind(path: Path, kind: str) -> None:
    if kind == "file":
        path.write_text("file\n", encoding="utf-8")
    elif kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        path.symlink_to("target.txt")
    else:  # pragma: no cover - protects parametrized test maintenance.
        raise AssertionError(f"unknown path kind: {kind}")


def _remove_kind(path: Path, kind: str) -> None:
    if kind in {"file", "symlink"}:
        path.unlink()
    elif kind == "directory":
        path.rmdir()
    else:  # pragma: no cover - protects parametrized test maintenance.
        raise AssertionError(f"unknown path kind: {kind}")
