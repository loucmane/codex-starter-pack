# Findings

- 2026-06-15 — `_doctor_repair_actions` mixes a cosmetic, ever-present action
  (`normalize_plan_table`, emitted even for a healthy kickoff plan table) with substantive drift
  actions. This is the root cause of two design traps: (a) "any action present" over-fires on
  every clean kickoff; (b) the cosmetic action masks manual-only drift in the safe/manual split.
  Both handled by gating on doctor "repairable" severity AND filtering to substantive actions.
- 2026-06-15 — `doctor()` calls `next_action()` (~line 8570), so `next_action` must never call
  `doctor()`. Detection reuses the lighter `_doctor_repair_actions` + `_classify_doctor_state`.
- 2026-06-15 — A genuinely malformed plan table and a healthy table both emit only
  `normalize_plan_table`; they are indistinguishable by the action list. A malformed table can
  reach "repairable" severity, but since its sole action is the cosmetic one, TM 225 lets it
  fall through to the ladder (the pre-TM-225 behavior) rather than surfacing a repair state —
  `_parse_plan_rows` handles the table downstream as before.
- 2026-06-15 — Adversarial review (5-agent refute panel) surfaced Finding #2 (major): the
  `substantive or repair_actions` fallback resurrected the cosmetic action and swallowed a real
  branch/task-alignment failure. Reproduced end-to-end (rename branch off task id → previously
  `safe_repair_available`; now correctly `scope_required`). Fixed + regression-tested before
  commit. Also #3 (count divergence, accepted) and #1 (double-compute, deferred).
