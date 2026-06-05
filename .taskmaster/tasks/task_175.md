# Task ID: 175

**Title:** Re-run final agent-surface regression with selected channel present

**Status:** pending

**Dependencies:** 174

**Priority:** high

**Description:** Re-prove agent exclusion after the selected channel, audit destination, oracle, enablement, and kill-switch machinery exist.

**Details:**

Scope: implement the sixth gate-closing task from .taskmaster/docs/reconcile-enablement-gate-backlog-amendment.md. Prove the single-gated-caller audit still holds. Prove no MCP tool, package CLI command, scripts/codex-task path, preview/report consumer, repair/start/kickoff flow, or hook can transitively reach apply. Prove no agent-writable input can satisfy approved context, confirmation, idempotency claim, kill-switch enablement, terminal-state clearing, or audit destination selection. Behavioral dispatch tests must instantiate real MCP, CLI, and codex-task surfaces and fail to reach the write function. Add a standing CI test that forbids production apply code or a satisfiable enable conjunction while any G1-G8 gate marker remains open. Keep default config zero-delta. Non-goals: no live apply, no enablement, no new candidate class.

**Test Strategy:**

No test strategy provided.
