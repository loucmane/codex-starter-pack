# Task 240 Verification Evidence

## Focused Checks

| Check | Result |
| --- | --- |
| changed ledger/recorder/replay/witness/audit suites | 92 passed |
| full installer suite | 139 passed, 1 opt-in certification smoke skipped |
| schema, packaged-asset parity, replay-coldstart, and PR-4 parity suites | 43 passed |
| ledger and witness focused rerun | 52 passed |
| installed Codex two-child worktree acceptance | passed |
| Codex reload/continuation/repair/release-contract regressions | 21 passed |
| Black on all changed Python | passed |
| Ruff on all changed Python | passed |
| six source/package mirror comparisons | byte-identical |

## Repository Checks

| Check | Result |
| --- | --- |
| full pytest suite except one temp-location-invalid case | 1,908 passed, 4 opt-in distribution/MCP smokes skipped |
| Taskmaster health | 245 tasks, 383 subtasks, 430 references, 0 invalid |
| plan/tracker sync | passed |
| work-tracking audit | passed; no issues |
| S:W:H:E guard | passed |
| timestamp regressions | 5 passed |
| template drift strict check | 0 findings |
| CI-profile template scanners | all 6 stages passed; 0 broken references, 0 security findings |
| reference-fix dry-run | no fixes |
| template monitoring/performance strict reports | passed |
| phase-0, cost, and migration dashboards | generated with their documented warning statuses; commands passed |
| Git whitespace check | passed at the completed implementation/evidence head |

## Local Temp-Worktree Exception

The unchanged test
`test_test_enabled_apply_refuses_governed_repo_target_before_validation` is deliberately
deselected only in this local full-suite run. Its premise is that the governed source
checkout is outside the system temp directory. Task 240's isolated implementation
worktree is `/tmp/codex-task240`, so the premise is false and the test reaches the next
fail-closed reason (`candidate_already_done`) instead of
`target_not_isolated_temp`.

The test and production reconcile code are unchanged. Hosted CI checks out the source
repository outside `/tmp` and must execute this case normally before delivery. The
focused Task 240 behavior has no dependency on reconcile apply.

## Source-Repository Aegis State

This source worktree intentionally has no installed-target manifest or shim. Source-CLI
status therefore reports `not_installed`; strict installed-target verify refuses the
missing manifest exactly as designed. Task 240 does not install, repair, or fabricate a
second mutable Aegis instance in the linked worktree. The applicable source-repository
lifecycle gates are tests, Taskmaster health, plan sync, work-tracking audit, S:W:H:E
guard, source scanners, and the hosted branch witness.

`aegis brief --check` passed through the source CLI. The temporary ignored capsule and
verification files generated during diagnosis were removed; tracked `.aegis/brief.json`
was preserved.

## Preservation

- Main-checkout user configuration and untracked `.codex`, `.agents`, and local `.aegis`
  drift remain outside this worktree and outside the task staging scope.
- The current protected `.codex/deep-work.config.toml` digest observed from the main
  checkout is
  `sha256:f5c579c39b7655ca3078e484ffdce007229618f44a08d7a28b63c65dc96a6708`.
- Four generated template dashboard files were restored byte-for-byte to `HEAD` through
  the repository-approved file-edit path after validation; they are not Task 240
  changes.
- No per-worktree `.aegis/state` is installed or checked in.

## Hosted Evidence

Pending implementation commit and draft PR. The implementation head must pass the
ordinary Python 3.11/3.12, source guard, meta-workflow guard, Aegis witness, and
evidence-gated delivery checks before Taskmaster completion/archive.
