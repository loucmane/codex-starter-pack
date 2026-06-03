# Task ID: 153

**Title:** Add default-off reconcile apply write apparatus

**Status:** done

**Dependencies:** 152 ✓

**Priority:** high

**Description:** Implement the first real reconcile apply write path while keeping it default-off, agent-inaccessible, and fully protected by fresh validation, snapshot rollback, audit records, and idempotency.

**Details:**

Scope:
- Introduce the complete reconcile apply write apparatus for the single supported class only: merged_but_not_done with proof_source=git_ancestor, forward-only Taskmaster set-status done.
- The path must remain default-off. Merging this task must not make apply live in any real repo, CI default, MCP tool, codex-task route, reconcile report/preview consumer, or CLI --apply flag.
- Apply may be reachable only through the gated orchestrator, with positive approved-context proof, eligible class/proof, kill-switch enabled for the class, fresh apply-time sacrificial cascade validation under the current pinned toolchain, and an atomic idempotency claim.
- Missing, corrupt, or unreadable kill-switch state means disabled. Explicit disable has top precedence over every proof, context, or enable. Enabling the kill-switch must itself be agent-excluded.
- Fresh apply-time cascade validation is a correctness gate on the success path, not only a rollback trigger. If the real cascade touches any path outside the validated prediction, misses an expected path, or has stale toolchain evidence, apply must abort and snapshot-restore rollback.
- Rollback must be snapshot-restore, not operation-inverse: restore captured pre-state bytes/type/mode/symlink targets for modified paths and delete paths that were absent before. It must cover the real Taskmaster cascade including .taskmaster/state.json rewrites.
- Rollback failure is terminal and fail-closed: record a durable un-auto-clearable audit/breadcrumb, auto-engage the apply kill-switch, and require operator resolution. Never silently retry or swallow rollback failure.
- Use an atomic idempotency claim/lock before live write so concurrent runs cannot both pass not-already-applied. Same merge/task/proof twice must make the second run a no-op.
- Write an apply audit transaction record for each attempted apply, including approved-context proof, merge proof, toolchain evidence, eligibility predicate/corpus version, predicted and actual deltas, before/after hashes, rollback handle, idempotency key, outcome, and rollback/terminal-failure state.

Acceptance criteria:
- Default config runs the full apply path through the 145 side-effect oracle with real config loader and real cascade and proves zero live-repo deltas. Do not satisfy this with lexical switch assertions.
- One remove-one-conjunct test per required gate: context, eligibility, kill-switch enable, fresh validation, and idempotency. Removing any one must refuse before mutation, and cheap denials must short-circuit before expensive clone validation.
- Single-caller audit proves the live-write function has exactly one caller: the gated orchestrator.
- No transitive agent reach: MCP tools, reconcile flags, --apply, codex-task routes, preview/report consumers, and other agent-facing entrypoints cannot reach the write function.
- Recorded Task 152 validation is not a license: if fresh apply-time validation is stubbed as not run, apply refuses.
- Toolchain mismatch between current apply environment and validated evidence refuses.
- Successful-path divergence test: set-status succeeds but the actual delta differs from prediction; apply aborts and snapshot-restore rollback returns the tree to pre-state.
- Partial-apply failure test: inject failure between set-status and generate; rollback fires and the oracle proves the tree returns to pre-state.
- Rollback-failure test: inject rollback failure; terminal breadcrumb/audit is written, kill-switch is engaged, and future applies are refused until operator resolution.
- Idempotency/concurrency tests prove atomic claim behavior and second-run no-op.
- All 144-152 read-only, inertness, no-consumer, precision, side-effect oracle, shadow, and CI cascade validation tests remain green unchanged.

Non-goals:
- Do not enable apply or flip any production/default kill-switch on.
- Do not add a CLI --apply flag, MCP apply tool, codex-task apply route, operator-local apply, preview/report execution path, shadow accumulation ledger, post-merge enablement workflow, or any class beyond merged_but_not_done/git_ancestor forward done.
- Do not mutate any real governed repo or real task outside isolated test-enabled contexts.

**Test Strategy:**

No test strategy provided.
