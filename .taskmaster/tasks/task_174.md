# Task ID: 174

**Title:** Define terminal rollback failure operator resolution

**Status:** pending

**Dependencies:** 173

**Priority:** high

**Description:** Define and test the production operator procedure for terminal rollback failures without adding automatic repair or agent clearing.

**Details:**

Scope: implement the fifth gate-closing task from .taskmaster/docs/reconcile-enablement-gate-backlog-amendment.md. Document the manual resolution procedure for dirty governed repositories after rollback failure. Prove terminal breadcrumbs are durable, audit-linked, and checked before any future apply attempt. Prove terminal state never retries or auto-clears. Prove clearing terminal state requires approved non-agent operator action and is audited. Prove governed agents cannot clear terminal state, delete the breadcrumb, or re-enable the class through normal governed surfaces. Integrate with the Task 170 audit destination and Task 173 kill-switch semantics. Non-goals: no live apply, no automatic repair, no agent-cleared terminal state.

**Test Strategy:**

No test strategy provided.
