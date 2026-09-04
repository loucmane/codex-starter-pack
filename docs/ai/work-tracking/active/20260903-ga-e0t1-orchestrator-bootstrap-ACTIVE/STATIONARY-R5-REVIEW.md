# ga-fjoi stationary coordination — independent R5 source review

Status: **source PASS; delivery and live acceptance pending**. This record does
not close ga-fjoi, activate candidate code, or grant lifecycle/disclosure authority.

## Review binding

The operator supplied Fable's independent review on 2026-09-04. All six review
areas passed, including the previously unreviewed R3 source-only entrypoints,
control-word hard-policy correction, and complete stationary coordination path.
The relay is snapshotted in `reports/ga-fjoi-independent-review-r5-relay.txt`
with one final newline added (and no other byte difference); snapshot SHA-256 is
`d4dd2953bd45d5e6166f641e89c67623cceaf3ef5ed947ddf1369dd45f11127c`.
Original attachment SHA-256 is
`affba25883cc2094c73b782142fec9e3c1dfeeef97269f5bf2c60ba0459b66f3`.
Some prose in the operator-provided relay is truncated; no missing text has been
silently reconstructed as a direct quote.

Reverified before integration: all 22 candidate file hashes match manifest
`9fa2506e6c7287671e912b0a1053479564c67693b640b1260586a0b320b5d67e`,
and full patch SHA-256 remains
`2dd2d720d6f7562f6637ec751ff8c32481281879381edb93290b5db59ef43ba1`.
The source review packet SHA-256 remains
`efd674ebc0a7f4a7f90d0d607729bd3d00f846efc7f91bdd2cd547cf36d1cac4`.
No source changes were made in response to this PASS.

## Test evidence and limits

Locally observed final result: **2,721 passed, 21 skipped, zero failures**;
receipt `reports/ga-fjoi-source-only-r5-final-verification.json`, SHA-256
`2aec321577aad430d2f002f84496395f357a25d6e4d7ba6d060304138be97b31`.
The receipt binds the preserved complete JUnit and unchanged source hashes.

Fable reports its independent full run exited zero with 2,738 passing cases out
of the same 2,742 total, with the 17 environment-dependent cases executing there.
That implies four remaining skips. This is **operator-relayed independent test
evidence**, not a second locally observed JUnit result. Fable independently counted
the 108 real canonical caches and reviewed the executable poison-positive controls.

Carry these limits into live acceptance: installed-runtime overlays need their
own reviewed binding; the one-coordinator-per-Bead rule is policy, not a distributed
lease; these checks are not an OS sandbox or protection against a hostile same-UID
process racing verified files. Source PASS does not prove live client behavior.

## Integration preflight

Candidate branch is `codex/ga-e0t1-orchestrator-bootstrap`, HEAD
`d9488ec280effc008f24616c34fdfa8444f56ade`. Local and remote main are exactly
`3641fa7aa11c9713da3dac3c075f50caee547ed8`; canonical checkout is clean.
Their merge base is `ed5bdca9ff27efdb4f2e618e55ae1f89dd43a27b`.
Main's entire tree is byte-identical to that merge-base tree. Thus main introduces
no competing file edit: the candidate's later acceptance record and appended
tracking history must remain intact. No conflict resolution, reset, rebase,
archive move, or historical rewrite is needed or authorized by this observation.
Recheck these exact facts before the signed integration commit and publication.

Fresh ga-fjoi readback remains in progress, unassigned, and bound to
`external-coordinator.v1:3405c3087bfabe276d3e8cf9721b4ae095c2d221e7952c9532cf3dfa8bef2c88`.
Its note records the one-time direct Codex implementation exception. Readiness
remains READY for ga-e0t1. The denied production Bead-note append remains preserved
and unreplayed; its eventual reconciliation still requires the approved path.

## Remaining acceptance

1. Exact signed candidate, verified base, required hosted green CI,
   CLEAN/MERGEABLE state, and zero unresolved review threads.
2. Merge-bound canonical activation with loaded-byte proof and unchanged unrelated
   configuration; never activate the unmerged source candidate.
3. One unchanged canonical Fable seat coordinating two distinct synthetic task
   worktrees, negative target/permission cases and non-interference; observe the
   existing fixture, session and disclosure scope before starting any client.
4. Reconcile the owed Bead evidence through its approved path, then close ga-fjoi
   only after the actual live acceptance succeeds. Parent ga-e0t1 closeout still
   depends separately on ga-fc6p's preservation-aware archive repair.

All earlier R1–R5 reports, refusals, interrupted runs, failed fixtures, cache
files and original paths remain preserved. No HPFetcher/Blog, rig, service, key,
configuration, or live session mutation occurred while recording this review.
