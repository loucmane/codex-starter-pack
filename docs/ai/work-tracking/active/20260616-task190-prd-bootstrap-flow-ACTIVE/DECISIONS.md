# Decisions

- 2026-06-16 — A zero-task ledger is reclassified from `invalid` to a new `empty` Taskmaster
  state. An initialized-but-taskless ledger is a fresh-project bootstrap phase, not corruption;
  routing it to "repair Taskmaster" was wrong. Genuine corruption (bad JSON, missing/malformed
  container, invalid ids/deps) stays `invalid`.
- 2026-06-16 — PRD detection (`_prd_state`) considers ONLY canonical `.taskmaster/docs/prd.txt`
  and `prd.md`. A generic `*.md` glob would false-positive on unrelated docs (this repo has
  `reconcile-enablement-gate-backlog-amendment.md`). Non-canonical names/casing/subdirs are a
  deliberate conservative miss (documented in the docstring + matches the Taskmaster lowercase
  convention) — they still steer toward PRD authoring, never crash, never fabricate an id.
- 2026-06-16 — The example template is excluded by content-equality to the LIVE
  `example_prd.txt` + placeholder markers, never by a hard-coded hash (survives template drift).
  PRD read is bounded (1MB) and binary-skipping (NUL bytes).
- 2026-06-16 — `prd_parsed_tasks_pending` vs `first_task_ready` discriminator = PRD presence
  (the design's "expansion gate" had no clean on-disk signal). valid+none-started+PRD = still in
  the parsed-tasks review phase; valid+none-started+no-PRD = a curated ledger ready for first
  kickoff. Both bind only a real ledger task.
- 2026-06-16 — `no_taskmaster` (absent) preserves `installed_no_current_work`'s local-work path
  (`aegis start`, including `suggested_mcp_call=aegis.start`) AND adds the task-driven path
  (`task-master init` + PRD), surfacing an already-authored PRD when present. The old
  `installed_no_current_work` return in `next_action` is now an unreachable defensive fallthrough
  (its brief + the live `_classify_doctor_state` usage stay).
- 2026-06-16 — `started` predicate counts only in-progress/done/completed. An all-terminal
  ledger (cancelled/deferred/blocked only) routes to first_task_ready; this is safe (Taskmaster
  authority, no fabricated id) and the wording defers to `task-master next` rather than promising
  an actionable task. Documented in a code comment.
- 2026-06-16 — Adversarial review (5 agents) verdict: **ship**, no must-fix. Folded in the cheap
  should-consider items (bounded/binary-safe PRD read, no_taskmaster surfaces an existing PRD,
  softened first_task_ready wording, defensive-fallthrough annotation, tighter test helper).
  Accepted/deferred as documented above: non-canonical PRD names (conservative miss), placeholder
  false-exclude (very low likelihood, safe downgrade).
- 2026-07-03 — Capsule evaluation gate is reframed for the owner deployment: resume-time drift
  refresh is the primary success criterion; cold-start A/B remains a secondary track for
  headless/new-user/cold-start-heavy deployments. PR-3 narration and PR-4 retirement are
  dogfood-gated follow-ons, not automatic next steps.
