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


def test_validate_gac_guidance_requires_response_modes() -> None:
    module = load_guard_module()
    relative = Path('templates/behaviors/git/before-commit.md')
    text = """
# Before Commit

Return the raw message only.
""".strip()
    issues = module.validate_gac_guidance(relative, text)
    assert any('response-mode markers' in issue.message for issue in issues)


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


def test_validate_gac_guidance_allows_canonical_docs() -> None:
    module = load_guard_module()
    text = (module.REPO_ROOT / 'templates' / 'conventions' / 'git' / 'commit-format.md').read_text(encoding='utf-8')
    issues = module.validate_gac_guidance(Path('templates/conventions/git/commit-format.md'), text)
    assert issues == []


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


def test_validate_template_metadata_flags_missing_required_keys(monkeypatch) -> None:
    module = load_guard_module()
    fake_rule = module.TemplateMetadataRule(
        name='handlers',
        include=['templates/handlers/**/*.md'],
        exclude=[],
        required_keys=['title', 'type', 'status'],
        frontmatter='required',
        enforce=True,
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
    )
    monkeypatch.setattr(module, 'select_template_metadata_rule', lambda path: fake_rule)
    issues = module.validate_template_metadata(Path('templates/handlers/example.md'), '# No frontmatter\n')
    assert any('requires frontmatter' in issue.message for issue in issues)


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
