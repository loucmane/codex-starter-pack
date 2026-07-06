# Task 190 Support fresh-project PRD bootstrap continuation flow – Changelog

- 2026-06-16 14:32 CEST — Initialized active work-tracking folder.
- 2026-06-16 — Added 5 fresh-project bootstrap states to `aegis next` (no_taskmaster,
  taskmaster_empty, prd_available_not_parsed, prd_parsed_tasks_pending, first_task_ready) with
  briefs; new `empty` Taskmaster state (split from invalid); read-only `_prd_state` PRD
  detection; assets re-mirrored; new test_prd_bootstrap_states.py + 4 updated tests. Design +
  adversarial-review workflows (verdict ship); polish folded in. Full suite 1699 passed.
- 2026-07-03 — Added capsule resume-drift decision record, updated AEGIS capsule/program docs,
  and refreshed Taskmaster roadmap tasks 208/210 so PR-3/PR-4 are gated on real resume-drift
  evidence instead of the owner workflow waiting on cold-start A/B.
- 2026-07-06 13:04 CEST — Archived active work-tracking folder.
