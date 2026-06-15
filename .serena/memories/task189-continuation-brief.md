# Task 189 — agent-ready continuation brief on `aegis next`

**Status:** done (2026-06-15), branch `feat/task-189-continuation-brief`. Builds on TM 188
(continuation contract). Residual #2 deferred to **TM 225**.

## What shipped (residuals #1 + #3)
`aegis next` now attaches a per-state `continuation_brief` to every payload.

- `scripts/_aegis_installer.py`:
  - `_CONTINUATION_UNIVERSAL_STOP` — halt conditions on every brief (readiness BLOCKED,
    pending tracking unlogged, protected/owned path, confirmation boundary).
  - `CONTINUATION_BRIEF_BY_STATE` — table keyed by `next_action`'s `state`; entries give
    continue_means / next_safe_action / confirmation_boundary / artifact_policy. Includes the
    post-closeout delivery states (`delivery_pending`, `delivery_unknown`) encoded as
    confirmation-gated.
  - `_continuation_brief(state, phase, *, current_task_authority=None)` — builds the read-only
    brief (read_only always True).
  - `_workflow_guidance_payload(..., current_task_authority=None)` — emits
    `payload["continuation_brief"]`.
  - `next_action` — computes `current_task_authority` once at the start of the current-work
    region (`taskmaster:<id>` / `observation-session` / `local-tracked-work`) and threads it
    into every active-work state so a bare "continue" can't be read as "switch tasks".
  - `format_next_summary(payload)` — concise read-only CLI rendering.
- `aegis_foundation/cli.py`: `aegis next` defaults to the summary; `--json` emits the payload.
  Safe because no runtime parses `aegis next` stdout (MCP + codex-task call `next_action()`).
- `aegis_foundation/assets/scripts/_aegis_installer.py`: re-mirrored byte-identical (TM 219).
- `tests/meta_workflow_guard/test_continuation_brief.py`: invariants — brief on every state,
  read_only, never auto-merge/push (merge only as approval-gated boundary), delivery
  confirmation-gated, authority threads end-to-end, CLI summary/--json.

## Key design calls
- Derive brief from `state` via the table (no per-call-site edits across ~16 callers).
- Delivery: do NOT lift dynamic `push_branch`/`open_pr` into next_safe_action — confirmation-gate.
- Verified end-to-end on a temp installed target (codex repo itself is `not_installed` — it's
  the foundation source, no self-manifest).

## Gotcha
The Codex kickoff wizard re-introduced `task-master generate` churn in tasks.json (every id
int→string, 223 lines). Fix: restore HEAD format, surgically flip only the status fields.
`task_188.md` left at a pre-existing pending-vs-done skew (generate-one blocked while 189 dirty).

Verification: full suite 1678 passed / 4 skipped; focused 24 passed.
