# Evidence profile contract

Project profiles specialize the generic evidence workflow without moving project judgment into
Gas City Operations. A profile is a tracked JSON file with schema
`gas-city-evidence-profile.v1`, one project/rig identity, and one or more lanes.

Each lane declares exactly:

- a tracked bundle builder, prompt, rubric, and JSON report schema relative to the project root;
- the closed bundle-file inventory the builder must create;
- the closed report-file inventory a reviewer may create; and
- literal case-insensitive patterns that must never appear in the blind bundle.

The project owns what those assets mean. The generic commands only bind their bytes, enforce
closed input/output surfaces, validate declared schemas, and compare finding identifiers. They
must never recreate a project gate, fold, quality score, promotion decision, or repair verdict.

## Freeze request

`gas-city-evidence-freeze-request.v1` is a reviewed, UTF-8 JSON object with these exact fields:

`schema`, `run_id`, `created_at`, `parent_bead`, `mode`, `repair`, `supersedes`,
`subject_root`, `candidates`, `external_inputs`, `fable_inputs`, `authoritative_outputs`,
`lane_io`, `authorization_envelope`, and `run_root`.

All paths except tracked profile asset paths are absolute. `mode` is always `shadow`. A repair
uses a new run id, sets `repair=true`, names `supersedes`, and points to the prior sibling run;
no evidence file is overwritten.

## Authorization envelope

`gas-city-evidence-authorization-envelope.v1` records, but never grants, live authority. It binds
the canonical request digest, authorization interval, verbatim operator authorization, project,
rig, bead, run, mode, worker ceiling, exact lane report directories, and exclusions. At minimum
the exclusions are `push`, `merge`, `deploy`, `publish`, `rig-lifecycle`, and
`authoritative-output-write`.

The controller must still possess current operator authority when dispatch occurs. An envelope
cannot authorize routing, lifecycle, a worker, signing, Git publication, or project mutation.

## Ordering artifacts

Controller events use schema `gas-city-evidence-controller-event.v1` and are appended to the
parent bead as evidence:

1. `seal` binds the full-visibility Fable report path and SHA-256.
2. `fable-readback` binds the seal event and confirms the same report digest by Fable.
3. `dispatch` binds the readback event and precedes every worker report.
4. `release` binds the dispatch event, follows collection, and contains the exact policy
   attestation: `Fable did not independently access worker reports before release.`

The first three relationships are mechanically verified. The nonaccess statement is explicitly
policy-only; v1 does not pretend to prove information Fable did not access.
