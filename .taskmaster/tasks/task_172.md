# Task ID: 172

**Title:** Wire live apply-time side-effect oracle for selected channel

**Status:** done

**Dependencies:** 171 ✓

**Priority:** high

**Description:** Make the deep Task 145/A1 mutation-time oracle gate real for the selected future channel while keeping apply disabled.

**Details:**

Scope: implement the third gate-closing task from .taskmaster/docs/reconcile-enablement-gate-backlog-amendment.md. Wrap the selected channel future apply attempt in a process-level before/after snapshot oracle. Allow only explicitly declared audit/report artifacts outside the Taskmaster status cascade. Fail on unexpected .taskmaster, .aegis, work-tracking, git-ref, source, plan, session, or workflow-state deltas. Prove path-level mismatch and semantic mismatch both roll back, and rollback failure enters terminal fail-closed state. Ensure operator-facing preview, audit, and contract text only claim oracle-backed mutation-time blast-radius verification. Extend runtime toolchain binding so live apply refuses when Taskmaster/toolchain evidence does not match the precision-validated baseline. Keep default config zero-delta and enable conjunction unsatisfiable. Non-goals: no apply enablement, no production approved context, no new candidate class.

**Test Strategy:**

No test strategy provided.
