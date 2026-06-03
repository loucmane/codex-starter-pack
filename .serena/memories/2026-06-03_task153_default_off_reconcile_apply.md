# Task 153 - Default-off reconcile apply write apparatus

Date: 2026-06-03
Branch: feat/task-153-default-off-reconcile-apply

Implemented Task 153 as an internal, default-off reconcile apply write apparatus. The runtime lives in `aegis_foundation/reconcile_apply_runtime.py` and is intentionally not exposed via CLI, MCP, `scripts/codex-task`, installer, or agent-facing reconcile surfaces.

Key implementation points:
- Extended `reconcile_apply_scaffold.py` with an optional internal `enable_gate_open=True` path while preserving the public Task 150 default refusal behavior.
- Added `run_reconcile_apply_write_apparatus(...)`, which refuses by default before validation, idempotency, audit, or Taskmaster writes.
- Test-enabled writes are restricted to isolated temp targets and temp state roots.
- The enabled test path requires approved context, enabled kill switch, matching pinned Taskmaster toolchain evidence, fresh sacrificial cascade validation, and atomic idempotency claim.
- Successful live writes must exactly match the fresh validation predicted delta; divergence rolls back.
- Rollback uses snapshot-restore of pre-state bytes/metadata and deletes created paths, not inverse `set-status`.
- Terminal rollback failure writes an audit record, engages the kill switch, and returns a fail-closed `terminal_rollback_failed` result.
- Audit records include runtime fields for toolchain evidence, predicted/actual delta paths, before/after hashes, outcome, rollback state, authorization binding, and idempotency key.

Tests added in `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py` cover default zero-delta behavior, remove-one-conjunct refusal, fresh validation requirement, real Taskmaster cascade success, idempotency/no-op, atomic file claims, live-delta divergence rollback, partial-write rollback, terminal rollback failure + kill-switch engagement, single-caller audit, and no agent-facing reachability.

Verification captured in `docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/reports/default-off-reconcile-apply/verification-summary.md`:
- `uv run black --check ...` passed.
- `uv run ruff check ...` passed.
- Focused Task 153 pytest passed: 16 passed.
- Adjacent reconcile safety matrix passed: 130 passed.

Docs updated:
- `docs/aegis/reconcile-promotion-contract.md`
- `docs/aegis/reconcile-disabled-apply-scaffold-contract.md`
- `docs/aegis/reconcile-shadow-apply-contract.md`

Task 153 remains default-off. Future enablement/live apply remains a separate task.