# Task 213 — Per-session hashed capsule A/B assignment (2026-06-11)

Spec §7's calendar-day A/B alternation and 2-week window are superseded (owner-approved
amendment, 2026-06-11): the experimental unit is the cold start, so assignment now
randomizes per session.

## Mechanism
- `brief_lib.capsule_assignment(root, session_id, env)` decides the arm. Precedence:
  `AEGIS_CAPSULE` env (owner override) > brief.json `inject: false` (hard off) >
  `"ab_assignment": "session-hash"` (sha256(session_id) parity, even → on) > static on.
  Paths without a session_id (CLI renders, `--check`) never randomize.
- `gate_lib.session_start_hook` parses the payload first, then stamps `session_begin`
  with `capsule_injected` AND `assignment` mode (`session-hash` / `env-override` /
  `brief-inject-false` / `static-on`).
- `aegis ab [--min-n N] [--json]` counts genuine cold starts per arm — only
  `source == "startup"` (resume/clear/compact excluded) AND `cwd` inside the target repo
  (replay-worktree/hook-capture sessions share the ledger via the git common dir and must
  not count). Default stopping rule: 15 per arm.
- Codex `.aegis/brief.json` opts in with `"ab_assignment": "session-hash"`.
- `replay_coldstart.run_live_ab` now sets `AEGIS_CAPSULE=on` explicitly for the capsule
  arm (an unset env would randomize under session-hash).

## Known accepted biases (documented in spec §7)
Carryover via handoff files attenuates the delta toward zero (harsher on the capsule);
arms are unblinded.

Tests: tests/claude_adapter/test_ab_assignment.py (15). Mirrors (assets/live) kept
byte-identical for gate_lib.py and brief_lib.py.
