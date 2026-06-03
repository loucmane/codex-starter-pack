# Task 155 - Semantic Canonicalization Negative Tests

Task 155 adds test-only hardening for `validate_taskmaster_apply_semantic_delta` in `aegis_foundation/reconcile_shadow_apply.py` via `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`.

Coverage added:
- Target task status must transition exactly to `done`; non-done statuses reject with `target_status_not_done`.
- Non-target task content drift rejects with `tasks_json_semantic_mismatch`.
- `updatedAt` and tag metadata churn remain narrow exemptions; adjacent semantic content changes still reject.
- Dependency ID type normalization does not hide dropped dependencies.
- Absent `subtasks` and `subtasks: []` remain equivalent only for absent-vs-empty normalization; non-empty subtask deletion rejects.

Verification captured in `docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/reports/semantic-canonicalization-negatives/verification-summary.md`: focused shadow apply tests `34 passed`, adjacent apply apparatus tests `19 passed`, and Ruff passed for the touched test file.