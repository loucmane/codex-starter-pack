# Task 225 — doctor repair states in `aegis next` (design)

> Filename is the generic kickoff-scaffold name; this is the Task 225 design artifact,
> referenced by `plan-step-scope`. Residual #2 of TM 189.

## Problem
TM 189 shipped the per-state continuation brief but deferred one residual: `next_action`
never surfaced the **doctor-derived repair classification** (safe-repair vs manual-review).
So when an installed workflow had fixable drift, `aegis next` would advise "log scope / run
closeout" on top of the drift instead of "repair first".

## Design (single-sourced, severity-gated, recursion-safe)
- **`_repair_plan_split(repair_actions) -> (safe, manual)`**: factored from the inline split in
  `doctor()` (was lines 8551-8552). `safe` = actions with `safe is True` (auto-applyable by
  `aegis repair --apply`); `manual` = everything else. `doctor()` now reuses it, so both
  surfaces classify by exactly one predicate.
- **`next_action` repair branch**, injected **after** `workflow_scaffold_incomplete` and
  **before** the scope/implement/verify/closeout ladder:
  - Detection is **read-only and recursion-safe**: it calls `_doctor_repair_actions` directly,
    NOT `doctor()` (doctor() calls next_action() at ~8570 — calling it back would recurse).
  - **Trigger = doctor's own "repairable" severity**, computed by reusing the canonical
    `_classify_doctor_state(...)`. This is the load-bearing correctness choice: a *healthy*
    kickoff target still emits a cosmetic `normalize_plan_table` (safe) action, so gating on
    "any repair action present" (the original design) would route **every fresh kickoff** to
    `safe_repair_available` instead of `scope_required`. Gating on severity excludes that.
  - **`normalize_plan_table` is excluded from the safe/manual split** (it is cosmetic and
    ever-present from kickoff output). Without this, a manual-only drift would be misclassified
    `safe_repair_available` and `repair --apply` would claim a fix it did not make.
  - `safe_repair_available` when there is a substantive safe action; otherwise
    `manual_review_repair` (safe==0, manual>=1).

## States + briefs
- `safe_repair_available` — continue = review the plan, then apply only the safe repairs with
  `aegis repair --apply` after surfacing the plan. `apply_command="aegis repair --apply"`.
- `manual_review_repair` — continue = surface the plan only; manual-review actions need an
  explicit human decision and are never auto-applied. `apply_command=None`; no `--apply` in
  copyable_repairs.

## Precedence (verified by tests)
`pending_tracking` ▶ outranks repair (repair --apply hard-refuses while pending exists) ▶
repair outranks the scope/implement/verify/closeout ladder. Terminal/observation/scaffold
states are checked earlier and keep their behavior (no regression).

## Deviations from the design workflow (wf_a0f8fcab)
1. Injection point moved from line 2941 (before observation/closeout/scaffold) to after the
   scaffold check — 2941 would have made a normal post-closeout task (work-tracking still
   ACTIVE, exactly like 189 pre-archive) route to `safe_repair_available` instead of delivery
   guidance, and would have subsumed `workflow_scaffold_incomplete`.
2. Added the severity gate + `normalize_plan_table` exclusion — the design's "any safe action"
   gate produced a false positive on every clean kickoff (empirically confirmed).

## Scope boundary
`doctor`'s `current_state` taxonomy (severity-oriented: installed_with_failures /
in_progress_ready) intentionally differs from `next_action`'s phase taxonomy and predates
TM 225; not mirrored here.
