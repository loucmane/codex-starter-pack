# Task 225 Surface doctor safe-repair vs manual-review states in aegis next – Handoff Summary

## Current State
- TM 225 complete (residual #2 of TM 189). `next_action` now surfaces two repair states between
  the scaffold check and the scope/implement/verify/closeout ladder:
  - `safe_repair_available` — substantive safe drift; continue = review plan then
    `aegis repair --apply`.
  - `manual_review_repair` — substantive non-safe drift; surface plan only, never auto-applied.
- Detection is read-only and recursion-safe (`_doctor_repair_actions` + `_classify_doctor_state`
  severity, never `doctor()`), gated on doctor "repairable" severity AND a substantive
  (non-cosmetic) repair action. `_repair_plan_split` single-sources the safe/manual classify.
- Two `CONTINUATION_BRIEF_BY_STATE` entries; assets installer re-mirrored byte-identical.
- Adversarial review (5-agent) found one major bug (cosmetic-action resurrection swallowing a
  real failure) — fixed + regression-tested before commit.
- Verification: focused 20 passed; installer/MCP/replay/parity 175 passed; full suite green
  (see reports/). New suite: `tests/meta_workflow_guard/test_repair_next_states.py`.

## Next Steps
- Push branch `feat/task-225-doctor-repair-states`, open PR, merge on owner approval.
- After merge + branch cleanup: archive this folder (rides the next kickoff).

## Deferred (documented in DECISIONS)
- Finding #1: dedupe the doctor→next_action double battery computation (perf nicety).
- Finding #3: next_action vs doctor repair_plan count divergence (intentional; accepted).
- TM 189 residual #2 is now closed by this task.
