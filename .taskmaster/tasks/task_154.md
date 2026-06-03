# Task ID: 154

**Title:** Add semantic blast-radius validation for reconcile apply

**Status:** pending

**Dependencies:** 153 ✓

**Priority:** high

**Description:** Harden the Task 153 reconcile apply apparatus so validated apply deltas are semantic, not just path-level, before any post-merge shadow accumulation or live enablement work proceeds.

**Details:**

Scope:
- Extend the reconcile apply validation model from path-level blast radius to a two-tier gate: keep the Task 145 whole-tree/path oracle as the outer gate for unexpected files, and add a semantic/content validator as the inner gate for expected aggregate files.
- For `.taskmaster/tasks/tasks.json`, parse before and after, apply the same toolchain-version-scoped canonicalization to both sides, then assert the only surviving semantic difference is the target task allowed status transition to `done`. Known Taskmaster number-to-string ID/dependency normalization must be factored out by normalize-both-sides-and-semantic-diff, not by exempting broad reformat/canonicalization categories.
- Treat canonicalization as pinned to the current validated Taskmaster/toolchain evidence. A Taskmaster or relevant runner/toolchain version change must invalidate semantic evidence and force re-validation before apply.
- Deepen the existing sacrificial clone validation and Task 153 fresh apply-time validation in place; do not add a parallel validator. The single blast-radius truth computation must return both path delta and semantic delta verdicts.
- Add generated task markdown content validation for the target task file. The validator must assert expected target-task status/content changes and reject unrelated or action-shaped drift; it must not accept path-level change alone.
- Add an audit for type-sensitive task ID comparisons across Aegis/Codex code, especially guards, readiness, reconcile, Taskmaster joins, and current-work/task-binding code. No logic should depend on numeric task IDs such as `id == 42`; comparisons must normalize task IDs first.
- Add terminal rollback hard-deny: any terminal rollback-failure breadcrumb independently blocks future apply attempts, regardless of kill-switch state.
- Add a subsequent-apply refusal test after terminal state and define/guard the operator-resolution clearing path as agent-excluded. A governed agent must not be able to clear terminal rollback state and resume apply.
- Add explicit governed-repo target refusal for the Task 153 test-enabled path: even with `enable_write_path=True`, `target_root` pointing at the real governed repo must refuse before validation or mutation.
- Add behavioral reachability tests for agent-facing surfaces, not only static import/caller tests. Instantiate or exercise CLI/MCP/codex-task surfaces and prove no route dispatches to the write apparatus.
- Add enable-source hardening tests proving no agent-writable input, env var, repo config, workflow state, or preview/report payload can satisfy the enable gate or flip the kill-switch toward enabled.

Acceptance criteria:
- Existing Task 153 default-off behavior remains unchanged: default apply path produces zero live-repo deltas and no audit/idempotency/Taskmaster writes.
- Path oracle still fails on any unexpected file or git/workflow-state delta.
- Semantic validator catches unrelated task changes inside `.taskmaster/tasks/tasks.json`, including unrelated status flips, dependency changes, ID changes that survive canonicalization, metadata drift, task insertion/removal, and subtask drift.
- Canonicalized semantic diff allows the known number-to-string normalization only when it is content-preserving under the pinned Taskmaster/toolchain evidence, and rejects any broad canonicalization exemption that hides real semantic changes.
- Generated markdown validator catches unexpected non-target generated task content drift and accepts only the expected target generated file update.
- Fresh apply-time validation refuses when semantic delta differs from prediction, even if path delta matches.
- Terminal rollback-failure breadcrumb alone blocks subsequent apply; kill-switch failure does not leave apply live.
- Clearing terminal rollback state requires approved non-agent context and is unreachable from governed-agent surfaces.
- Test-enabled apply refuses the real governed repo target even when all other gates are satisfied.
- CLI, MCP, codex-task, preview/report, and config/env entrypoints cannot behaviorally dispatch to or enable the write path.
- Type-sensitive task ID audit is covered by tests or static guard assertions and documents any intentional normalized comparison helper.
- All Task 144-153 read-only, inertness, side-effect oracle, precision, rollback, preview, shadow, CI cascade, and default-off write apparatus tests remain green.

Non-goals:
- Do not enable reconcile apply.
- Do not add CLI `--apply`, MCP apply, codex-task apply, operator-local apply, post-merge enablement, or any new mutation class.
- Do not hand-edit or revert Taskmaster-owned `tasks.json` normalization; treat it as evidence for semantic validation.
- Do not replace the path oracle with semantic validation; both gates are required.

Test strategy:
- Add focused tests for semantic tasks.json diffing, canonicalize-both-sides behavior, generated markdown validation, terminal breadcrumb hard-deny, governed-target refusal, behavioral agent-surface reachability, and enable-source hardening.
- Extend the existing Task 151/152/153 sacrificial cascade tests so validation returns path and semantic verdicts from the same computation.
- Re-run the focused Task 153 apparatus tests plus adjacent reconcile safety matrix.

**Test Strategy:**

No test strategy provided.
