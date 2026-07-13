# Task 240 Worktree And Child-Agent Evidence

## Scope

Task 240 implements the capture correction selected by Task 239 while preserving the
existing Git-common-dir ledger, advisory enforcement, legacy workflow scaffolding, and
S:W:H:E narration.

## Delivered State

- Ledger schema version `1` has additive repository identity, worktree root, observed
  HEAD, and parent-agent fields with read-only legacy compatibility and writable
  migration.
- Installed Codex targets receive structurally merged synchronous project hooks for
  SessionStart, PostToolUse, SubagentStart, and SubagentStop. Existing project hooks are
  preserved; malformed project hook JSON is refused.
- Codex mutation, nonzero failure, lifecycle, and inferred-scope rows retain factual
  child/session-root attribution. Deeper ancestry remains explicit-only.
- Witness and replay reads are repository/branch safe by default.
- Two concurrent child worktrees resolve one ledger, retain distinct branch/worktree
  context, and preserve 6/6 rows after normal teardown without per-worktree mutable
  state.

## Evidence

- Contract: `docs/ai/work-tracking/archive/20260713-task240-worktree-child-evidence-COMPLETED/designs/worktree-child-evidence-contract.md`
- Coverage: `docs/ai/work-tracking/archive/20260713-task240-worktree-child-evidence-COMPLETED/reports/worktree-child-evidence/task240-coverage-report.md`
- Regression results: 92 core tests, 139 installer tests with one opt-in smoke skipped,
  43 schema/parity tests, plus Black, Ruff, mirror parity, Taskmaster health, and plan
  sync.

## Continuation

Run the final work-tracking audit, S:W:H:E guard, source-CLI Aegis verification, closeout
preview, and witness. Mark Task 240 done only after final-head verification, then publish
the isolated branch under repository exact-head delivery policy. Preserve all unrelated
main-checkout `.codex`, `.agents`, and local `.aegis` drift.
