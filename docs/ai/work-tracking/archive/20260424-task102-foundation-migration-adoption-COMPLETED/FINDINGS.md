# Findings

- 2026-04-24 — Task 102 should not add new core behavior; the needed work is to document the contract, bootstrap path, and compatibility findings as an adoption playbook.
- 2026-04-24 — The documentation needs to speak to two different audiences: brand-new repositories and existing repositories that already have workflow or template state to reconcile.
- 2026-04-24 — The cleanest canonical home for migration/adoption guidance is a dedicated engine validation module; the older enforcement integration guide is too specific to reuse for this purpose.
- 2026-04-24 — Adding a new engine module requires updating the verifier, registry, and metadata inventory in the same change to avoid repeating engine-surface drift.
- 2026-04-25 — Delayed closeout exposed an enforcement mismatch: the session-end protocol clears active pointers, but guard/audit still treated missing `sessions/current` or `plans/current` as an error even when `sessions/state.json.current` was `null` and no active work-tracking folder remained.
