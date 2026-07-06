# Task ID: 226

**Title:** Capsule freshness triggers for delivery and orientation boundaries

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Make capsule compile/status support session/resume, post-merge, task-status-change, orientation, pre-delivery, verification, risk-register-change, and manual triggers so long-running chats and PR delivery keep one canonical capsule fresh without restoring per-mutation ceremony.

**Details:**

Adds aegis brief --status, compile_reason metadata, freshness snapshots in current.json, SessionStart reason stamping, and spec/tests. This task records the scoped capsule freshness trigger implementation and supplies the delivery-witness branch/task mapping for the PR.

**Test Strategy:**

No test strategy provided.
