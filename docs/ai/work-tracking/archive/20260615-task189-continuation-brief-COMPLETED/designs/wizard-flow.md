# Task 189 — Continuation brief design

> Filename is the generic kickoff-scaffold name; this file is the Task 189 design artifact
> (the brief that `aegis next` attaches), referenced by `plan-step-scope`.

## Problem
TM 188 installed the cross-agent continuation *contract* as a document (`.aegis/contract.md`
plus AGENTS.md/CLAUDE.md summaries). A document only helps an agent that reads it. The running
tool — `aegis next` — said *what* the next required action was, but not what a bare "continue"
**authorises** in the current state. An agent reading `aegis next` could still over-read
"continue" as "do the whole task" or "switch to another task".

## Goal (this PR — residuals #1 and #3)
Make `aegis next` speak the contract per state:
1. Every `next_action` payload carries a `continuation_brief`.
2. A concise human rendering (`format_next_summary`) + a `--json` escape hatch on the CLI.

Deferred to a follow-up (residual #2): surfacing the doctor-derived safe-repair vs
manual-review split as distinct `next_action` states. Filed as **TM 225**.

## Design
- `CONTINUATION_BRIEF_BY_STATE`: a table keyed by `next_action`'s `state`. Each entry gives
  `continue_means`, `next_safe_action`, optional `confirmation_boundary` / `artifact_policy`.
  Keying by state means every state gets a coherent brief with **no per-call-site edits** to
  the ~16 `_workflow_guidance_payload` callers — the brief is derived from the `state` arg.
- `_continuation_brief(state, phase, *, current_task_authority=None)` builds the dict, filling
  unset fields from universal defaults and always appending `_CONTINUATION_UNIVERSAL_STOP`
  (readiness BLOCKED, unlogged pending tracking, protected/owned path, confirmation boundary).
  `read_only` is always `True` — the brief is proof that `aegis next` grants no mutation
  authority.
- `_workflow_guidance_payload` gains `current_task_authority` and emits
  `payload["continuation_brief"]`. `next_action` computes the authority once where the
  current-work region begins (`taskmaster:<id>` / `observation-session` / `local-tracked-work`)
  and threads it into every active-work state, so a bare "continue" can't be read as "switch
  tasks".

## Safety invariants (locked by tests)
- The brief never names merge/push/force-push as an auto action; merge is only ever a
  confirmation boundary that requires explicit approval/confirmation.
- Delivery states (`delivery_pending`, `delivery_unknown`, `closeout_passed`) are
  confirmation-gated, not auto-deliver. `delivery_*` deliberately does **not** lift the
  dynamic `push_branch`/`open_pr` action into `next_safe_action` (that would present a
  boundary-crossing step as "safe").
- The closeout brief mirrors the contract's "non-dry-run closeout needs explicit close-out
  intent" wording; `AEGIS_CONTINUATION_SUMMARY` ("exactly ONE safe step") is the upstream
  source of truth shared with TM 188.

## CLI
`aegis next` now prints the concise summary by default (state, authority, what "continue"
means, the one safe action, confirm-first/stop-if lines, read-only disclaimer); `--json`
emits the full payload. No runtime consumer parses `aegis next` stdout as JSON (the MCP server
and `codex-task` call `next_action()` in-process), so the default change is safe.

## Parity
`scripts/_aegis_installer.py` mirrored byte-for-byte to
`aegis_foundation/assets/scripts/_aegis_installer.py` (TM 219 parity test). `aegis_foundation/cli.py`
ships directly from the package — no mirror.
