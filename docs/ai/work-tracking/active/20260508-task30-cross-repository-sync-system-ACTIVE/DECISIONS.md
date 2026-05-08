# Decisions

- 2026-05-08 — Treat Task 30's original auto-sync wording as historical. Implementation must follow the current portable foundation and the Task 4 backlog-alignment audit requirement for evidence-driven reframing.
- 2026-05-08 — Implement `python3 scripts/codex-task sync plan` as a non-destructive planning helper. It may read source/target repository files and write explicit report/runbook outputs when requested, but it must not copy files into the target, create branches, commit, push, open PRs, or perform bidirectional sync.
- 2026-05-08 — Keep dashboard and scheduled automation out of Task 30. Those require separate scope because the current foundation already has optional metrics/drift reporting and does not yet define a remote sync service contract.
