# Task ID: 251

**Title:** Fix Aegis Advisory Pending Delivery Closeout Semantics

**Status:** done

**Dependencies:** 250 ✓

**Priority:** high

**Description:** Correct Aegis so advisory-mode pending events are preserved and summarized without blocking strict delivery verification or closeout, while required strict pending-tracking failures still fail closed. Treat Blog Task 40 only as a downstream reproduction fixture and implement the behavior upstream in Aegis without modifying Blog or changing enforcement mode.

**Details:**

Implement the correction in the Aegis source of truth, primarily `scripts/_aegis_installer.py`, and keep the packaged mirror `aegis_foundation/assets/scripts/_aegis_installer.py` byte-identical per `tests/meta_workflow_guard/test_assets_scripts_parity.py`. Audit the current pending-tracking path: `_pending_tracking_events`, `_pending_events_by_mode`, `_strict_pending_tracking_check`, `verify`, `closeout`, `next_action`, `doctor`, `enforcement_status`, and `_build_closeout_repair_guidance`. Introduce a single helper/classifier for pending-tracking state that distinguishes required strict events, advisory events, malformed queues, mixed required/advisory queues, missing/unknown provenance, and invalid event shape. Use that helper everywhere so status, verify, closeout, closeout_ready, doctor, and next-action guidance agree.

Required behavior: in advisory mode, advisory-only pending events remain in `.aegis/state/pending-tracking.json` as audit evidence, are counted and context-budget summarized, and do not make `aegis verify --strict`, `aegis closeout --dry-run`, or normal `aegis closeout` fail. Normal advisory delivery must not require `aegis repair --apply`, handoff repair ceremony, or manual pending queue draining. Strict enforcement must still fail closed when unresolved required tracking exists, the pending queue is malformed/invalid JSON or non-list, required and advisory state is mixed in a way that could hide required work, provenance is absent/unknown, or event mode cannot be trusted. Closeout dry-run must remain non-mutating: it may summarize advisory events and projected actions, but must not delete or rewrite pending tracking, current-work, reports, handoff, or work-tracking surfaces.

Preserve complete evidence: do not discard advisory events during verification or closeout. Add report fields such as `pending_tracking.summary`, `pending_tracking.advisory_preserved`, `pending_tracking.required_unresolved`, and `pending_tracking.queue_valid` or equivalent, with bounded event samples and exact counts. Ensure `aegis_foundation/output_budget.py` rendering keeps large advisory queues within the default budget while retaining exact cardinality metadata and artifact paths. Update guidance text that currently suggests `aegis repair --apply` for advisory pending re-entry so advisory-only state points to normal delivery/closeout, while strict re-entry with unresolved required or suspicious queues remains fail-closed and actionable.

Add documentation under `docs/aegis/` and the packaged asset copy under `aegis_foundation/assets/docs/aegis/` describing the root cause, the advisory pending-event lifecycle, why Blog Task 40 is only the downstream reproduction, and the safe Blog retry procedure. Explicitly state that this task does not modify the Blog repository and does not switch Blog/Aegis enforcement mode as part of the fix. Include guidance that advisory pending queues are audit residue to preserve and summarize, not a cleanup backlog to manually drain.

**Test Strategy:**

Add focused pytest coverage in `tests/meta_workflow_guard/test_aegis_installer.py` for advisory-only pending queues passing `verify(strict=True)`, `closeout(dry_run=True)`, and normal `closeout` while preserving the queue file and recording advisory counts/samples. Add negative tests proving strict/required pending events still fail `mutation.pending_tracking_empty`, malformed JSON or non-list queues fail closed, mixed required/advisory queues fail closed, and missing/unknown provenance fails closed. Assert dry-run closeout does not mutate pending tracking, current-work, reports, handoff, or work-tracking surfaces.

Add output-budget tests in `tests/claude_adapter/test_output_budget.py` using a large advisory pending fixture to prove one-screen default output preserves exact advisory counts and samples safely. Add replay/corpus coverage using `aegis_foundation.replay` or existing replay fixtures to prove advisory events remain retained in stored artifacts even when stdout is sampled. Add source/package parity checks through the existing asset parity suite and docs parity assertions for root-cause and Blog retry documentation. Add a downstream reproduction fixture for Blog Task 40 under `tests/fixtures/aegis/` and a test that reproduces the previous closeout/delivery failure against Aegis-only fixtures, without reading or modifying the Blog repository.

Run focused verification: `python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/claude_adapter/test_output_budget.py tests/meta_workflow_guard/test_assets_scripts_parity.py`, plus any new replay/documentation test files. Finish with `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`.
