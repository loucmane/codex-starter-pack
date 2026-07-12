# Completed Delivery Guidance Contract

## Evidence

Blog Task 67 (`gitleaks-repository-dispatch`) closed successfully on
`feat/task-67-gitleaks-repository-dispatch`. GitHub PR #28 merged that branch into `main`:

- head: `0833414a8faa469c34ea26846e36eb85da277876`
- merge commit: `81511aa10bfa13191f95bd15b80d4d889ce2e0e8`
- base: `main`
- merged at: `2026-07-11T20:51:18Z`

The retained closeout report records Task 67 and the completed archive. On synchronized `main`,
`aegis next` nevertheless returned historical branch-mismatch guidance because branch comparison
preceded merged-PR inspection. After Task 38 kickoff, the global passed Task 67 report could also
be mistaken for current Task 38 closeout truth.

## Current-Truth Rule

A passed closeout report belongs to current work only when the existing
`_closeout_report_matches_current_work` predicate proves both task ID and work-tracking identity.
An envelope's own `closeout_passed_at` remains a valid compatibility signal. A report for a prior
task cannot arm delivery guidance for new active work.

## Historical-Branch Rule

When current and recorded branches differ, Aegis may classify the closed task as merged complete
before returning branch mismatch only if all evidence agrees:

1. GitHub reports a merged PR whose head is the recorded closed branch.
2. The PR includes a merge-commit OID.
3. The current branch equals the PR base branch.
4. The current branch has an upstream for that same base branch.
5. The merge commit is an ancestor of local `HEAD`.
6. `HEAD...@{u}` reports zero ahead and zero behind.

The proof is read-only. It does not fetch, repair, sync, reset, rewrite state, or fabricate an
envelope. Any absent, malformed, unavailable, or contradictory input produces concise
`delivery_unknown` evidence.

## Preserved Behavior

- Same-branch no-upstream, pushed-without-PR, draft, pending-CI, failed-CI, green-awaiting-owner,
  and merged states remain unchanged.
- Merge authorization remains explicit and exact-head governed.
- Advisory/strict enforcement behavior is unchanged.
- Legacy plans, sessions, trackers, handoffs, decisions, and S:W:H:E remain complementary.
- Installed targets continue using current-work state; source-checkout derivation is unaffected.

## Exclusions

- No generic repair or delivery sync.
- No output-budget work (Task 238).
- No worktree/subagent attribution work (Tasks 239-240).
- No PR-4 retirement, hash chain, OS sandbox, policy DSL, or ledger migration.

## Rollback

Revert Task 245's squash commit. The prior branch-mismatch-first behavior returns without target
state migration or cleanup.
