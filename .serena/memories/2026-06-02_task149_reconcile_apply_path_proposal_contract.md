# Task 149 - Reconcile apply-path proposal contract

Branch: `feat/task-149-reconcile-apply-path-proposal-contract`.

Task 149 was sharpened after Claude feedback: the primary deliverable is the invocation/confirmation model for any future reconcile apply path, not just another enumeration of Tasks 145-148.

Implemented as contract/design only:
- Added `docs/aegis/reconcile-apply-path-proposal-contract.md`.
- Added `tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`.
- Updated related reconcile promotion, rollback, and inert preview docs to reference Task 149 while preserving read-only behavior.
- Updated Taskmaster Task 149 details to center agent-excluded invocation.

Key design decision:
- Future apply must be agent-excluded.
- The governed agent cannot invoke apply or satisfy confirmation.
- Apply cannot be exposed as an MCP tool for the governed agent, as `aegis reconcile --apply`, or through the normal agent-facing `scripts/codex-task aegis reconcile` path.
- First acceptable future channels are post-merge CI or operator-controlled local invocation outside the governed agent runtime.

First future apply class remains narrow:
- `merged_but_not_done` with `git_ancestor` proof only.
- All other classes remain manual-only or contract-excluded.

New prerequisites named for future work:
- apply-audit breadcrumb separate from degraded events
- global kill-switch default-disabled
- Task 150 should be a disabled apply orchestration scaffold with an intentionally unsatisfiable enable gate only after the Task 149 prompt is reviewed.

Verification completed so far:
- Focused Task 149 tests: 10 passed.
- Adjacent reconcile contract suite: 73 passed, 94 deselected.
- Black check passed for new Task 149 test.
- Ruff passed for new Task 149 test.