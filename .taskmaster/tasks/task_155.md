# Task ID: 155

**Title:** Harden semantic canonicalization negative tests

**Status:** pending

**Dependencies:** 154 ✓

**Priority:** high

**Description:** Add paired negative tests for Task 154 semantic canonicalization exemptions so each allowed Taskmaster normalization has a nearby proof that real semantic drift in the same area is still rejected.

**Details:**

Scope: strengthen the Task 154 semantic validator test suite without broadening canonicalization or enabling apply. Add focused tests for tag-level metadata to ensure only enumerated Taskmaster metadata churn is ignored and meaningful tag/task state changes are rejected. Add strict absent-vs-empty subtasks coverage: absent <-> [] is allowed, but non-empty subtasks -> [] or subtask deletion is rejected. Add dependency coercion coverage proving numeric/string dependency normalization is allowed only after canonical type normalization and that dropped, added, or changed dependencies are rejected. Keep the semantic validator as normalize-both-sides-and-diff; do not introduce category-level exemptions. Acceptance: targeted semantic tests fail before the hardening and pass after; existing Task 144-154 tests remain green; no apply path or agent-facing surface is added.

**Test Strategy:**

No test strategy provided.
