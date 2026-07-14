# Advisory Pending-Event Lifecycle

## Purpose

Aegis hooks retain pending mutation events as audit evidence. The event's recorded enforcement mode determines whether it represents required workflow work:

- an explicit `mode: advisory` event is passive evidence;
- an explicit `mode: strict` event is required tracking;
- malformed, mixed, missing-provenance, or unknown-mode state is untrusted and fails closed.

Advisory-only evidence is preserved and summarized. It does not block strict verification, delivery witness preparation, or closeout. Do not drain advisory pending events as routine ceremony, and do not run generic repair merely to make their count reach zero.

## Root Cause

Before Task 251, the hook runtime correctly stamped advisory events, but downstream commands ignored the stamp:

- strict verification failed every non-empty queue;
- closeout independently failed every non-empty queue;
- `aegis next` told agents to log advisory events one by one;
- repair guidance turned passive evidence into a cleanup backlog;
- the legacy queue reader could filter malformed entries and make untrusted state look empty.

Blog Task 40 exposed the contradiction with 97 advisory events: product and standard governance checks were complete, but `aegis verify --strict` and closeout still demanded an empty queue.

## Canonical Classification

The complete queue remains at `.aegis/state/pending-tracking.json`. Agent-facing reports contain exact counts, a bounded sample, and the artifact path.

| Classification | Meaning | Delivery |
| --- | --- | --- |
| `absent` | Queue file does not exist | allow |
| `empty` | Valid queue with no events | allow |
| `advisory_only` | Every event explicitly records advisory provenance | allow and preserve |
| `required_only` | One or more explicit strict events | fail closed |
| `mixed` | Advisory and strict events coexist | fail closed until strict events are logged |
| `unknown` | Event shape or provenance is missing or unsupported | fail closed for manual inspection |
| `malformed` | Queue JSON or envelope is invalid | fail closed for manual inspection |

The current enforcement mode does not rewrite historical provenance. Advisory-only residue remains passive after strict re-entry; a new mutation made under strict mode is recorded as strict and blocks subsequent strict mutations until reconciled.

## Verification and Closeout

`aegis verify --strict` and closeout use the same pending-state classification.

- Advisory-only queues pass the pending-tracking gate.
- The queue is not deleted, rewritten, or drained.
- Closeout dry-run remains non-mutating.
- Required, mixed, unknown, and malformed queues fail closed.
- Repair guidance is emitted only for required strict events. Untrusted queues point to the canonical artifact and read-only doctor output rather than inventing a mutation.

The legacy gate identifier `mutation.pending_tracking_empty` remains for compatibility. Its message and structured details now state whether pending evidence is delivery-safe; the identifier no longer means every allowed queue must literally be absent.

## Safe Blog Task 40 Retry

Blog is a downstream consumer and was not modified while the upstream correction was developed. After the upstream Task 251 PR is merged, use a separate attended managed-runtime refresh.

1. Confirm the stable upstream source commit supplied in the Task 251 handoff.
2. In `/home/loucmane/dev/blog`, confirm Task 40 is still in progress on `feat/task-40-migrate-react-next-framework-build-system` and preserve all existing unstaged rollout and product evidence.
3. Record `git status --short`, the enforcement state, and the pending queue digest/count. Keep enforcement advisory.
4. Preview the supported update:

   `./.aegis/bin/aegis update --target-dir .`

5. Stop if the plan reports a conflict, unsafe overwrite, manual-review path, unrelated product path, or any change under `.codex/`.
6. Only after the owner approves that attended rollout, apply it:

   `./.aegis/bin/aegis update --target-dir . --apply`

7. Run:

   `./.aegis/bin/aegis verify --target-dir . --strict`

8. Confirm `mutation.pending_tracking_empty` passes with classification `advisory_only`, the exact advisory count is reported, and the canonical queue remains present.
9. Run closeout preflight only:

   `./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff`

10. Confirm the preflight does not mutate the queue, current-work state, reports, handoff, Taskmaster, or product files. Do not run final Task 40 closeout until separately authorized.

Do not run `aegis repair --apply`, do not manually drain or individually log the advisory queue, do not switch enforcement to strict, and do not hot-patch Blog's managed Aegis assets.

## Scope Boundary

This lifecycle correction does not retire legacy sessions, plans, trackers, handoff, or S:W:H:E projections. It makes passive capsule/ledger evidence and the legacy scaffolding coexist without forcing advisory evidence through strict per-mutation ceremony.

Gas Town migration and Taskmaster retirement are separate program decisions. They are not part of this correction and must not begin until the owner explicitly authorizes them at a sensible stopping point.
