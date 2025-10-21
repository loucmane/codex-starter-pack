"""Unit tests for codex-guard timestamp enforcement helpers."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path


def load_guard_module():
    name = 'codex_guard_test_module'
    if name in sys.modules:
        del sys.modules[name]
    path = Path('scripts/codex-guard')
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def test_validate_session_edit_dates_flags_legacy_session() -> None:
    module = load_guard_module()
    legacy_session = module.REPO_ROOT / 'sessions' / '1999' / '01' / '1999-01-01-legacy.md'
    changed = [legacy_session]
    issues = module.validate_session_edit_dates(changed)
    assert any('1999-01-01-legacy.md' in issue.render() for issue in issues)


def test_validate_active_folder_edits_flags_mismatched_prefix() -> None:
    module = load_guard_module()
    legacy_tracker = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'active' / '19990101-legacy-task-ACTIVE' / 'TRACKER.md'
    issues = module.validate_active_folder_edits([legacy_tracker])
    assert any('19990101-legacy-task-ACTIVE' in issue.render() for issue in issues)


def test_validate_session_allows_latest_completed() -> None:
    module = load_guard_module()
    latest = module.REPO_ROOT / 'sessions' / '2025' / '10' / '2025-10-20-001-guard-enhancements.md'
    assert latest.exists(), 'expected latest prior session to exist'
    issues = module.validate_session_edit_dates([latest])
    assert issues == []


def test_validate_session_flags_older_completed() -> None:
    module = load_guard_module()
    older = module.REPO_ROOT / 'sessions' / '2025' / '10' / '2025-10-11-001-task87-replace-monolith.md'
    assert older.exists(), 'expected older session to exist'
    issues = module.validate_session_edit_dates([older])
    assert any('2025-10-11-001-task87-replace-monolith.md' in issue.render() for issue in issues)


def test_should_ignore_relative_skips_configured_prefix(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setenv('CODEX_GUARD_IGNORE_PATHS', 'sessions/1999')
    # Reload to pick up new environment variable
    module = load_guard_module()
    relative = Path('sessions/1999/01/1999-01-01-legacy.md')
    assert module.should_ignore_relative(relative)


def test_validate_session_respects_ignore(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setenv('CODEX_GUARD_IGNORE_PATHS', 'sessions/1999')
    module = load_guard_module()
    legacy_session = module.REPO_ROOT / 'sessions' / '1999' / '01' / '1999-01-01-legacy.md'
    issues = module.validate_session_edit_dates([legacy_session])
    assert issues == []
