# Evidence workflow v1 contract

## Purpose

Provide a reusable report-only evidence lane for Gas City-managed projects without creating a
second ledger or weakening project-owned quality logic. Version 1 proves the abstraction against
one already-adjudicated HPFetcher batch. Blog is out of scope.

## Ownership boundary

- The `gas-city-workflow` plugin owns the manifest schema, reusable skill, validation, bundle
  audit, report validation, and cross-lane comparison.
- Each project owns its profile, bundle builders, lane prompts, rubrics, and report schemas.
- Beads remain the only work ledger. A run must resolve its parent bead in the profile's declared
  rig before freeze.
- Aegis stores source-change evidence. Obsidian is a deterministic projection only.
- HPFetcher retains all gate, fold, promotion, adjudication, and repair semantics. The generic
  layer records and compares those outcomes but never re-derives them.

## V1 surface

The skill exposes `freeze`, `shadow`, `adjudicate`, and `closeout`. The implementation consists of
one JSON schema and five small commands under `plugins/gas-city-workflow/scripts/evidence/`:

1. `freeze_evidence_run.py` creates an immutable shadow manifest from a validated profile,
   subject Git state, bound workflow assets, sorted external-input inventory, and authorization
   envelope reference.
2. `validate_evidence_run.py` recomputes every binding, refuses existing run-id overwrite,
   requires `supersedes` for successor repairs, cross-checks project id/rig, and hard-errors on
   every mode except `shadow`.
3. `audit_blind_bundle.py` rejects forbidden content, `.git` metadata, special files, escaping
   symlinks, undeclared files, and writes outside the lane's exact output directory.
4. `validate_review_report.py` checks lane schema, manifest/run/candidate identity, declared
   outputs, and evidence-only status.
5. `compare_review_lanes.py` verifies sealed Fable digest/readback/release ordering and compares
   lane findings without calculating a domain verdict.

## Frozen manifest

`gas-city-evidence-run.v1` binds:

- `run_id`, `created_at`, `frozen_at`, optional `supersedes`, immutable `mode=shadow`;
- parent bead id, project id, rig, subject repository/branch/commit/clean state;
- profile path and SHA-256;
- every lane prompt, rubric, report schema, and bundle-builder path plus SHA-256;
- Fable sealed-review input paths and SHA-256 values;
- a sorted external-input list with path, SHA-256, and reason plus its canonical inventory digest;
- exact lane input bundle and authorized output paths;
- authorization-envelope path/digest, expiry, scope, and explicit exclusions;
- authoritative-output inventory captured before dispatch;
- append-forward lineage and closeout evidence references.

The envelope records live authority but never grants it. Dispatch requires both current operator
authorization and a manifest-matching envelope. Merge, push, deploy, publication, project-output
mutation, and rig lifecycle remain excluded.

## Blindness and ordering

Bundle builders produce closed inputs in fresh empty directories. Blind lanes never receive a
checkout, worktree, Git metadata, or a path that can traverse back to the source repository.
Bundle audits run before dispatch and after collection.

Fable reviews its declared full-visibility inputs, seals the plaintext report digest, and the
controller appends a seal event to the parent bead. Fable reads that note back and confirms the
digest. Only then may dispatch occur. After worker reports are collected, the controller appends
a release event, and only then are reports supplied for Fable comparison. The event order is
mechanical; the claim that Fable did not independently access reports before release is
explicitly policy-only in v1.

## Fail-closed fixtures before pilot

Tests must reject digest drift, profile drift, external-input drift, bundle leakage, Git metadata,
escaping symlinks, unauthorized writes, dirty subject trees, project/rig mismatch, overwrite of a
run id, repair without `supersedes`, candidate mismatch, malformed reports, interrupted closeout,
and `mode=authoritative`.

## Pilot acceptance

Use one already-adjudicated HPFetcher batch. Capture authoritative outputs before the shadow run,
then require identical bytes afterward. Sol lanes write only inside declared report directories.
Record seal → Fable readback → dispatch → release ordering on the parent bead, produce a generic
comparison report, prove zero process/session/worktree residue, and record the evidence pointer on
the parent bead. No shadow finding changes HPFetcher output or promotion state.
