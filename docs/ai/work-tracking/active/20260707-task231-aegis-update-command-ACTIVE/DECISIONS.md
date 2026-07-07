# Decisions

- 2026-07-07 — Ship `aegis update` as a composed single-repo updater, not as a fleet
  updater. Fleet registry, MCP process restart orchestration, update PR mode, rollback
  automation, and PR-4 scaffold retirement remain separate follow-up work.
- 2026-07-07 — Treat strict verification failures as report evidence rather than an
  update failure when runtime pointer, managed asset refresh, and capsule compile succeed.
  This prevents stale workflow-state residue from blocking safe capsule/runtime updates.
- 2026-07-07 — Add MCP `aegis.update` in the same slice. The user-facing problem is
  cross-project Aegis refresh through agent tooling, so MCP should expose the composed
  updater instead of leaving agents to reassemble the old manual sequence.
