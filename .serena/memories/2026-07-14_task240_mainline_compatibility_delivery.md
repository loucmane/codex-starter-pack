# Task 240 Mainline Compatibility And Delivery

## Context

Task 240's worktree and child-agent evidence branch was based on an older mainline. Before
delivery, current main through Task 251 was merged non-rewriting into the existing branch.
The branch-local Task 240 plan and session projections were restored to their verified
completed-source values before any further mutation.

## Compatibility Resolution

- Preserved Task 240's shared Git-common-dir ledger, worktree attribution, child/parent
  identity, branch-safe witness/replay filtering, and structural Codex hook merge behavior.
- Preserved current main's first-class canonical `apply_patch` handling, pending-tracking
  capture, ledger recording, installer adoption safety, per-agent reload state, and
  advisory-pending closeout semantics.
- Kept `scripts/_aegis_installer.py` and its packaged asset byte-identical.
- Kept historical Task 247-251 source, Taskmaster, plan, session, and archived evidence
  unchanged; those files are mainline history, not Task 240-authored replacements.
- Did not create installed Aegis state in the source worktree and did not touch unrelated
  primary-checkout `.codex`, `.agents`, or local `.aegis` drift.

## Verification So Far

- Focused combined Codex/worktree slice: 43 passed.
- Broad adapter, installer, replay, continuation, and delivery compatibility run: 901
  passed, four explicit opt-in skips, followed by 20/20 passing continuation/repair tests
  after correcting a duplicate local test helper.
- Final exact-tree repository suite: 1,862 passed and four explicit opt-in certification/
  distribution smokes skipped in one sequential Git-isolated invocation.
- Affected adapter/installer/replay rerun after static cleanup: 214 passed and one explicit
  certification smoke skipped.
- Merge-aware source guard remediation: 85 guard-rule tests pass; only clean staged paths
  inherited unchanged from MERGE_HEAD are excluded from current-session date validation,
  while current-task, worktree, untracked, renamed, and inspection-failure cases remain
  visible.
- Black and Ruff checks pass on the composed files.
- Completed-source readiness is READY, Taskmaster full-graph health is valid, and plan
  parity passes.

## Remaining Delivery Work

Create the non-rewriting merge commit, push PR #266, and require fresh exact-head hosted
verification before evidence-governed delivery.
