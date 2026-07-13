# Task ID: 240

**Title:** Make Worktree And Child-Agent Evidence First-Class

**Status:** in-progress

**Dependencies:** 239 ✓

**Priority:** high

**Description:** Implement the narrowly selected correction from the capture audit so supported child work is recorded once with reliable repository, branch, worktree, and parent-child attribution.

**Details:**

Implement roadmap workstream C4 only after Task 239 identifies the causal gap. Ensure all worktrees resolve the intended shared ledger; events record repository identity, worktree root, branch, HEAD, agent_id, agent_type, and parent_agent_id where supported; parent orchestration and child implementation remain distinguishable; concurrent writers do not lose, duplicate, or cross-attribute events; branch-scoped witness and replay queries exclude unrelated traffic; and teardown preserves history. Explicitly report unsupported hook surfaces. Test two concurrent child worktrees with mutations and failures, WAL contention/retry, teardown ownership, and cross-branch verification-at-HEAD isolation. Compare measured coverage before and after, and document a parent-only rollback.

**Test Strategy:**

No test strategy provided.
