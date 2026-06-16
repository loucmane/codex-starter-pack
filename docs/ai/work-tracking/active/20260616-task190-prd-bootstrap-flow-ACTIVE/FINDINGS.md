# Findings

- 2026-06-16 — Scope reconciliation: `_taskmaster_state` returned only absent/invalid/valid, and
  in `next_action` the `absent` case collapsed into `installed_no_current_work` ("start local
  work") while an EMPTY ledger returned `invalid` (`empty_taskmaster_tasks`) → routed to
  `installed_taskmaster_invalid` ("repair Taskmaster"). No PRD awareness existed. So the
  fresh-project bootstrap had no dedicated guidance — TM 190 is real and well-scoped.
- 2026-06-16 — PRD path conventions: real PRD at `.taskmaster/docs/prd.txt`; shipped example at
  `.taskmaster/templates/example_prd.txt`. Detection must exclude the template (a user copying it
  to docs/prd.txt is the critical false-positive) without a hard-coded hash.
- 2026-06-16 — `prd_parsed_tasks_pending` vs `first_task_ready` has no clean on-disk "expansion
  gate" signal; PRD-presence is the concrete discriminator used.
- 2026-06-16 — Behavior change has real (legitimate) test impact: 4 existing tests asserted the
  old routing and were updated to the new correct states; the empty-ledger case was removed from
  the invalid parametrize. Verified the `installed_taskmaster_present` test still holds (its
  ledger has a `done` task → `started`).
- 2026-06-16 — Adversarial review (5-agent refute panel) verdict **ship**, zero must-fix, no
  safety regressions. Surfaced minor guidance/test-strength gaps (all-terminal ledger wording,
  absent+PRD signal, weak helper, bounded read) — folded in. Reusable: the suite is parallel-safe
  and the state machine is now the canonical place for fresh-project routing.
