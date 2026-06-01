# Task ID: 141

**Title:** Add read-only Aegis reconciliation report

**Status:** pending

**Dependencies:** 136 ✓

**Priority:** high

**Description:** Add a read-only reconcile command that reports drift between Taskmaster status, branch/PR/git merge truth, active Aegis work, and local stubs without auto-mutating status.

**Details:**

Agent-runtime-first rationale: final done truth should converge on merge/git reality, but first the system must prove it can detect drift safely. Acceptance: command reports merged-but-not-done, done-but-not-merged, abandoned in-progress branch, stale local/ad hoc stubs, and multi-PR epic ambiguity; gh is optional acceleration and git-only fallback works; command is read-only, emits JSON and human summaries, and has tests for branch ancestry, missing remotes, merged PR metadata, and ambiguous/multi-PR cases.

**Test Strategy:**

No test strategy provided.
