# Task 144 Reconcile Read-Only Contract

Task 144 encodes Task 143's reconcile promotion criteria as a contract/test gate, not a mutation feature.

Key decisions:
- `aegis reconcile` remains report-only/read-only across `scripts/codex-task`, packaged `aegis_foundation` CLI, core `scripts/_aegis_installer.py::reconcile`, and MCP `aegis.reconcile`.
- Future auto-mutation must be a separate Taskmaster task and branch with operator confirmation, audit breadcrumb, rollback evidence, high-confidence proof requirements, and manual-only finding classifications.
- Manual-only/ambiguous findings include `multi_pr_epic_ambiguity`, `abandoned_in_progress_branch`, `stale_local_stub`, `local_ad_hoc_stub`, and squash/offline unknown merge truth such as `git_only_non_ancestor_or_missing_base`.

Implementation artifacts:
- Added `docs/aegis/reconcile-promotion-contract.md`.
- Added CLI parser tests in `tests/meta_workflow_guard/test_aegis_installer.py` rejecting mutation-shaped reconcile flags for both repo helper and packaged CLI.
- Added MCP schema/execution tests in `tests/meta_workflow_guard/test_aegis_mcp_server.py` ensuring `aegis.reconcile` exposes only `target_dir`, `base_ref`, `use_github`, and returns `read_only=True` without mutating git status.

Verification captured during implementation:
- Focused pytest: `uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py` -> 102 passed, 1 skipped.
- Smoke: `python3 scripts/codex-task aegis reconcile --target-dir . --no-github` -> CLEAN, 144 tasks, 0 findings, and empty before/after `git status --short` diff.