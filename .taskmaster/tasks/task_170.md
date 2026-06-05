# Task ID: 170

**Title:** Define reconcile apply audit storage, retention, and review boundary

**Status:** done

**Dependencies:** 169 ✓

**Priority:** high

**Description:** Create the production audit/report destination contract for any future reconcile apply channel before channel or oracle work depends on it.

**Details:**

Scope: implement the first post-Task-169 gate-closing task from .taskmaster/docs/reconcile-enablement-gate-backlog-amendment.md. Define durable audit/report destinations for before, after, rollback, terminal, and channel-confirmation breadcrumbs. Define retention, artifact download/review procedure, and allowed out-of-Taskmaster report paths. Prove failure to write the before-audit breadcrumb blocks mutation before any Taskmaster status write. Prove audit records bind task id, finding kind, proof, context proof id, toolchain, predicted paths, actual paths, semantic validation, rollback handle, idempotency key, and chain hash. Document observability/alerting expectations for apply fired, rollback executed, and terminal rollback failure entered. Keep default config zero-delta and the enable conjunction unsatisfiable. Non-goals: no apply, no approved invocation channel, no kill-switch flip, no production enablement.

**Test Strategy:**

No test strategy provided.
