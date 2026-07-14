# Task 242 Mainline Reconciliation — 2026-07-14

## Scope

Task 242 extracts Aegis managed-asset assembly, target materialization, prior-byte recovery,
and fail-closed update planning from the installer into the stdlib-only
`aegis_foundation.managed_update` module. The July 14 continuation reconciles that extraction
with the already-merged Tasks 247–251 without restoring stale pre-adapter behavior.

## Authoritative Composition

- Current `main` is authoritative for autonomous delivery, first-class Codex `apply_patch`
  hooks, Codex hook migration/adoption, advisory-pending closeout, schemas, and all Tasks
  247–251 lifecycle evidence.
- Task 242 is authoritative only for the managed-update module boundary, installer wrappers,
  deterministic golden plans, and its own lifecycle evidence.
- Live and packaged installers must remain byte-identical.
- No downstream state, manifest schema, target layout, enforcement mode, or migration changes.

## Reconciliation Findings

- Codex now shares the Claude hook runtime. The extracted asset builder therefore models
  `codex_shared_runtime_files`, emits each path once in multi-agent installs, and renders the
  shared dispatcher for Codex-only installs.
- Codex hook safety from Tasks 248–249 moved into the extracted core: semantically identical
  owner-created hook JSON is adopted byte-for-byte; structural merge is allowed only for a
  fresh target or unchanged managed baseline; divergent installed or unowned hooks remain
  manual review.
- The Codex golden plan is now 38 creates, two safe modifications, zero skips/conflicts/manual
  reviews, digest `4367457a215ea7d0c08321e8fa5cddb51b52da107a3e8e3784a9a8be4c7f57d3`.
- HP-Fetcher and Blog golden digests are unchanged.

## Verification At Continuation

- 10 managed-update/golden tests passed.
- 49 Codex hook/apply-patch/parity tests passed.
- 155 installer/release tests passed with three explicit opt-in smokes skipped.
- Ruff, Black, source/package parity, Taskmaster health, plan sync, and diff checks pass.
- Full `/tmp` suite: 2,030 passed, four opt-in skips, one known governed-checkout location
  assertion. The isolated assertion passes under a non-temp repository context.
- Signed runtime tree `d29cea9793057340e9b4334cf94287b6300fbe4e` passed the complete suite
  from a non-temp task-bearing checkout: 2,031 passed, four opt-in smokes skipped, zero failures
  in 407.46 seconds. Hosted protected CI and witness must still pass on the final evidence-only
  PR head.

## Delivery And Rollback

Commit the merge composition, verify its exact tree from a normal checkout, retarget draft PR
#268 to `main`, and deliver through the protected evidence policy. Rollback is one reviewed
revert and requires no downstream repair or migration.
