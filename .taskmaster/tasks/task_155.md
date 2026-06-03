# Task ID: 155

**Title:** Harden semantic canonicalization negative tests

**Status:** pending

**Dependencies:** 154 ✓

**Priority:** high

**Description:** Add paired negative tests for Task 154 semantic canonicalization exemptions so each allowed Taskmaster normalization has a nearby proof that real semantic drift in the same area is still rejected.

**Details:**

Scope: strengthen the Task 154 semantic validator test suite without broadening canonicalization or enabling apply. Add focused tests for tag-level metadata to ensure only enumerated Taskmaster metadata churn is ignored and meaningful tag/task state changes are rejected. Add strict absent-vs-empty subtasks coverage: absent <-> [] is allowed, but non-empty subtasks -> [] or subtask deletion is rejected. Add dependency coercion coverage proving numeric/string dependency normalization is allowed only after canonical type normalization and that dropped, added, or changed dependencies are rejected. Keep the semantic validator as normalize-both-sides-and-diff; do not introduce category-level exemptions. Acceptance: targeted semantic tests fail before the hardening and pass after; existing Task 144-154 tests remain green; no apply path or agent-facing surface is added.
<info added on 2026-06-03T17:11:24.897Z>
Add review-driven core invariant tests in tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py around validate_taskmaster_apply_semantic_delta in aegis_foundation/reconcile_shadow_apply.py. Cover that any non-target task status or content drift rejects even when the target task correctly changes to done, proving the expected_after copy may differ only at the target task status. Add parametrized coverage that the target task status must become exactly done; target transitions to in-progress, cancelled, deferred, pending, or any non-done value must fail with target_status_not_done. Add an updatedAt co-location regression proving the canonicalizer ignores only the updatedAt timestamp field: changing updatedAt alone remains allowed, but changing updatedAt together with nearby semantic content such as title, description, details, priority, dependencies, subtasks, or status still rejects with tasks_json_semantic_mismatch. Keep these as negative tests for the current canonicalize-both-sides-and-diff validator; do not add broader exemptions or apply-facing behavior.
</info added on 2026-06-03T17:11:24.897Z>

**Test Strategy:**

No test strategy provided.
