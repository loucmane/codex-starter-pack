# Task 153 Add default-off reconcile apply write apparatus – Implementation Notes

## Planned Workstreams
- Extended `aegis_foundation/reconcile_apply_scaffold.py` so the approved-context and kill-switch evaluators remain default-unsatisfiable but can be opened explicitly by an internal test-enabled runtime.
- Added `aegis_foundation/reconcile_apply_runtime.py` as the only module containing the first Taskmaster write function for `merged_but_not_done/git_ancestor`.
- Kept the write path unreachable from CLI, MCP, `scripts/codex-task`, and preview/report consumers; no `--apply` or production/default enablement was added.
- Implemented fresh apply-time sacrificial validation, toolchain staleness refusal, file-backed idempotency claims, audit JSONL writing, whole-tree snapshot rollback, successful-path divergence rollback, partial-write rollback, and terminal rollback failure handling with kill-switch engagement.
- Added `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py` to prove default-off inertness, one-conjunct refusal behavior, fresh validation requirement, real Taskmaster cascade execution in isolated fixtures, idempotency, rollback behavior, terminal rollback failure, single-caller discipline, and no agent surface reachability.
- Updated `docs/aegis/reconcile-promotion-contract.md`, `docs/aegis/reconcile-disabled-apply-scaffold-contract.md`, and `docs/aegis/reconcile-shadow-apply-contract.md` for the Task 153 boundary.
