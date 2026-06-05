# Task ID: 173

**Title:** Implement agent-excluded enablement and kill-switch control plane

**Status:** pending

**Dependencies:** 172

**Priority:** high

**Description:** Define the durable enable/disable control plane without turning it on, with separate tests for agent exclusion and kill-switch precedence.

**Details:**

Scope: implement the fourth gate-closing task from .taskmaster/docs/reconcile-enablement-gate-backlog-amendment.md. Define durable global and per-class kill-switch state with default-off behavior. Prove missing, corrupt, unreadable, stale, wrong-class, global-disabled, and class-disabled states all refuse before clone or write work. Prove explicit disable outranks valid context, eligibility, precision evidence, toolchain match, and idempotency. Prove governed agents cannot enable, clear, or rewrite the switch from MCP, CLI, scripts/codex-task, hooks, environment, config, workflow-state, or report surfaces. Define emergency disable behavior; disabling may be allowed through an approved non-agent path, while enabling remains stricter and agent-excluded. Prove the enable conjunction remains unsatisfiable after this task in default CI and default local state. Non-goals: no kill-switch flip to enabled, no live apply, no operator-local apply command, no MCP apply tool.

**Test Strategy:**

No test strategy provided.
