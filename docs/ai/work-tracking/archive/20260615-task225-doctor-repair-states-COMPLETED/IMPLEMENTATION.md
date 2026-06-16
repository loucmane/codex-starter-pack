# Task 225 Surface doctor safe-repair vs manual-review states in aegis next – Implementation Notes

## Changes
- `scripts/_aegis_installer.py`
  - `_repair_plan_split(repair_actions)` — factored from `doctor()`'s inline safe/manual split;
    `doctor()` now reuses it (single-sourced classification).
  - `next_action` — new repair branch after `workflow_scaffold_incomplete`, before the
    scope/implement/verify/closeout ladder. Read-only detection via `_doctor_repair_actions`
    (NOT `doctor()` — avoids recursion). Trigger gated on `_classify_doctor_state(...)`
    severity `== "repairable"` (not mere action presence). Excludes cosmetic
    `normalize_plan_table` from the safe/manual split. Emits `safe_repair_available`
    (substantive safe action present) or `manual_review_repair` (safe==0, manual>=1).
  - `CONTINUATION_BRIEF_BY_STATE` — entries for `safe_repair_available` and
    `manual_review_repair` (manual is confirmation-gated; neither names merge/push).
- `aegis_foundation/assets/scripts/_aegis_installer.py` — re-mirrored byte-identical (TM 219).
- `tests/meta_workflow_guard/test_repair_next_states.py` — new suite (9 tests).

## Verification
- New suite + continuation-brief suite: 19 passed. Installer/MCP/replay: 168 passed (no
  regressions). Full suite: 1687 passed / 4 skipped. Evidence under `reports/`.

## Key decisions / deviations
See `designs/wizard-flow.md` and DECISIONS.md: severity gate + normalize_plan_table exclusion
(the design workflow's "any safe action" gate false-positived on every clean kickoff); injection
after scaffold (the design's line-2941 point regressed post-closeout/observation/scaffold).
