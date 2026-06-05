# Reconcile Enablement Gate Backlog Amendment

## Context

Aegis Task 169 completed the fresh enablement-readiness audit for the reconcile apply
control plane. The source-of-truth inventory is
`docs/aegis/reconcile-enablement-readiness-gates.md`.

Task 169's verdict is NO-GO for creating any first guarded apply task. The current
implementation remains default-off and agent-unreachable. The next backlog must close
gates before any future apply task can be scoped.

This amendment creates the post-Task-169 gate-closing backlog. It must not create an apply
task, enable mutation, flip a kill-switch, add an MCP/CLI apply surface, or broaden the
candidate class beyond `merged_but_not_done/git_ancestor`.

## Corrected Gate Order

The order is derived from the Task 169 inventory and follow-up review:

1. Audit destination, retention, and review boundary first. Approved invocation and live
   oracle work both need a defined audit/report destination.
2. Approved invocation and confirmation channel second. The live oracle must wrap a
   selected channel, so channel selection precedes oracle implementation.
3. Live apply-time side-effect oracle after the selected channel exists.
4. Agent-excluded enablement plus kill-switch semantics after channel/oracle foundations.
5. Terminal rollback operator resolution after audit and kill-switch semantics exist.
6. Final agent-surface regression after the selected channel and enablement machinery are
   present.
7. Enablement evidence decision packet last. It may say GO or NO-GO, but it must not enable
   apply by itself.
8. A first guarded apply task may only be created later if the decision packet says GO and
   every gate marker is closed.

## New Gate-Closing Tasks

### Task 170: Define Reconcile Apply Audit Storage, Retention, And Review Boundary

Create the production audit/report destination contract for any future reconcile apply
channel.

Acceptance criteria:

- Defines a durable audit/report destination for before, after, rollback, terminal, and
  channel-confirmation breadcrumbs.
- Defines retention, artifact download/review procedure, and allowed out-of-Taskmaster
  report paths.
- Proves failure to write the before-audit breadcrumb blocks mutation before any Taskmaster
  status write.
- Proves audit records bind task id, finding kind, proof, context proof id, toolchain,
  predicted paths, actual paths, semantic validation, rollback handle, idempotency key, and
  chain hash.
- Documents observability/alerting expectations for apply fired, rollback executed, and
  terminal rollback failure entered.
- Keeps default config zero-delta and enable conjunction unsatisfiable.
- Non-goals: no apply, no approved invocation channel, no kill-switch flip, no production
  enablement.

### Task 171: Define Approved Reconcile Apply Invocation And Confirmation Channel

Select and define the first future apply invocation channel, preferably post-merge CI
unless review finds a stronger first channel.

Acceptance criteria:

- Selects one first channel: post-merge CI or operator-controlled local.
- Defines positive context proof shape bound to task id, proof, ref/run/operator identity,
  exact candidate class, audit destination, and idempotency claim.
- Proves malformed, stale, PR-shaped, wrong-ref, wrong-task, wrong-proof, missing, replayed,
  and governed-agent-originated confirmations all refuse.
- Adds production-channel concurrency/idempotency design: two approved invocations of the
  same candidate cannot both fire; the atomic claim happens before live write.
- Ensures the channel cannot call apply while the enable gate remains unsatisfiable.
- Records approved channel identity in audit breadcrumbs using Task 170's destination.
- Keeps default config zero-delta and no governed-agent apply surface.
- Non-goals: no live apply, no enablement, no kill-switch flip, no MCP/CLI apply surface.

### Task 172: Wire Live Apply-Time Side-Effect Oracle For The Selected Channel

Make the deep Task 145/A1 gate real for the selected future channel while keeping apply
disabled.

Acceptance criteria:

- Wraps the selected channel's future apply attempt in a process-level before/after
  snapshot oracle.
- Allows only explicitly declared audit/report artifacts outside the Taskmaster status
  cascade.
- Fails on unexpected `.taskmaster`, `.aegis`, work-tracking, git-ref, source, plan,
  session, or workflow-state deltas.
- Proves path-level mismatch and semantic mismatch both roll back, and rollback failure
  enters terminal fail-closed state.
- Ensures operator-facing preview, audit, and contract text only claim oracle-backed
  mutation-time blast-radius verification.
- Extends runtime toolchain binding so live apply refuses when the Taskmaster/toolchain
  evidence does not match the precision-validated baseline.
- Keeps default config zero-delta and enable conjunction unsatisfiable.
- Non-goals: no apply enablement, no production approved context, no new candidate class.

### Task 173: Implement Agent-Excluded Enablement And Kill-Switch Control Plane

Define the durable enable/disable control plane without turning it on.

Acceptance criteria:

- Defines durable global and per-class kill-switch state with default-off behavior.
- Proves missing, corrupt, unreadable, stale, wrong-class, global-disabled, and
  class-disabled states all refuse before clone or write work.
- Proves explicit disable outranks valid context, eligibility, precision evidence,
  toolchain match, and idempotency.
- Proves governed agents cannot enable, clear, or rewrite the switch from MCP, CLI,
  `scripts/codex-task`, hooks, environment, config, workflow-state, or report surfaces.
- Defines emergency disable behavior. Disabling may be allowed through an approved
  non-agent path; enabling remains stricter and agent-excluded.
- Proves the enable conjunction remains unsatisfiable after this task in default CI and
  default local state.
- Non-goals: no kill-switch flip to enabled, no live apply, no operator-local apply
  command, no MCP apply tool.

### Task 174: Define Terminal Rollback Failure Operator Resolution

Define and test the production operator procedure for terminal rollback failures.

Acceptance criteria:

- Documents the manual resolution procedure for dirty governed repositories after rollback
  failure.
- Proves terminal breadcrumbs are durable, audit-linked, and checked before any future
  apply attempt.
- Proves terminal state never retries or auto-clears.
- Proves clearing terminal state requires approved non-agent operator action and is audited.
- Proves governed agents cannot clear terminal state, delete the breadcrumb, or re-enable
  the class through normal governed surfaces.
- Integrates with the Task 170 audit destination and Task 173 kill-switch semantics.
- Non-goals: no live apply, no automatic repair, no agent-cleared terminal state.

### Task 175: Re-run Final Agent-Surface Regression With Selected Channel Present

Re-prove agent exclusion after the selected channel, audit destination, oracle, enablement,
and kill-switch machinery exist.

Acceptance criteria:

- Single-gated-caller audit still holds.
- No MCP tool, package CLI command, `scripts/codex-task` path, preview/report consumer,
  repair/start/kickoff flow, or hook can transitively reach apply.
- No agent-writable input can satisfy approved context, confirmation, idempotency claim,
  kill-switch enablement, terminal-state clearing, or audit destination selection.
- Behavioral dispatch tests instantiate real MCP/CLI/codex-task surfaces and fail to reach
  the write function.
- Adds a standing CI test that forbids production apply code or a satisfiable enable
  conjunction while any G1-G8 gate marker remains open.
- Keeps default config zero-delta.
- Non-goals: no live apply, no enablement, no new candidate class.

### Task 176: Produce Enablement Evidence Decision Packet

Produce a reviewed go/no-go decision packet after all prior gates have evidence.

Acceptance criteria:

- Computes gate status from machine-readable G1-G8 markers and refuses GO if any marker is
  open.
- Cites the precision corpus artifact as the precision basis; operational runs are
  inertness/context evidence only; cascade smoke is not precision.
- Lists toolchain baseline and live evidence and refuses GO on mismatch.
- Lists operational post-merge runs, precision corpus result, unexplained divergences,
  benign-normalization reviews, alerting/audit readiness, terminal-resolution readiness,
  and agent-surface regression evidence.
- Requires explicit recorded operator decision; a green packet must not auto-create Task
  177 or enable apply.
- Emits NO-GO if evidence is incomplete, stale, ambiguous, or missing.
- Non-goals: no apply, no kill-switch flip, no creation of first guarded apply task by the
  packet itself.

### Task 177: First Guarded Reconcile Apply Task Placeholder

Do not create this task unless Task 176 emits GO. If it is eventually created, it must be a
separate reviewed task and remain scoped only to `merged_but_not_done/git_ancestor`.

Acceptance criteria if created later:

- First commit checks the Task 176 decision packet is GO and operator-approved.
- Refuses to run if any G1-G8 gate marker is open or stale.
- Keeps candidate class limited to `merged_but_not_done/git_ancestor`.
- No MCP apply tool and no governed-agent path.

Do not generate this placeholder as an actionable task now unless Taskmaster requires it for
dependency planning; it should remain a documented future line, not pending implementation.

## Mechanical NO-GO Enforcement

Tasks 170-176 must add mechanical enforcement so Task 177 cannot be created or made
reachable prematurely:

- Each closed gate emits a machine-readable marker or tested assertion.
- A standing test fails if production apply entrypoints or satisfiable enablement appear
  while any gate marker remains open.
- Every gate-closing task re-runs default config zero live delta and enable conjunction
  unsatisfiable checks.
- The decision packet refuses GO unless all gate markers are closed and current.
- No task may broaden the candidate class, introduce a governed-agent apply surface, or
  enable mutation as a side effect of closing a gate.
