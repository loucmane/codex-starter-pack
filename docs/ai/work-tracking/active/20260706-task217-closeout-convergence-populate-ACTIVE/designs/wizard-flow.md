# Task 217 — Closeout populate scope

## Decision

Implement the Task 217 populate step inside the existing Aegis closeout evaluator, not as a new wizard or a parallel repair command.

## Scope

- Populate only from already-logged `plan-step-implement` and `plan-step-verify` evidence rows.
- Require strict verification to pass, and require a green `.aegis/reports/verification-report.json` before emitting strict-verification evidence into handoff sections.
- Preserve `dry_run` as read-only: it may report `would_update` surfaces but must not write surfaces, closeout reports, or current-work state.
- Preserve operator-authored HANDOFF prose by repairing only closeout-owned semantic/evidence sections.
- Do not drain pending tracking inside closeout. A real pending event remains an independent closeout blocker; this is stricter than a risky auto-drain and preserves the Task 216 invariant.

## Implementation Shape

- Add surgical HANDOFF section helpers.
- Add a final-closeout populate phase that back-fills missing session/tracker/implementation/changelog progress entries when the evidence token is already present in plan rows and has an existing S:W:H:E source entry on another surface.
- Keep repair guidance visible on dry-run failures, so non-mutating preflight still explains the exact repair path.
- Mirror the live installer into the packaged asset copy under `aegis_foundation/assets/scripts/`.

## Verification

- Regression coverage rewrites the two Task 217 central closeout tests.
- New coverage proves path-lost evidence is populated on final closeout.
- Negative coverage proves pending tracking and strict verification failures are still the real blockers when no implementation/verification evidence exists.
