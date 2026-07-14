# PR #278 Executor Run-Evidence Remediation

## Root Cause

PR #278's ordinary candidate-head checks were complete and green, but the
merge-capable retry was triggered by `workflow_run`. GitHub attached Actions run
`29320216830` and its two jobs to trusted `main` at
`0088fff82337fb428740db42a8146c5bef92186d`, while the pull request head remained
`eb7933bf771738ef3d13dc18921dce2141df1a54`.

The first Task 250 implementation searched the candidate-head Checks API for the
current `policy-authorized merge` job. That is structurally impossible for a
`workflow_run` executor, so policy failed closed with
`executor-self-check-missing` even though the current run and merge job were
available through the trusted Actions run/jobs APIs.

## Correction

- Candidate-head check runs and legacy statuses remain a complete, independent,
  all-green inventory.
- Prior canonical `policy-authorized merge` checks are excluded from independent
  status accounting, but they cannot establish current executor identity.
- Current executor identity comes from the exact numeric Actions run and its
  complete paginated job inventory.
- Run and job evidence must match trusted workflow name/path, repository and head
  repository, run attempt, active status, canonical job URL, and trigger-specific
  head semantics.
- `pull_request_target` binds to the candidate head; `workflow_run` binds to the
  current trusted default-branch head.
- Both executor evaluations recollect minimized run/job evidence. The second
  evaluation remains immediately before the protected SHA-pinned merge.

No attended-path, review, exact-head, current-base, same-repository, complete-file,
required-workflow, independent-check, legacy-status, or test-deletion gate was
weakened.

## Verification

| Check | Result |
|---|---|
| Focused delivery policy/workflow tests | `90 passed` |
| PR #276 `pull_request_target` replay | evaluator `provisional`; exact trusted executor `allow` |
| PR #278 `workflow_run` replay | evaluator `allow`; exact trusted executor `allow` without a current candidate self-check |
| Adversarial run/job/check/status cases | passed; malformed, incomplete, spoofed, stale, completed, duplicate, and mismatched evidence defers/fails closed |
| Ruff lint | passed |
| Ruff format check | passed |
| Actionlint | passed |
| Source/package policy parity | byte-identical |
| Taskmaster health | 249 tasks, 383 subtasks, 434 dependencies, 0 invalid |
| Work-tracking audit | passed |
| Plan/tracker sync | passed |
| S:W:H:E guard | passed |
| Diff check | passed |
| Changed-diff secret scan | no leaks found |
| Full repository suite from `/tmp` worktree | `1990 passed, 4 skipped, 1 failed` in 394.12s |
| Exact location-dependent failure from source checkout | `1 passed` |

The sole full-suite failure was
`test_test_enabled_apply_refuses_governed_repo_target_before_validation`, which
uses `REPO_ROOT` to distinguish the governed source checkout from an isolated
temporary target. A Git worktree rooted under `/tmp` is intentionally classified
as isolated and returned `candidate_already_done` instead of
`target_not_isolated_temp`. The exact assertion passed from
`/home/loucmane/codex`; it is not caused by this delivery-policy change.

## Hosted Acceptance Completed

The governance remediation passed protected checks and merged at reviewed head
`6d679245` as `89ea3a4`. PR #278 was then updated to current base through a signed,
non-rewriting merge and autonomously squash-merged by trusted run `29323250166`
as `c3daa484`. Repository-dispatch CI and guards all passed against that exact
merge SHA. See `hosted-canary-acceptance.md` for the complete run inventory and
tree-equality evidence.
