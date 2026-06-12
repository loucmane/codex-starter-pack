# Task 213 — Per-session hashed A/B assignment: design scope

Date: 2026-06-11. Owner-approved amendment to `docs/aegis/AEGIS_CAPSULE_SPEC.md` §7.

## Problem
The §7 falsifier assigned capsule on/off by calendar day and waited a fixed 2-week
window. The experimental unit is the cold start (the capsule only acts at SessionStart),
so calendar-day assignment clusters sessions into noisy units, bakes in day-of-week
confounds, and the window is just a sample-size proxy.

## Decision
1. **Assignment**: `"ab_assignment": "session-hash"` in `.aegis/brief.json` →
   `brief_lib.capsule_assignment()` picks the arm from sha256(session_id) parity
   (even → on). Precedence: `AEGIS_CAPSULE` env (owner override) > `inject: false`
   (hard off) > session-hash > static on. No session_id (CLI renders, `--check`) →
   never randomize.
2. **Instrumentation**: `session_begin` stamps gain an `assignment` mode field so the
   analysis can distinguish hashed arms from overrides.
3. **Stopping rule**: fixed-n replaces fixed-time — `aegis ab [--min-n N]` counts
   genuine cold starts per arm (source == `startup` only; sessions begun outside the
   target repo excluded — replay worktrees and hook captures share the ledger via the
   git common dir). Default 15/arm.
4. **Harness pin**: `run_live_ab` sets `AEGIS_CAPSULE=on` for the capsule arm; an unset
   env would randomize under session-hash.

## Accepted biases (documented in spec §7)
Carryover via handoff files attenuates the delta toward zero (harsher on the capsule);
arms are unblinded.

## Boundary
No changes to Codex-owned paths. HP-Coach adoption is a one-line brief.json addition
(`ab_assignment`) noted for the upgrade prompt; that repo is read-only from this task.
