# Task 107 Direct Git Execution Mode - Kickoff

Branch: `feat/task-107-direct-git-execution-mode`.

Purpose: enforce regular Git/GitHub command execution as Codex's default when the user delegates commit/push/PR/merge work and SSH/GPG auth is available. `gac` is a legacy/user convenience alias only and should be emitted only when explicitly requested or selected as manual fallback after auth failure.

Queue-jump rationale: Taskmaster next is Task 10, but Task 107 is intentionally prioritized because stale GAC-default behavior caused a live workflow regression immediately after Task 106.

Current implementation slice: updated `templates/conventions/git/commit-format.md`, `templates/behaviors/git/before-commit.md`, `templates/handlers/operators/git/create-commit-message.md`, `templates/TOOLS.md`, `templates/tools/git/commands.md`, `scripts/codex-guard`, and `tests/meta_workflow_guard/test_guard_rules.py` so canonical commit guidance requires `direct-git-execution`, `full-gac-command`, `message-payload-only`, and `auth-refresh-required`, and rejects stale manual-GAC default language.

Targeted test passed: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_guard_rules.py -k gac` -> 9 passed.