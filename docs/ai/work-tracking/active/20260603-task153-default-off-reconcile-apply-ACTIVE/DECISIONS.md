# Decisions

- 2026-06-03 — Add the live write apparatus in a new internal module, `aegis_foundation/reconcile_apply_runtime.py`, instead of adding any CLI/MCP/reconcile report route.
- 2026-06-03 — Keep Task 150's public/default scaffold behavior unchanged; only the new runtime can pass `enable_gate_open=True`, and only when `enable_write_path=True` is supplied in isolated tests.
- 2026-06-03 — Implement rollback as snapshot restore of actual changed paths from a whole-tree pre-state. Do not use inverse `task-master set-status` as rollback.
- 2026-06-03 — Treat rollback failure as terminal: write audit/breadcrumb data, engage the kill-switch, and require operator resolution.
