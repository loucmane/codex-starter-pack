# Decisions

- 2026-06-15 — Detect repairability via `_doctor_repair_actions` + the canonical
  `_classify_doctor_state` severity, NOT by calling `doctor()`. `doctor()` calls `next_action()`,
  so calling it back would infinite-recurse. Factored `_repair_plan_split` so `doctor` and
  `next_action` classify safe/manual by one predicate.
- 2026-06-15 — Trigger the repair state on doctor's **"repairable" severity AND a substantive
  (non-`normalize_plan_table`) repair action**, not on mere presence of any repair action. A
  healthy kickoff target always emits a cosmetic `normalize_plan_table` (safe) action;
  triggering on "any action" routed every clean kickoff to `safe_repair_available` instead of
  `scope_required` (empirically confirmed). Deviates from the design workflow's "any safe
  action" gate.
- 2026-06-15 — Injection point: AFTER `workflow_scaffold_incomplete`, BEFORE the
  scope/implement/verify/closeout ladder — NOT the design's line-2941 (before
  observation/closeout/scaffold). At 2941 a normal post-closeout task (work-tracking still
  ACTIVE, exactly like 189 pre-archive) would route to `safe_repair_available` instead of
  delivery guidance, and `workflow_scaffold_incomplete` would be subsumed. The chosen point
  keeps terminal/observation/scaffold states authoritative and preempts only the active-work
  ladder.
- 2026-06-15 — **Adversarial-review Finding #2 (major, fixed before commit):** the first cut
  used `substantive or repair_actions` as a fallback, which resurrected the cosmetic
  `normalize_plan_table` when it was the only action left. A repairable-severity failure with no
  substantive repair action (branch renamed off the task id → `branch_task_alignment` fails;
  also a cosmetic-only plan-table normalization) was misrouted to `safe_repair_available`;
  `repair --apply` then "fixed" only the cosmetic action and silently swallowed the real
  failure. Fix: route to a repair state ONLY when `substantive_repairs` is non-empty; otherwise
  fall through to the ladder (the pre-TM-225 behavior). Regression test added
  (`test_repairable_severity_without_substantive_action_falls_through`).
- 2026-06-15 — **Finding #3 (minor, accepted):** `next_action.details.repair_plan` counts the
  substantive actions it routes on (excludes `normalize_plan_table`); `doctor.repair_plan`
  counts the full plan (includes it). Intentional: next_action reports routing-relevant drift.
  The two surfaces already use different taxonomies; not reconciled to avoid changing doctor's
  public output/tests.
- 2026-06-15 — **Finding #1 (minor, deferred):** when `doctor()` runs on an active task it
  computes the strict-check + repair-action battery, then calls `next_action()` which recomputes
  it (~2.4ms). next_action is reached only at command cadence (aegis next/status/doctor), never
  from PreToolUse/PostToolUse/Stop hooks, so this is negligible. A future dedupe (pass
  precomputed checks/actions into next_action) is possible but adds signature surface; deferred.
- 2026-06-15 — Did NOT mirror the two states into `_classify_doctor_state` (doctor's
  `current_state`). doctor's severity taxonomy intentionally differs from next_action's phase
  taxonomy and predates TM 225.
