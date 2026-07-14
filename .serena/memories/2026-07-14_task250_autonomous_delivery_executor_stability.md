# Task 250 — Evidence-gated autonomous delivery executor stability

## Current state

- Task 250 is in terminal closeout on `feat/task-250-autonomous-delivery-closeout`.
- Final remediation PR #279 merged normally as `89ea3a4538e659992b5685b3cc3b3b8116a76c39`.
- Ordinary canary PR #278 autonomously merged through trusted run `29323250166` as `c3daa484932292bc25f0f58d51fb96e63c0200f4`; exact-merge-SHA CI and guards passed.
- PR #276 is superseded: its durable Task 249 terminal state is preserved, while its stale Taskmaster/session pointers must not be merged. The one omitted archived verification report is restored in Task 250 closeout.

## Selected design

- Keep default evaluator `blocked`/`unstable` results non-authorizing.
- Permit executor-phase `allow` only when complete exact-head check and legacy-status inventories prove every independent signal green and identify exactly the current trusted GitHub Actions executor run as the sole non-green check.
- Bind the exception to check name, GitHub App slug, repository Actions URL, current run ID, non-completed status, and exact head SHA.
- Recollect all volatile PR/workflow/check/status/review evidence and re-evaluate immediately before the normal protected SHA-pinned squash merge.
- Preserve attended-path, same-repository, exact-head, review-thread, complete-inventory, protected-path, and required-workflow gates.

## Evidence so far

- Sanitized PR #276 telemetry fixture added.
- Focused adversarial policy/workflow suite: 72 passed.
- Wider affected source/guard/Codex/policy suite: 388 passed.
- Ruff lint/format, source/package policy parity, Taskmaster health, dependency validation, plan sync, and template drift pass.
- Task 249 is `done`; its 12 terminal files match signed closeout commit `955385929fc0d96285c741bdfe2c6e5e0b97dea6` byte-for-byte and are included through supported archival so Task 250 is the sole ACTIVE work authority.

## Next steps

1. Run terminal readiness, Taskmaster health, work-tracking audit, plan sync, source guard, strict Aegis verification, witness, and closeout.
2. Close PR #276 as superseded after committing the missing durable report; do not merge its stale projections.
3. Deliver and merge Task 250 closeout, synchronize `main`, and preserve unrelated local drift.
4. Begin the dedicated upstream advisory-pending/closeout correction reproduced by Blog Task 40.
