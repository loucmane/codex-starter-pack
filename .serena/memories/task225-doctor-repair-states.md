# Task 225 — doctor repair states in `aegis next`

**Status:** done (2026-06-15), branch `feat/task-225-doctor-repair-states`. Closes TM 189
residual #2. Built with design + adversarial-review workflows.

## What shipped
`next_action` now surfaces doctor-derived repair states between the scaffold check and the
scope/implement/verify/closeout ladder.

- `scripts/_aegis_installer.py`:
  - `_repair_plan_split(repair_actions) -> (safe, manual)` — factored from `doctor()`'s inline
    split (was ~8551); `doctor()` reuses it (single-sourced safe/manual classify).
  - `next_action` repair branch (search "TM 225"):
    - read-only, recursion-safe: uses `_doctor_repair_actions` + `_classify_doctor_state`,
      NEVER `doctor()` (doctor calls next_action → would recurse).
    - trigger = doctor "repairable" severity AND a **substantive** repair action
      (non-`normalize_plan_table`). `normalize_plan_table` is cosmetic + ever-present (fires on
      healthy kickoff tables), so it's filtered.
    - `safe_repair_available` (substantive safe action) → continue = review then
      `aegis repair --apply`. `manual_review_repair` (safe==0, manual≥1) → surface only, never
      auto-applied, no `--apply` in repairs.
  - `CONTINUATION_BRIEF_BY_STATE` entries for both.
- `aegis_foundation/assets/scripts/_aegis_installer.py` re-mirrored byte-identical (TM 219).
- `tests/meta_workflow_guard/test_repair_next_states.py` (10 tests).

## Key calls (validated empirically)
- Deviated from the design workflow: injection AFTER scaffold (not its line-2941, which would
  regress post-closeout/observation/scaffold), and severity+substantive gate (its "any safe
  action" gate false-positived on every clean kickoff).
- **Adversarial review caught a major bug:** an early `substantive or repair_actions` fallback
  resurrected the cosmetic action when it was the only one left, so a repairable failure with no
  substantive repair action (branch renamed off task id → `branch_task_alignment` fails; or a
  cosmetic-only plan-table normalization) misrouted to `safe_repair_available` and
  `repair --apply` swallowed the real failure. Fix: only enter a repair state when
  `substantive_repairs` is non-empty; else fall through (pre-TM-225 behavior). Regression-tested.

## Test induction
safe drift: delete `.aegis/bin/aegis` (restore_managed_file). manual drift: replace it with a
directory (managed.manual, safe=False). pending precedence: write events to pending-tracking.

Verification: focused 20 passed; installer/MCP/replay/parity 175; full suite green.
Deferred (DECISIONS): #1 doctor→next_action double-compute; #3 count divergence.
See [[task189-continuation-brief]].
