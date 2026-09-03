"""Historical terminal spellings must not reactivate archived plan scopes."""

from types import SimpleNamespace

import pytest

from tests.meta_workflow_guard.test_guard_rules import load_guard_module


@pytest.mark.parametrize("status", ["complete", "completed", "done"])
def test_terminal_spelling_preserves_history_without_conflict(tmp_path, monkeypatch, status):
    guard = load_guard_module()
    monkeypatch.setattr(guard, "REPO_ROOT", tmp_path)
    current = tmp_path / "current.md"
    old = tmp_path / "old.md"
    original = (
        "## Scope\n- scripts/codex-guard\n\n"
        f"| plan-step-verify | verify | evidence | {status} |\n"
        "| plan-step-emergency | unused | evidence | n/a |\n"
    ).encode()
    old.write_bytes(original)
    assert (
        guard.validate_plan_conflicts(current, SimpleNamespace(scope=["scripts/codex-guard"])) == []
    )
    assert old.read_bytes() == original


@pytest.mark.parametrize("status", ["in-progress", "pending", "unknown", ""])
def test_active_or_unknown_overlap_remains_blocked(tmp_path, monkeypatch, status):
    guard = load_guard_module()
    monkeypatch.setattr(guard, "REPO_ROOT", tmp_path)
    (tmp_path / "active.md").write_text(
        "## Scope\n- scripts/codex-guard\n\n"
        f"| plan-step-verify | verify | evidence | {status} |\n"
    )
    issues = guard.validate_plan_conflicts(
        tmp_path / "current.md", SimpleNamespace(scope=["scripts/codex-guard"])
    )
    assert len(issues) == 1
    assert "Active plan overlaps" in issues[0].message
