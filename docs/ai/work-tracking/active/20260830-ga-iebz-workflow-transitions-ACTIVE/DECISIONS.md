# Decisions

- 2026-08-30 — Implement a thin modular CLI over existing project-context, kickoff,
  readiness, guard, Git, closeout, and publication components; do not duplicate their policy.
- 2026-08-30 — Store append-forward transition journals under the Git common directory so
  linked worktrees share recovery state without committing host-local transaction files.
- 2026-08-30 — Keep external publication, rig lifecycle, service mutation, keys, and
  deployment outside this workflow's authority even when it reports those next actions.

## Progress Log
- **2026-08-30 12:43 CEST** - [S:20260830|W:ga-iebz-workflow-transitions|H:workflow:design|E:docs/ai/work-tracking/active/20260830-ga-iebz-workflow-transitions-ACTIVE/designs/workflow-transition-contract.md] Defined the memory-independent modular transition contract, journal phases, source/installed backends, and non-authority boundaries
