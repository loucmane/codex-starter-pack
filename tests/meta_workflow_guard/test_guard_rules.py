"""Unit tests for codex-guard timestamp enforcement helpers."""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.meta_workflow_guard.cross_project_fixtures import (
    REPO_SHAPES,
    write_governed_markdown,
    write_metadata_policy,
    write_repo_config,
)

# TM 193 parallel-safety: several tests here create fixtures at FIXED paths inside the real
# repo's docs/ai/work-tracking/active|archive dirs (the guard validators resolve paths relative
# to REPO_ROOT, so the fixtures cannot move to tmp). Under pytest-xdist concurrent workers would
# race on those shared paths. Pinning the whole module to one xdist group keeps these tests on a
# single worker (serial among themselves, like a non-parallel run) while the rest of the suite
# parallelizes. Requires `--dist loadgroup`.
pytestmark = pytest.mark.xdist_group(name="guard_real_repo_worktracking")


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


def test_find_legacy_monolith_references_ignores_hyphenated_filenames() -> None:
    module = load_guard_module()
    text = """
    - templates/workflows/examples/common-workflows.md
    - templates/conventions/timestamps/usage-patterns.md
    - templates/integration/best-practices/integration-patterns.md
    """
    assert module.find_legacy_monolith_references(text) == []


def test_find_legacy_monolith_references_flags_standalone_legacy_names() -> None:
    module = load_guard_module()
    text = """
    Replace WORKFLOWS.md first.
    Move references away from PATTERNS.md.
    """
    matches = module.find_legacy_monolith_references(text)
    tokens = {token for token, _hint in matches}
    assert {'workflows.md', 'patterns.md'} <= tokens


def test_validate_active_folder_edits_flags_mismatched_prefix() -> None:
    module = load_guard_module()
    legacy_tracker = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'active' / '19990101-legacy-task-ACTIVE' / 'TRACKER.md'
    issues = module.validate_active_folder_edits([legacy_tracker])
    assert any('19990101-legacy-task-ACTIVE' in issue.render() for issue in issues)


def test_validate_active_folder_allows_tracked_mismatch(monkeypatch) -> None:
    module = load_guard_module()
    folder = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'active' / '19990101-legacy-task-ACTIVE'
    tracker = folder / 'TRACKER.md'

    # ensure helper thinks folder is tracked
    monkeypatch.setattr(module, '_folder_tracked', lambda rel: True)
    issues = module.validate_active_folder_edits([tracker])
    assert issues == []


def test_validate_active_folder_allows_untracked_multi_day_started_folder(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300102')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    tracker = folder / 'TRACKER.md'
    try:
        tracker.write_text(
            """
# Tracker

**Started**: 2030-01-01
**Status**: ACTIVE
**Last Updated**: 2030-01-02

## Progress Log
- **2030-01-02 09:00** — [S:20300102|W:task99-workflow|H:serena/memory|E:.serena/memories/2030-01-02_task99.md] Continued the existing active folder
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        monkeypatch.setattr(module, '_folder_tracked', lambda rel: False)
        issues = module.validate_active_folder_edits([tracker])
        assert issues == []
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_work_tracking_folder_names_skips_tracked_existing(monkeypatch) -> None:
    module = load_guard_module()
    entries = [
        (
            '??',
            'docs/ai/work-tracking/active/19990101-legacy-task-ACTIVE/reports/work-tracking-enforcement/guard-1999-01-01-pass.txt',
        )
    ]
    monkeypatch.setattr(module, '_path_tracked', lambda rel: True)
    issues = module.validate_work_tracking_folder_names(entries)
    assert issues == []


def test_validate_work_tracking_folder_names_allows_untracked_multi_day_started_folder(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300102')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
# Tracker

**Started**: 2030-01-01
**Status**: ACTIVE
**Last Updated**: 2030-01-02

## Progress Log
- **2030-01-02 09:00** — [S:20300102|W:task99-workflow|H:serena/memory|E:.serena/memories/2030-01-02_task99.md] Continued the existing active folder
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        entries = [
            (
                '??',
                'docs/ai/work-tracking/active/20300101-task99-workflow-ACTIVE/reports/workflow/guard-2030-01-02-pass.txt',
            )
        ]
        issues = module.validate_work_tracking_folder_names(entries)
        assert issues == []
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_session_allows_latest_completed(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2025-11-25')
    latest = module.REPO_ROOT / 'sessions' / '2025' / '11' / '2025-11-24-001-task89-work-tracking.md'
    assert latest.exists(), 'expected latest prior session to exist'
    issues = module.validate_session_edit_dates([latest])
    assert issues == []


def test_validate_session_allows_multiple_completed_sessions_from_latest_prior_date(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-03')
    latest = module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-02-002-task.md'
    sibling = module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-02-001-task.md'
    monkeypatch.setattr(module, '_find_latest_prior_session', lambda: latest)
    monkeypatch.setattr(module, '_session_marked_complete', lambda path: True)
    issues = module.validate_session_edit_dates([sibling])
    assert issues == []


def test_validate_session_allows_completed_multi_day_bundle_for_current_task(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-04')
    monkeypatch.setattr(module, '_find_latest_prior_session', lambda: None)
    monkeypatch.setattr(
        module,
        'CURRENT_SESSION_PATH',
        module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-04-001-task99-workflow.md',
    )
    monkeypatch.setattr(module, '_session_marked_complete', lambda path: True)

    changed = [
        module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-01-001-task99-workflow.md',
        module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-02-001-task99-workflow.md',
        module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-03-001-task99-workflow.md',
    ]

    assert module.validate_session_edit_dates(changed) == []


def test_validate_session_flags_incomplete_multi_day_bundle_for_current_task(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-04')
    monkeypatch.setattr(module, '_find_latest_prior_session', lambda: None)
    monkeypatch.setattr(
        module,
        'CURRENT_SESSION_PATH',
        module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-04-001-task99-workflow.md',
    )
    monkeypatch.setattr(module, '_session_marked_complete', lambda path: False)

    changed = [module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-02-001-task99-workflow.md']

    issues = module.validate_session_edit_dates(changed)
    assert any('2030-01-02-001-task99-workflow.md' in issue.render() for issue in issues)


def test_validate_session_flags_completed_prior_session_for_other_task(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-04')
    monkeypatch.setattr(module, '_find_latest_prior_session', lambda: None)
    monkeypatch.setattr(
        module,
        'CURRENT_SESSION_PATH',
        module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-04-001-task99-workflow.md',
    )
    monkeypatch.setattr(module, '_session_marked_complete', lambda path: True)

    changed = [module.REPO_ROOT / 'sessions' / '2030' / '01' / '2030-01-02-001-task100-other.md']

    issues = module.validate_session_edit_dates(changed)
    assert any('2030-01-02-001-task100-other.md' in issue.render() for issue in issues)


def test_validate_session_flags_older_completed(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2025-11-25')
    older = module.REPO_ROOT / 'sessions' / '2025' / '10' / '2025-10-21-001-task88-alignment-docs.md'
    assert older.exists(), 'expected older session to exist'
    issues = module.validate_session_edit_dates([older])
    assert any('2025-10-21-001-task88-alignment-docs.md' in issue.render() for issue in issues)


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


def test_get_current_branch_uses_github_head_ref(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setenv('GITHUB_HEAD_REF', 'feat/task-92-expand-workflow-guard-coverage')
    assert module.get_current_branch() == 'feat/task-92-expand-workflow-guard-coverage'


def test_validate_runtime_artifacts_flags_pycache() -> None:
    module = load_guard_module()
    changed = [module.REPO_ROOT / 'tests' / '__pycache__' / 'example.cpython-312.pyc']
    issues = module.validate_runtime_artifacts(changed)
    assert any('__pycache__' in issue.render() for issue in issues)


def test_validate_runtime_artifacts_flags_codex_sqlite_wal() -> None:
    module = load_guard_module()
    changed = [module.REPO_ROOT / '.codex' / 'logs_2.sqlite-wal']
    issues = module.validate_runtime_artifacts(changed)
    assert any('.codex/logs_2.sqlite-wal' in issue.render() for issue in issues)


def test_validate_session_state_flags_current_mismatch(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    sessions_dir.mkdir()
    state_path = sessions_dir / 'state.json'
    current_session = sessions_dir / '2026-04-22-002-task92-kickoff.md'
    current_session.write_text('---\ndate: 2026-04-22\nsession_id: 2026-04-22-002\n---\n', encoding='utf-8')
    current_link = sessions_dir / 'current'
    current_link.symlink_to(current_session)
    state_path.write_text(
        '{"current":"2026-04-22-001-task91-continuation.md","paused":[],"updated_at":"2026-04-22T17:35:49+02:00"}\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'SESSIONS_DIR', sessions_dir)
    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'CURRENT_SESSION_PATH', current_session)
    entries = [(' M', 'sessions/state.json')]
    changed = [state_path]
    issues = module.validate_session_state(entries, changed)
    assert any('does not match sessions/current target' in issue.message for issue in issues)


def test_validate_session_state_flags_current_in_paused(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    sessions_dir.mkdir()
    state_path = sessions_dir / 'state.json'
    current_session = sessions_dir / '2026-04-22-002-task92-kickoff.md'
    current_session.write_text('---\ndate: 2026-04-22\nsession_id: 2026-04-22-002\n---\n', encoding='utf-8')
    current_link = sessions_dir / 'current'
    current_link.symlink_to(current_session)
    state_path.write_text(
        '{"current":"2026-04-22-002-task92-kickoff.md","paused":["2026-04-22-002-task92-kickoff.md"],"updated_at":"2026-04-22T17:35:49+02:00"}\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'SESSIONS_DIR', sessions_dir)
    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'CURRENT_SESSION_PATH', current_session)
    entries = [(' M', 'sessions/state.json')]
    changed = [state_path]
    issues = module.validate_session_state(entries, changed)
    assert any('must not also appear in paused' in issue.message for issue in issues)


def test_validate_session_state_flags_missing_paused_target(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    sessions_dir.mkdir()
    state_path = sessions_dir / 'state.json'
    current_session = sessions_dir / '2026-04-22-002-task92-kickoff.md'
    current_session.write_text('---\ndate: 2026-04-22\nsession_id: 2026-04-22-002\n---\n', encoding='utf-8')
    current_link = sessions_dir / 'current'
    current_link.symlink_to(current_session)
    state_path.write_text(
        '{"current":"2026-04-22-002-task92-kickoff.md","paused":["2026-04-22-001-task91-continuation.md"],"updated_at":"2026-04-22T17:35:49+02:00"}\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'SESSIONS_DIR', sessions_dir)
    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'CURRENT_SESSION_PATH', current_session)
    entries = [(' M', 'sessions/state.json')]
    changed = [state_path]
    issues = module.validate_session_state(entries, changed)
    assert any("Paused session '2026-04-22-001-task91-continuation.md' does not exist" in issue.message for issue in issues)


def test_validate_session_state_allows_matching_helper(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    sessions_dir.mkdir()
    state_path = sessions_dir / 'state.json'
    paused_session = sessions_dir / '2026-04-22-001-task91-continuation.md'
    paused_session.write_text('---\ndate: 2026-04-22\nsession_id: 2026-04-22-001\n---\n', encoding='utf-8')
    current_session = sessions_dir / '2026-04-22-002-task92-kickoff.md'
    current_session.write_text('---\ndate: 2026-04-22\nsession_id: 2026-04-22-002\n---\n', encoding='utf-8')
    current_link = sessions_dir / 'current'
    current_link.symlink_to(current_session)
    state_path.write_text(
        '{"current":"2026-04-22-002-task92-kickoff.md","paused":["2026-04-22-001-task91-continuation.md"],"updated_at":"2026-04-22T17:35:49+02:00"}\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'SESSIONS_DIR', sessions_dir)
    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'CURRENT_SESSION_PATH', current_session)
    entries = [(' M', 'sessions/state.json')]
    changed = [state_path]
    issues = module.validate_session_state(entries, changed)
    assert issues == []


def test_between_sessions_state_allows_cleared_session_pointers(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    active_dir = tmp_path / 'active'
    sessions_dir.mkdir()
    active_dir.mkdir()
    state_path = sessions_dir / 'state.json'
    current_link = sessions_dir / 'current'
    state_path.write_text(
        '{"current":null,"paused":[],"updated_at":"2030-01-02T17:35:49+02:00"}\n',
        encoding='utf-8',
    )

    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'WORK_TRACKING_PREFIX', active_dir)

    assert module.is_between_sessions_state()


def test_between_sessions_state_rejects_missing_symlink_with_active_session(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    active_dir = tmp_path / 'active'
    sessions_dir.mkdir()
    active_dir.mkdir()
    state_path = sessions_dir / 'state.json'
    current_link = sessions_dir / 'current'
    state_path.write_text(
        '{"current":"2030-01-02-001-task.md","paused":[],"updated_at":"2030-01-02T17:35:49+02:00"}\n',
        encoding='utf-8',
    )

    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'WORK_TRACKING_PREFIX', active_dir)

    assert not module.is_between_sessions_state()


def test_between_sessions_state_rejects_active_work_tracking(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    sessions_dir = tmp_path / 'sessions'
    active_dir = tmp_path / 'active'
    sessions_dir.mkdir()
    active_dir.mkdir()
    (active_dir / '20300102-task99-workflow-ACTIVE').mkdir()
    state_path = sessions_dir / 'state.json'
    current_link = sessions_dir / 'current'
    state_path.write_text(
        '{"current":null,"paused":[],"updated_at":"2030-01-02T17:35:49+02:00"}\n',
        encoding='utf-8',
    )

    monkeypatch.setattr(module, 'SESSION_STATE_PATH', state_path)
    monkeypatch.setattr(module, 'CURRENT_SESSION_SYMLINK', current_link)
    monkeypatch.setattr(module, 'WORK_TRACKING_PREFIX', active_dir)

    assert not module.is_between_sessions_state()


def _configure_tracker_resolution_fixture(module, monkeypatch, tmp_path):
    repo_root = tmp_path / 'repo'
    active_root = repo_root / 'docs' / 'ai' / 'work-tracking' / 'active'
    archive_root = repo_root / 'docs' / 'ai' / 'work-tracking' / 'archive'
    current_work = repo_root / '.aegis' / 'state' / 'current-work.json'
    archive_root.mkdir(parents=True)
    current_work.parent.mkdir(parents=True)
    monkeypatch.setattr(module, 'REPO_ROOT', repo_root)
    monkeypatch.setattr(module, 'WORK_TRACKING_PREFIX', active_root)
    monkeypatch.setattr(module, 'WORK_TRACKING_ARCHIVE_BASE', archive_root)
    monkeypatch.setattr(module, 'CURRENT_WORK_STATE_PATH', current_work)
    monkeypatch.setattr(
        module,
        'WORK_TRACKING_RELATIVE',
        Path('docs/ai/work-tracking/active'),
    )
    monkeypatch.setattr(
        module,
        'WORK_TRACKING_ARCHIVE_RELATIVE',
        Path('docs/ai/work-tracking/archive'),
    )
    return repo_root, active_root, archive_root, current_work


def test_get_active_tracker_path_prefers_active_folder(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    _repo_root, active_root, archive_root, current_work = _configure_tracker_resolution_fixture(
        module, monkeypatch, tmp_path
    )
    active_tracker = active_root / '20300102-task99-current-ACTIVE' / 'TRACKER.md'
    active_tracker.parent.mkdir(parents=True)
    active_tracker.write_text('# Active tracker\n', encoding='utf-8')
    completed_tracker = archive_root / '20300101-task98-old-COMPLETED' / 'TRACKER.md'
    completed_tracker.parent.mkdir(parents=True)
    completed_tracker.write_text('# Completed tracker\n', encoding='utf-8')
    current_work.write_text(
        json.dumps(
            {
                'status': 'completed',
                'paths': {
                    'work_tracking': completed_tracker.parent.relative_to(
                        _repo_root
                    ).as_posix()
                },
            }
        ),
        encoding='utf-8',
    )

    assert module.get_active_tracker_path() == active_tracker


@pytest.mark.parametrize('create_active_root', [False, True])
def test_get_active_tracker_path_falls_back_to_completed_current_work(
    monkeypatch, tmp_path, create_active_root
) -> None:
    module = load_guard_module()
    repo_root, active_root, archive_root, current_work = _configure_tracker_resolution_fixture(
        module, monkeypatch, tmp_path
    )
    if create_active_root:
        active_root.mkdir(parents=True)
    completed_tracker = archive_root / '20300101-task98-old-COMPLETED' / 'TRACKER.md'
    completed_tracker.parent.mkdir(parents=True)
    completed_tracker.write_text('# Completed tracker\n', encoding='utf-8')
    current_work.write_text(
        json.dumps(
            {
                'status': 'completed',
                'paths': {
                    'work_tracking': completed_tracker.parent.relative_to(repo_root).as_posix()
                },
            }
        ),
        encoding='utf-8',
    )

    assert module.get_active_tracker_path() == completed_tracker


def test_get_active_tracker_path_rejects_completed_path_outside_archive(
    monkeypatch, tmp_path
) -> None:
    module = load_guard_module()
    repo_root, _active_root, _archive_root, current_work = _configure_tracker_resolution_fixture(
        module, monkeypatch, tmp_path
    )
    outside = repo_root / 'docs' / 'ai' / 'work-tracking' / 'elsewhere' / 'task-COMPLETED'
    outside.mkdir(parents=True)
    (outside / 'TRACKER.md').write_text('# Outside tracker\n', encoding='utf-8')
    current_work.write_text(
        json.dumps(
            {
                'status': 'completed',
                'paths': {'work_tracking': outside.relative_to(repo_root).as_posix()},
            }
        ),
        encoding='utf-8',
    )

    with pytest.raises(SystemExit, match='must stay under'):
        module.get_active_tracker_path()


def test_get_active_tracker_path_rejects_non_completed_archive_folder(
    monkeypatch, tmp_path
) -> None:
    module = load_guard_module()
    repo_root, _active_root, archive_root, current_work = _configure_tracker_resolution_fixture(
        module, monkeypatch, tmp_path
    )
    archived_active = archive_root / '20300101-task98-old-ACTIVE'
    archived_active.mkdir(parents=True)
    (archived_active / 'TRACKER.md').write_text('# Invalid tracker\n', encoding='utf-8')
    current_work.write_text(
        json.dumps(
            {
                'status': 'completed',
                'paths': {'work_tracking': archived_active.relative_to(repo_root).as_posix()},
            }
        ),
        encoding='utf-8',
    )

    with pytest.raises(SystemExit, match='end with -COMPLETED'):
        module.get_active_tracker_path()


def test_get_active_tracker_path_rejects_non_completed_current_work(
    monkeypatch, tmp_path
) -> None:
    module = load_guard_module()
    repo_root, _active_root, archive_root, current_work = _configure_tracker_resolution_fixture(
        module, monkeypatch, tmp_path
    )
    completed = archive_root / '20300101-task98-old-COMPLETED'
    completed.mkdir(parents=True)
    (completed / 'TRACKER.md').write_text('# Completed tracker\n', encoding='utf-8')
    current_work.write_text(
        json.dumps(
            {
                'status': 'in-progress',
                'paths': {'work_tracking': completed.relative_to(repo_root).as_posix()},
            }
        ),
        encoding='utf-8',
    )

    with pytest.raises(SystemExit, match='no completed Aegis work-tracking path'):
        module.get_active_tracker_path()


def test_collect_validation_issues_includes_archived_tracker(
    monkeypatch, tmp_path
) -> None:
    module = load_guard_module()
    archive_relative = Path('docs/ai/work-tracking/archive')
    archive_folder = tmp_path / archive_relative / '20300101-task98-old-COMPLETED'
    tracker = archive_folder / 'TRACKER.md'
    archive_folder.mkdir(parents=True)
    tracker.write_text('# Completed tracker\n', encoding='utf-8')
    validated_folders = []
    evaluated_files = []

    monkeypatch.setattr(module, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(module, 'WORK_TRACKING_RELATIVE', Path('docs/ai/work-tracking/active'))
    monkeypatch.setattr(module, 'WORK_TRACKING_ARCHIVE_RELATIVE', archive_relative)
    monkeypatch.setattr(module, 'collect_git_status_entries', lambda _include: [])
    monkeypatch.setattr(module, 'compute_changed_files', lambda _entries, _include: [tracker])
    monkeypatch.setattr(module, 'validate_session_state', lambda _entries, _paths: [])
    monkeypatch.setattr(module, 'validate_runtime_artifacts', lambda _paths: [])
    monkeypatch.setattr(module, 'validate_taskmaster_activity', lambda _paths: [])
    monkeypatch.setattr(module, 'validate_active_folder_edits', lambda _paths: [])
    monkeypatch.setattr(module, 'validate_session_edit_dates', lambda _paths: [])
    monkeypatch.setattr(module, 'detect_tracked_active_deletions', lambda _entries: [])
    monkeypatch.setattr(module, 'validate_work_tracking_folder_names', lambda _entries: [])
    monkeypatch.setattr(
        module,
        'validate_work_tracking_documents',
        lambda folder: validated_folders.append(folder) or [],
    )
    monkeypatch.setattr(
        module,
        'evaluate_file',
        lambda path: evaluated_files.append(path) or [],
    )
    monkeypatch.setattr(module, 'resolve_plan_path', lambda: None)
    monkeypatch.setattr(module, 'is_between_sessions_state', lambda: True)

    issues, changed = module.collect_validation_issues(include_untracked=False)

    assert issues == []
    assert changed == [tracker]
    assert validated_folders == [archive_folder]
    assert evaluated_files == [tracker]


def test_validate_taskmaster_activity_requires_session_and_tracker_entries(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    session_path = tmp_path / '2030-01-02-001.md'
    session_path.write_text(
        """---
date: 2030-01-02
session_id: 2030-01-02-001
---

## Session
- **[09:00]** — [S:20300102|W:task92|H:shell:date|E:cmd`date '+%Y-%m-%d %H:%M:%S %Z %z'`] Kickoff
""",
        encoding='utf-8',
    )
    tracker_path = tmp_path / 'TRACKER.md'
    tracker_path.write_text(
        """# Tracker

**Started**: 2030-01-02
**Status**: ACTIVE
**Last Updated**: 2030-01-02

## Progress Log
- **2030-01-02 09:00** — [S:20300102|W:task92|H:serena/memory|E:.serena/memories/2030-01-02_task92.md] Kickoff
""",
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'CURRENT_SESSION_PATH', session_path)
    monkeypatch.setattr(module, 'get_active_tracker_path', lambda: tracker_path)
    changed = [module.REPO_ROOT / '.taskmaster' / 'tasks' / 'tasks.json']
    issues = module.validate_taskmaster_activity(changed)
    rendered = [issue.render() for issue in issues]
    assert any('current session lacks a Taskmaster activity entry' in item for item in rendered)
    assert any('tracker lacks a same-day Taskmaster activity entry' in item for item in rendered)


def test_validate_taskmaster_activity_allows_logged_entries(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    session_path = tmp_path / '2030-01-02-001.md'
    session_path.write_text(
        """---
date: 2030-01-02
session_id: 2030-01-02-001
---

## Session
- **[09:15]** — [S:20300102|W:task92|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Task 92 in progress
""",
        encoding='utf-8',
    )
    tracker_path = tmp_path / 'TRACKER.md'
    tracker_path.write_text(
        """# Tracker

**Started**: 2030-01-02
**Status**: ACTIVE
**Last Updated**: 2030-01-02

## Progress Log
- **2030-01-02 09:16** — [S:20300102|W:task92|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Logged Taskmaster status change
""",
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'CURRENT_SESSION_PATH', session_path)
    monkeypatch.setattr(module, 'get_active_tracker_path', lambda: tracker_path)
    changed = [module.REPO_ROOT / '.taskmaster' / 'tasks' / 'task_092.txt']
    issues = module.validate_taskmaster_activity(changed)
    assert issues == []


def test_build_tracker_last_updated_fix_updates_stale_date(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    relative = Path('docs/ai/work-tracking/active/20300101-task39-guard-auto-fix-mode-ACTIVE/TRACKER.md')
    text = """# Tracker

**Started**: 2030-01-01
**Status**: ACTIVE
**Last Updated**: 2030-01-01

## Progress Log
- **2030-01-02 09:00** — [S:20300102|W:task39|H:shell:date|E:cmd`date`] Continued
"""
    fix = module.build_tracker_last_updated_fix(relative, text)
    assert fix is not None
    assert fix.kind == 'tracker-last-updated'
    assert fix.before == '**Last Updated**: 2030-01-01'
    assert fix.after == '**Last Updated**: 2030-01-02'
    assert '**Last Updated**: 2030-01-02' in fix.new_text
    assert '**Last Updated**: 2030-01-01' not in fix.new_text


def test_build_tracker_last_updated_fix_inserts_missing_field(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    relative = Path('docs/ai/work-tracking/active/20300101-task39-guard-auto-fix-mode-ACTIVE/TRACKER.md')
    text = """# Tracker

**Started**: 2030-01-01
**Status**: ACTIVE

## Progress Log
- **2030-01-02 09:00** — [S:20300102|W:task39|H:shell:date|E:cmd`date`] Continued
"""
    fix = module.build_tracker_last_updated_fix(relative, text)
    assert fix is not None
    assert '**Status**: ACTIVE\n**Last Updated**: 2030-01-02\n' in fix.new_text


def test_collect_auto_fixes_respects_selected_kind(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    relative = Path('docs/ai/work-tracking/active/20300101-task39-guard-auto-fix-mode-ACTIVE/TRACKER.md')
    tracker = tmp_path / relative
    tracker.parent.mkdir(parents=True)
    tracker.write_text(
        """# Tracker

**Started**: 2030-01-01
**Status**: ACTIVE
**Last Updated**: 2030-01-01
""",
        encoding='utf-8',
    )

    assert module.collect_auto_fixes([tracker], {'unsupported-kind'}) == []
    fixes = module.collect_auto_fixes([tracker], {'tracker-last-updated'})
    assert [fix.kind for fix in fixes] == ['tracker-last-updated']


def test_apply_auto_fixes_writes_file_and_history(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'REPO_ROOT', tmp_path)
    relative = Path('docs/ai/work-tracking/active/20300101-task39-guard-auto-fix-mode-ACTIVE/TRACKER.md')
    tracker = tmp_path / relative
    tracker.parent.mkdir(parents=True)
    tracker.write_text('old\n', encoding='utf-8')
    history = tmp_path / 'reports' / 'guard-fixes' / 'history.jsonl'
    fix = module.GuardFix(
        kind='tracker-last-updated',
        path=relative,
        description='Update active tracker Last Updated metadata',
        before='old',
        after='new',
        new_text='new\n',
    )

    module.apply_auto_fixes([fix], history)

    assert tracker.read_text(encoding='utf-8') == 'new\n'
    payload = json.loads(history.read_text(encoding='utf-8').strip())
    assert payload['kind'] == 'tracker-last-updated'
    assert payload['path'] == relative.as_posix()
    assert payload['before'] == 'old'
    assert payload['after'] == 'new'


def test_guard_validate_preview_does_not_apply_fixes(monkeypatch, capsys) -> None:
    module = load_guard_module()
    issue = module.ValidationIssue(Path('docs/ai/work-tracking/active/example/TRACKER.md'), 'Tracker Last Updated is stale')
    fix = module.GuardFix(
        kind='tracker-last-updated',
        path=Path('docs/ai/work-tracking/active/example/TRACKER.md'),
        description='Update active tracker Last Updated metadata',
        before='old',
        after='new',
        new_text='new\n',
    )
    applied = False

    def fail_if_applied(*_args, **_kwargs):
        nonlocal applied
        applied = True

    monkeypatch.setattr(module, 'collect_validation_issues', lambda include_untracked: ([issue], [module.REPO_ROOT / fix.path]))
    monkeypatch.setattr(module, 'collect_auto_fixes', lambda changed_files, selected_kinds=None: [fix])
    monkeypatch.setattr(module, 'apply_auto_fixes', fail_if_applied)

    result = module.guard_validate(
        argparse.Namespace(
            include_untracked=True,
            fix_preview=True,
            auto_fix=False,
            fix_kind=None,
            fix_history=module.DEFAULT_FIX_HISTORY,
        )
    )

    assert result == 1
    assert applied is False
    output = capsys.readouterr().out
    assert 'Guard auto-fix preview:' in output
    assert 'tracker-last-updated' in output


def test_guard_validate_reports_remaining_failures_after_auto_fix(monkeypatch, tmp_path, capsys) -> None:
    module = load_guard_module()
    initial_issue = module.ValidationIssue(Path('TRACKER.md'), 'Tracker Last Updated is stale')
    remaining_issue = module.ValidationIssue(Path('plans/current'), 'Active plan symlink missing or invalid')
    fix = module.GuardFix(
        kind='tracker-last-updated',
        path=Path('docs/ai/work-tracking/active/example/TRACKER.md'),
        description='Update active tracker Last Updated metadata',
        before='old',
        after='new',
        new_text='new\n',
    )
    calls = iter([([initial_issue], [module.REPO_ROOT / fix.path]), ([remaining_issue], [module.REPO_ROOT / fix.path])])
    applied: list[module.GuardFix] = []

    monkeypatch.setattr(module, 'collect_validation_issues', lambda include_untracked: next(calls))
    monkeypatch.setattr(module, 'collect_auto_fixes', lambda changed_files, selected_kinds=None: [fix])
    monkeypatch.setattr(module, 'apply_auto_fixes', lambda fixes, history_path: applied.extend(fixes))

    result = module.guard_validate(
        argparse.Namespace(
            include_untracked=True,
            fix_preview=False,
            auto_fix=True,
            fix_kind=None,
            fix_history=str(tmp_path / 'history.jsonl'),
        )
    )

    assert result == 1
    assert applied == [fix]
    output = capsys.readouterr().out
    assert 'Applied 1 guard auto-fix(es).' in output
    assert 'Guard validation failed after auto-fix:' in output
    assert 'Active plan symlink missing or invalid' in output


def test_validate_gac_guidance_requires_response_modes() -> None:
    module = load_guard_module()
    relative = Path('templates/behaviors/git/before-commit.md')
    text = """
# Before Commit

Return the raw message only. Mention full-gac-command and message-payload-only.
""".strip()
    issues = module.validate_gac_guidance(relative, text)
    assert any('response-mode markers' in issue.message for issue in issues)


def test_validate_gac_guidance_rejects_stale_manual_gac_default() -> None:
    module = load_guard_module()
    relative = Path('templates/handlers/operators/git/create-commit-message.md')
    text = """
# Create Commit Message

Response modes: direct-git-execution, full-gac-command, message-payload-only, auth-refresh-required.

gac is executed manually by the developer.
""".strip()
    issues = module.validate_gac_guidance(relative, text)
    assert any('stale GAC-default language' in issue.message for issue in issues)


def test_validate_gac_guidance_requires_summary_block() -> None:
    module = load_guard_module()
    relative = Path('templates/behaviors/session/session-end.md')
    text = """
```bash
gac "feat: close session

- Captured handoff
- Updated tracker

Work tracking: 20260422-task92-ACTIVE"
```
""".strip()
    issues = module.validate_gac_guidance(relative, text)
    assert any('Summary block' in issue.message for issue in issues)


def test_validate_gac_guidance_ignores_deprecated_compaction_detection() -> None:
    module = load_guard_module()
    text = (module.REPO_ROOT / 'templates' / 'behaviors' / 'session' / 'compaction-detection.md').read_text(encoding='utf-8')
    issues = module.validate_gac_guidance(Path('templates/behaviors/session/compaction-detection.md'), text)
    assert issues == []


def test_validate_gac_guidance_allows_canonical_docs() -> None:
    module = load_guard_module()
    expected_docs = {
        Path('templates/conventions/git/commit-format.md'),
        Path('templates/behaviors/git/before-commit.md'),
        Path('templates/handlers/operators/git/create-commit-message.md'),
        Path('templates/tools/git/commands.md'),
        Path('templates/shared/tools/tool-selection-matrix.md'),
        Path('templates/CONVENTIONS.md'),
        Path('templates/BEHAVIORS.md'),
        Path('templates/REGISTRY.md'),
        Path('templates/MATRICES.md'),
    }
    assert expected_docs.issubset(module.GAC_RESPONSE_MODE_DOCS)
    for relative in sorted(module.GAC_RESPONSE_MODE_DOCS):
        text = (module.REPO_ROOT / relative).read_text(encoding='utf-8')
        issues = module.validate_gac_guidance(relative, text)
        assert issues == [], relative


def test_deprecated_compaction_detection_not_canonical_gac_doc() -> None:
    module = load_guard_module()
    assert Path('templates/behaviors/session/compaction-detection.md') not in module.GAC_SUMMARY_DOCS


def test_detect_tracked_active_deletions_flags(monkeypatch) -> None:
    module = load_guard_module()
    entries = [(' D', 'docs/ai/work-tracking/active/20251021-task88-taskmaster-alignment-ACTIVE/TRACKER.md')]
    monkeypatch.setattr(module, '_path_tracked', lambda rel: True)
    monkeypatch.setattr(module, 'WORK_TRACKING_ARCHIVE_BASE', module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'archive-test')
    issues = module.detect_tracked_active_deletions(entries)
    assert any('Tracked ACTIVE folder' in issue.message for issue in issues)


def test_detect_tracked_active_deletions_ignores_untracked(monkeypatch) -> None:
    module = load_guard_module()
    entries = [(' D', 'docs/ai/work-tracking/active/20251021-task88-taskmaster-alignment-ACTIVE/TRACKER.md')]
    monkeypatch.setattr(module, '_path_tracked', lambda rel: False)
    issues = module.detect_tracked_active_deletions(entries)
    assert issues == []


def _create_work_tracking_fixture(module, folder_name: str) -> Path:
    folder = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'active' / folder_name
    if folder.exists():
        import shutil

        shutil.rmtree(folder)
    archive_base = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'archive'
    archive_base.mkdir(parents=True, exist_ok=True)
    folder.mkdir(parents=True)
    return folder


def test_validate_work_tracking_documents_flags_missing_findings(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-01')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300101')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
- **2030-01-01 09:00** — [S:20300101|W:task99-workflow|H:shell|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Session kickoff
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        (folder / 'FINDINGS.md').write_text(
            """
# Findings

- 2029-12-31 — Legacy observation
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        issues = module.validate_work_tracking_documents(folder)
        assert any('FINDINGS.md' in issue.render() for issue in issues)
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_work_tracking_documents_flags_missing_decisions(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-01')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300101')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
- **2030-01-01 10:00** — [S:20300101|W:task99-workflow|H:serena/memory|E:memories/2030-01-01_task99] Logged progress
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        (folder / 'FINDINGS.md').write_text("- 2030-01-01 — Finding added\n", encoding='utf-8')
        (folder / 'DECISIONS.md').write_text("# Decisions\n\n- 2029-12-31 — Old decision\n", encoding='utf-8')
        (folder / 'CHANGELOG.md').write_text("- 2030-01-01 10:01 CET — Changelog updated\n", encoding='utf-8')
        issues = module.validate_work_tracking_documents(folder)
        assert any('DECISIONS.md' in issue.render() for issue in issues)
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_work_tracking_documents_flags_missing_changelog(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-01')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300101')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
- **2030-01-01 11:00** — [S:20300101|W:task99-workflow|H:serena/memory|E:memories/2030-01-01_task99] Logged progress
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        (folder / 'FINDINGS.md').write_text("- 2030-01-01 — Finding added\n", encoding='utf-8')
        (folder / 'DECISIONS.md').write_text("- 2030-01-01 — Decision added\n", encoding='utf-8')
        (folder / 'CHANGELOG.md').write_text("# Task 99 Changelog\n- 2029-12-30 15:00 CET — Old entry\n", encoding='utf-8')
        issues = module.validate_work_tracking_documents(folder)
        assert any('CHANGELOG.md' in issue.render() for issue in issues)
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_work_tracking_documents_flags_missing_serena_memory(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-01')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300101')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
- **2030-01-01 09:00** — [S:20300101|W:task99-workflow|H:shell|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Session kickoff
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        (folder / 'FINDINGS.md').write_text("- 2030-01-01 — Added finding\n", encoding='utf-8')
        (folder / 'DECISIONS.md').write_text("- 2030-01-01 — Recorded decision\n", encoding='utf-8')
        (folder / 'CHANGELOG.md').write_text(
            "- 2030-01-01 09:05 CET — Noted changes\n",
            encoding='utf-8',
        )
        issues = module.validate_work_tracking_documents(folder)
        assert any('Serena memory' in issue.message for issue in issues)
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_work_tracking_documents_allows_multi_day_with_updates(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300102')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
- **2030-01-02 08:15** — [S:20300102|W:task99-workflow|H:serena/memory|E:memories/2030-01-02_task99] Resumed work (multi-day folder)
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        (folder / 'FINDINGS.md').write_text("- 2030-01-02 — Follow-up finding\n", encoding='utf-8')
        (folder / 'DECISIONS.md').write_text("- 2030-01-02 — Follow-up decision\n", encoding='utf-8')
        (folder / 'CHANGELOG.md').write_text(
            "- 2030-01-02 08:16 CET — Continued updates\n",
            encoding='utf-8',
        )
        issues = module.validate_work_tracking_documents(folder)
        assert issues == []
    finally:
        import shutil

        shutil.rmtree(folder)


def test_validate_work_tracking_documents_flags_multi_day_without_updates(monkeypatch) -> None:
    module = load_guard_module()
    monkeypatch.setattr(module, 'TODAY_ISO', '2030-01-02')
    monkeypatch.setattr(module, 'DATE_PREFIX_EXPECTED', '20300102')
    folder = _create_work_tracking_fixture(module, '20300101-task99-workflow-ACTIVE')
    try:
        (folder / 'TRACKER.md').write_text(
            """
- **2030-01-01 10:00** — [S:20300101|W:task99-workflow|H:serena/memory|E:memories/2030-01-01_task99] Previous day entry
            """.strip()
            + "\n",
            encoding='utf-8',
        )
        (folder / 'FINDINGS.md').write_text("- 2030-01-01 — Previous finding\n", encoding='utf-8')
        (folder / 'DECISIONS.md').write_text("- 2030-01-01 — Previous decision\n", encoding='utf-8')
        (folder / 'CHANGELOG.md').write_text(
            "- 2030-01-01 10:01 CET — Previous changelog entry\n",
            encoding='utf-8',
        )
        issues = module.validate_work_tracking_documents(folder)
        assert any('Tracker missing entry' in issue.render() for issue in issues)
    finally:
        import shutil

        shutil.rmtree(folder)


def test_detect_tracked_active_deletions_flags_when_not_archived(monkeypatch) -> None:
    module = load_guard_module()
    active_folder = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'active' / '20300101-task99-workflow-ACTIVE'
    archive_folder = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'archive' / '20300101-task99-workflow-COMPLETED'
    try:
        active_folder.mkdir(parents=True, exist_ok=True)
        tracker_path = active_folder / 'TRACKER.md'
        tracker_path.write_text("dummy\n", encoding='utf-8')
        monkeypatch.setattr(module, '_path_tracked', lambda rel: rel.as_posix() == tracker_path.relative_to(module.REPO_ROOT).as_posix())

        monkeypatch.setattr(module, 'WORK_TRACKING_ARCHIVE_BASE', archive_folder.parent)
        entries = [(' D', tracker_path.relative_to(module.REPO_ROOT).as_posix())]
        issues = module.detect_tracked_active_deletions(entries)
        assert any('Tracked ACTIVE folder' in issue.message for issue in issues)

    finally:
        import shutil

        shutil.rmtree(active_folder, ignore_errors=True)
        shutil.rmtree(archive_folder, ignore_errors=True)


def test_detect_tracked_active_deletions_ignored_when_archived(monkeypatch) -> None:
    module = load_guard_module()
    active_folder = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'active' / '20300102-task99-workflow-ACTIVE'
    archive_folder = module.REPO_ROOT / 'docs' / 'ai' / 'work-tracking' / 'archive' / '20300102-task99-workflow-COMPLETED'
    try:
        active_folder.mkdir(parents=True, exist_ok=True)
        tracker_path = active_folder / 'TRACKER.md'
        tracker_path.write_text("dummy\n", encoding='utf-8')
        archive_folder.mkdir(parents=True, exist_ok=True)
        (archive_folder / 'TRACKER.md').write_text("**Status**: COMPLETED\n", encoding='utf-8')
        monkeypatch.setattr(module, '_path_tracked', lambda rel: rel.as_posix() == tracker_path.relative_to(module.REPO_ROOT).as_posix())
        monkeypatch.setattr(module, 'WORK_TRACKING_ARCHIVE_BASE', archive_folder.parent)
        entries = [(' D', tracker_path.relative_to(module.REPO_ROOT).as_posix())]
        issues = module.detect_tracked_active_deletions(entries)
        assert issues == []
    finally:
        import shutil

        shutil.rmtree(active_folder, ignore_errors=True)
        shutil.rmtree(archive_folder, ignore_errors=True)


def test_select_template_metadata_rule_matches_handlers() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/handlers/orchestrators/session-start.md'))
    assert rule is not None
    assert rule.name == 'handlers'


def test_select_template_metadata_rule_ignores_exemptions() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/TOOLS.md'))
    assert rule is None


def test_select_template_metadata_rule_matches_behaviors() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/behaviors/session/session-end.md'))
    assert rule is not None
    assert rule.name == 'behaviors'


def test_select_template_metadata_rule_exempts_behavior_index() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/behaviors/index.md'))
    assert rule is None


def test_select_template_metadata_rule_matches_guides() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/guides/index.md'))
    assert rule is not None
    assert rule.name == 'guides'


def test_select_template_metadata_rule_matches_matrices() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/matrices/routing/request-to-handler.md'))
    assert rule is not None
    assert rule.name == 'matrices'


def test_select_template_metadata_rule_exempts_matrices_index() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/matrices/index.md'))
    assert rule is None


def test_select_template_metadata_rule_matches_registry_components() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/registry/navigation/keywords.md'))
    assert rule is not None
    assert rule.name == 'registry-components'


def test_select_template_metadata_rule_exempts_registry_index() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/registry/index.md'))
    assert rule is None


def test_select_template_metadata_rule_matches_engine_modules() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/engine/core/session-resolver.md'))
    assert rule is not None
    assert rule.name == 'engine-modules'


def test_select_template_metadata_rule_exempts_engine_readme() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/engine/README.md'))
    assert rule is None


def test_select_template_metadata_rule_matches_shared_core_pattern() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/shared/patterns/ultrathink-format.md'))
    assert rule is not None
    assert rule.name == 'shared-core-patterns'


def test_select_template_metadata_rule_matches_pattern_templates() -> None:
    module = load_guard_module()
    rule = module.select_template_metadata_rule(Path('templates/patterns/session/session-patterns.md'))
    assert rule is not None
    assert rule.name == 'pattern-templates'


def test_validate_template_metadata_flags_missing_required_keys(monkeypatch) -> None:
    module = load_guard_module()
    fake_rule = module.TemplateMetadataRule(
        name='handlers',
        include=['templates/handlers/**/*.md'],
        exclude=[],
        required_keys=['title', 'type', 'status'],
        frontmatter='required',
        enforce=True,
        schema_path=None,
    )
    monkeypatch.setattr(module, 'select_template_metadata_rule', lambda path: fake_rule)
    text = """---
id: sample
name: Sample
---

# Sample
"""
    issues = module.validate_template_metadata(Path('templates/handlers/example.md'), text)
    messages = [issue.message for issue in issues]
    assert any("missing required key 'title'" in msg for msg in messages)
    assert any("missing required key 'type'" in msg for msg in messages)
    assert any("missing required key 'status'" in msg for msg in messages)


def test_validate_template_metadata_flags_missing_frontmatter(monkeypatch) -> None:
    module = load_guard_module()
    fake_rule = module.TemplateMetadataRule(
        name='handlers',
        include=['templates/handlers/**/*.md'],
        exclude=[],
        required_keys=['title', 'type', 'status'],
        frontmatter='required',
        enforce=True,
        schema_path=None,
    )
    monkeypatch.setattr(module, 'select_template_metadata_rule', lambda path: fake_rule)
    issues = module.validate_template_metadata(Path('templates/handlers/example.md'), '# No frontmatter\n')
    assert any('requires frontmatter' in issue.message for issue in issues)


def test_parse_front_matter_text_supports_yaml_lists() -> None:
    module = load_guard_module()
    metadata = module.parse_front_matter_text(
        """---
title: Example
type: guide
status: stable
tags:
  - alpha
  - beta
dependencies: [one, two]
---

# Example
"""
    )

    assert metadata['tags'] == ['alpha', 'beta']
    assert metadata['dependencies'] == ['one', 'two']


def test_validate_template_metadata_flags_schema_violations(monkeypatch) -> None:
    module = load_guard_module()
    fake_rule = module.TemplateMetadataRule(
        name='handlers',
        include=['templates/handlers/**/*.md'],
        exclude=[],
        required_keys=['title', 'type', 'status'],
        frontmatter='required',
        enforce=True,
        schema_path='templates/metadata/template-frontmatter.schema.json',
    )
    monkeypatch.setattr(module, 'select_template_metadata_rule', lambda path: fake_rule)
    text = """---
title: Example
type: guide
status: unknown
tags: not-a-list
---

# Example
"""

    issues = module.validate_template_metadata(Path('templates/handlers/example.md'), text)
    messages = [issue.message for issue in issues]
    assert any('schema violation at status' in msg for msg in messages)
    assert any('schema violation at tags' in msg for msg in messages)


def test_real_template_frontmatter_schema_accepts_governed_templates() -> None:
    module = load_guard_module()

    governed = []
    for path in Path('templates').rglob('*.md'):
        relative = path.relative_to(Path('.'))
        if module.select_template_metadata_rule(relative) is not None:
            governed.append((relative, path))

    assert governed
    issues = []
    for relative, path in governed:
        issues.extend(module.validate_template_metadata(relative, path.read_text(encoding='utf-8')))

    assert issues == []


def test_validate_swhe_entries_ignores_fenced_placeholder_examples() -> None:
    module = load_guard_module()
    text = """
```text
[S:2025-09-20|W:~/codex|H:searching|E:pending]
```

## Progress Log
- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/core/enforcement-check.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata
    """.strip()
    issues = module.validate_swhe_entries(
        Path('templates/engine/core/enforcement-check.md'),
        text,
        expected_session='20260422',
    )
    assert issues == []


def test_validate_swhe_entries_flags_placeholder_outside_code_fence() -> None:
    module = load_guard_module()
    text = "[S:2025-09-20|W:~/codex|H:searching|E:pending]"
    issues = module.validate_swhe_entries(
        Path('templates/engine/core/enforcement-check.md'),
        text,
        expected_session='20250920',
    )
    assert any('placeholder state' in issue.message for issue in issues)


def test_collect_template_metadata_drift_reports_issues(monkeypatch, tmp_path) -> None:
    module = load_guard_module()
    target = tmp_path / 'templates' / 'handlers' / 'example.md'
    target.parent.mkdir(parents=True)
    target.write_text(
        """---
id: sample
---
""",
        encoding='utf-8',
    )
    fake_rule = module.TemplateMetadataRule(
        name='handlers',
        include=['templates/handlers/**/*.md'],
        exclude=[],
        required_keys=['title', 'type', 'status'],
        frontmatter='required',
        enforce=True,
        schema_path=None,
    )
    monkeypatch.setattr(module, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(module, 'iter_repo_markdown_files', lambda: [target])
    monkeypatch.setattr(module, 'select_template_metadata_rule', lambda path: fake_rule)
    findings = module.collect_template_metadata_drift()
    messages = [finding.message for finding in findings]
    assert any("missing required key 'title'" in message for message in messages)
    assert all(finding.category == 'template-metadata' for finding in findings)


def test_collect_template_metadata_drift_supports_cross_project_template_roots(monkeypatch, tmp_path) -> None:
    module = load_guard_module()

    for name, shape in REPO_SHAPES.items():
        repo_root = tmp_path / name
        write_repo_config(repo_root, shape)
        policy_path = write_metadata_policy(repo_root, shape)
        markdown_path = write_governed_markdown(repo_root, shape, with_metadata=False)

        monkeypatch.setattr(module, 'REPO_ROOT', repo_root)
        monkeypatch.setattr(module, 'TEMPLATE_METADATA_POLICY_PATH', policy_path)

        findings = module.collect_template_metadata_drift()

        assert any(finding.path == markdown_path.relative_to(repo_root) for finding in findings)


def test_collect_canonical_doc_drift_flags_missing_doc(monkeypatch) -> None:
    module = load_guard_module()
    missing = Path('templates/missing-canonical.md')
    monkeypatch.setattr(module, 'GAC_RESPONSE_MODE_DOCS', {missing})
    monkeypatch.setattr(module, 'GAC_SUMMARY_DOCS', set())
    findings = module.collect_canonical_doc_drift()
    assert any(finding.path == missing and 'missing' in finding.message.lower() for finding in findings)


def test_collect_command_surface_drift_flags_missing_subcommand(monkeypatch) -> None:
    module = load_guard_module()

    def parser_without_drift():
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command', required=True)
        subparsers.add_parser('validate')
        return parser

    monkeypatch.setattr(module, 'build_parser', parser_without_drift)
    findings = module.collect_command_surface_drift()
    assert any("drift-check" in finding.message for finding in findings)


def test_guard_drift_check_writes_reports(monkeypatch, tmp_path, capsys) -> None:
    module = load_guard_module()
    report_dir = tmp_path / 'reports' / 'template-drift'
    finding = module.DriftFinding(
        category='template-metadata',
        path=Path('templates/handlers/example.md'),
        message='Example drift',
        blocking=True,
    )
    monkeypatch.setattr(module, 'collect_drift_findings', lambda: [finding])
    monkeypatch.setattr(module, 'REPO_ROOT', tmp_path)
    args = argparse.Namespace(
        report_dir='reports/template-drift',
        report=None,
        json_out=None,
        strict=True,
    )
    result = module.guard_drift_check(args)
    captured = capsys.readouterr()
    assert result == 1
    assert 'Template drift report' in captured.out
    text_reports = sorted(report_dir.glob('summary-*.txt'))
    json_reports = sorted(report_dir.glob('summary-*.json'))
    assert text_reports, 'expected drift text report'
    assert json_reports, 'expected drift json report'
    payload = json.loads(json_reports[0].read_text(encoding='utf-8'))
    assert payload['finding_count'] == 1
    assert payload['findings'][0]['message'] == 'Example drift'


def test_pre_commit_config_runs_codex_guard_validate_and_drift() -> None:
    config = Path('.pre-commit-config.yaml').read_text(encoding='utf-8')
    assert 'python3 scripts/codex-guard validate --include-untracked' in config
    assert 'python3 scripts/codex-guard drift-check --strict --report-dir ""' in config
    assert config.count('pass_filenames: false') >= 2
    assert config.count('always_run: true') >= 2
