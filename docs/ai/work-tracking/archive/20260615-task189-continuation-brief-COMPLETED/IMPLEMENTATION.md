# Task 189 Add agent-ready continuation brief to aegis next – Implementation Notes

## Scope shipped (residuals #1 + #3)
The continuation brief that TM 188's contract document describes, now emitted by the running
`aegis next` tool. Residual #2 (doctor-derived safe-repair vs manual-review states) deferred to
**TM 225**.

## Changes
- `scripts/_aegis_installer.py`
  - `_CONTINUATION_UNIVERSAL_STOP`: the always-applied halt conditions.
  - `CONTINUATION_BRIEF_BY_STATE`: per-state table (continue_means / next_safe_action /
    confirmation_boundary / artifact_policy), including the post-closeout delivery states
    (`delivery_pending`, `delivery_unknown`) encoded as confirmation-gated.
  - `_continuation_brief(state, phase, *, current_task_authority=None)`: builds the read-only
    brief from the table + universal defaults.
  - `_workflow_guidance_payload(..., current_task_authority=None)`: now attaches
    `continuation_brief` to every payload.
  - `next_action`: computes `current_task_authority` once at the start of the current-work
    region (`taskmaster:<id>` / `observation-session` / `local-tracked-work`) and threads it
    into every active-work state (pending_tracking, observation_*, scope, implementation,
    verification, strict-verify, closeout, delivery, complete).
  - `format_next_summary(payload)`: concise, read-only human rendering led by the brief.
- `aegis_foundation/cli.py`
  - `handle_next`: defaults to `format_next_summary`; `--json` emits the full payload.
  - `next` subparser: added `--json`.
- `aegis_foundation/assets/scripts/_aegis_installer.py`: re-mirrored byte-identical (parity).
- `tests/meta_workflow_guard/test_continuation_brief.py`: new suite.

## Verification
See `reports/` for the captured test run.
