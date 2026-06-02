# Decisions

- 2026-06-02 — Define Task 149 as a contract/design task only. It must not add
  an enabled apply path, disabled scaffold, reconcile mutation flag, Taskmaster
  writer, git writer, PR writer, closeout shortcut, or workflow-state writer.
- 2026-06-02 — Make the invocation/confirmation model the primary deliverable:
  future apply must be structurally agent-excluded. Acceptable future channels
  are post-merge CI or operator-controlled local invocation outside the governed
  agent runtime.
- 2026-06-02 — Keep the first future apply class narrow:
  `merged_but_not_done` with `git_ancestor` proof only. Everything else remains
  manual-only or contract-excluded until separately proven.
- 2026-06-02 — Add apply-audit breadcrumbs and a global kill-switch as explicit
  prerequisites for any future disabled scaffold. Task 150, if created, should
  be a disabled orchestration scaffold with an intentionally unsatisfiable
  enable gate.
