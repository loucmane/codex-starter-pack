# Task ID: 201

**Title:** Aegis break-glass recovery contract

**Status:** pending

**Dependencies:** 195

**Priority:** high

**Description:** Ensure every BLOCKED state includes a sanctioned, auditable recovery path instead of requiring upstream emergency releases.

**Details:**

Define and implement a recovery contract for readiness/BLOCKED states: every block must include a copyable safe repair, explicit reason, blast-radius tier, audit destination, and escalation path. Add aegis override --reason or equivalent for rate-limited break-glass where policy allows, with attribution and immutable evidence. Cover cases from the HP-Coach deployment: repair-while-blocked, completed observation/task folder archive, post-closeout delivery, pending tracking, stale MCP, and dirty observation artifacts. Use replay harness fixtures to prove recovery commands resolve historical deadlocks and do not become a generic bypass for source edits, destructive commands, or external deployments.

**Test Strategy:**

No test strategy provided.
