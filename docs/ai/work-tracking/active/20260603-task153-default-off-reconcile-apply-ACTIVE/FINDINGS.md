# Findings

- 2026-06-03 — Task 153 can extend the Task 150 scaffold without weakening existing behavior by adding explicit `enable_gate_open` parameters that default to `False`.
- 2026-06-03 — Rollback must capture a whole-tree pre-state for non-ignored paths, not only predicted paths, because the failure mode under test is an unpredicted path appearing after an otherwise successful write.
- 2026-06-03 — The existing shadow cascade helpers already provide the right prediction and proof-artifact semantics, so the write runtime reuses them rather than creating a second eligibility model.
