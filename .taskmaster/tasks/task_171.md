# Task ID: 171

**Title:** Define approved reconcile apply invocation and confirmation channel

**Status:** done

**Dependencies:** 170 ✓

**Priority:** high

**Description:** Select and define the first future apply invocation channel, with confirmation proof shape and concurrency/idempotency, while keeping apply disabled.

**Details:**

Scope: implement the second gate-closing task from .taskmaster/docs/reconcile-enablement-gate-backlog-amendment.md. Select one first channel, preferably post-merge CI unless review finds a stronger channel. Define positive context proof shape bound to task id, proof, ref/run/operator identity, exact candidate class, audit destination, and idempotency claim. Prove malformed, stale, PR-shaped, wrong-ref, wrong-task, wrong-proof, missing, replayed, and governed-agent-originated confirmations all refuse. Add production-channel concurrency/idempotency design: two approved invocations of the same candidate cannot both fire, with the atomic claim before live write. Ensure the channel cannot call apply while the enable gate remains unsatisfiable. Record approved channel identity in audit breadcrumbs using the Task 170 destination. Keep default config zero-delta and no governed-agent apply surface. Non-goals: no live apply, no enablement, no kill-switch flip, no MCP/CLI apply surface.

**Test Strategy:**

No test strategy provided.
