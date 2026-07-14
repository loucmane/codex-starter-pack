# Task 251 Advisory Pending Closeout Scope

## Objective

Correct the upstream Aegis pending-tracking semantics exposed by Blog Task 40. Advisory-only pending events are passive audit evidence: they must remain stored and visible, but they must not block strict delivery verification or closeout. Required or untrustworthy pending state must continue to fail closed.

The filename is retained because the repository kickoff template and source guard require `designs/wizard-flow.md`; this document defines the actual Task 251 runtime boundary and does not introduce a wizard.

## Confirmed Contradiction

The hook runtime records each event with enforcement-mode provenance. In advisory mode, repository guidance says agents do not reconcile events per mutation and must not drain them as routine ceremony. The verifier and closeout currently ignore that provenance:

- `_strict_pending_tracking_check` fails whenever the queue is non-empty;
- `closeout` independently fails whenever `_pending_tracking_events` is non-empty;
- the existing reader filters invalid event shapes and can collapse malformed state into an apparently empty queue;
- status and re-entry guidance still point advisory users toward generic repair.

That combination turns passive evidence into a delivery backlog and gives malformed state inconsistent treatment.

## Classification Contract

Introduce one read-only pending-state classifier and use its result throughout status, strict verification, closeout readiness, closeout, doctor, next-action guidance, and repair guidance.

The classifier must distinguish:

1. `absent` — queue file does not exist; delivery-safe.
2. `empty` — valid queue payload with zero events; delivery-safe.
3. `advisory_only` — every event is a mapping with explicit `mode: advisory`; delivery-safe, preserved, and summarized.
4. `required_only` — one or more explicit strict/required events; delivery-blocking.
5. `mixed` — advisory and required events coexist; delivery-blocking so advisory evidence cannot hide required work.
6. `unknown` — missing, unsupported, or untrusted mode/provenance, or invalid event shape; delivery-blocking.
7. `malformed` — invalid JSON, non-object payload, or non-list `events`; delivery-blocking.

Classification is based on stored event provenance, not on a caller-provided claim. Historical advisory-only residue remains non-blocking after strict re-entry; newly recorded strict events remain required and fail closed.

## Evidence and Output Contract

No verification or closeout path may delete, rewrite, drain, or individually log advisory events. Reports expose:

- exact total, advisory, required, and unknown counts;
- queue validity and classification;
- whether advisory evidence was preserved;
- whether required work remains unresolved;
- a bounded sample and the canonical queue artifact path.

Agent-facing output must remain bounded even for a large queue. The queue file remains the complete evidence source; summaries must never imply that sampled output is the full queue.

## Closeout Contract

- `verify(strict=True)` passes the pending-tracking gate for absent, empty, and advisory-only state.
- Closeout uses the same classifier; advisory-only state does not disable evidence population or create repair guidance.
- Required, mixed, unknown, and malformed states fail closed.
- `closeout(dry_run=True)` is observational and does not mutate pending tracking, current work, reports, handoff, or work-tracking files.
- Normal advisory delivery requires neither `aegis repair --apply` nor manual queue draining.

## Repository Boundary

In scope:

- upstream Aegis source and packaged mirror;
- focused installer, output-budget, replay/fixture, parity, and documentation tests;
- an Aegis-owned Blog Task 40 reproduction fixture containing no live Blog reads;
- upstream and packaged lifecycle/retry documentation.

Out of scope:

- no edits, staging, repair, closeout, Taskmaster mutation, or delivery operation in `/home/loucmane/dev/blog`;
- no enforcement-mode change;
- no draining of any live pending queue;
- no Gas Town migration or Taskmaster retirement;
- no broad legacy-scaffolding retirement.

## Acceptance Gate

Before implementation begins:

- Taskmaster Task 251 is `in-progress` and depends on completed Task 250;
- readiness, Taskmaster health, work-tracking audit, plan sync, and source guard pass;
- this scope artifact and the same-day Serena memory are referenced by the tracker;
- the Blog repository remains untouched.

Before delivery:

- positive advisory-only verification and closeout tests pass while proving queue preservation;
- strict/required, mixed, unknown, malformed, and invalid-shape regressions fail closed;
- dry-run immutability, context-budget behavior, source/package parity, replay fixture, and documentation parity pass;
- the final handoff includes the exact stable source commit and an attended, separate Blog update/retry procedure.
