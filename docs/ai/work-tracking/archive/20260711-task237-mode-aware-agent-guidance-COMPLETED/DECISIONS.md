# Decisions

- 2026-07-11 - Use one static mode-aware managed block rather than rewriting docs every time
  enforcement mode changes. Agents inspect mode once at orientation and follow the matching
  branch.
- 2026-07-11 - Cap each rendered entrypoint and each marker-delimited managed block at 25
  nonblank lines. Project-owned content is excluded from the managed budget.
- 2026-07-11 - Advisory wording explicitly forbids routine pending draining, handoff repair, and
  closeout ceremony while preserving passive recording, `aegis brief`, and `aegis witness`.
- 2026-07-11 - Strict wording points to `.aegis/contract.md` for readiness, kickoff, logging,
  verification, and closeout; Task 237 does not weaken or remove strict enforcement.
- 2026-07-11 - Always merge all three entrypoints into existing target bytes, including managed
  `CODEX.md`, because marker replacement is deterministic and preserves project-owned content.
- 2026-07-11 - Fresh Claude and Agents entrypoints receive explicit managed markers so future
  updates can distinguish Aegis-owned guidance from project-owned instructions.
- 2026-07-11 - Replace a markerless legacy Claude entrypoint only when its bytes exactly match
  the checksum recorded in the installed manifest. Any divergence is treated as owner content
  and preserved conservatively.
- 2026-07-11 - Do not apply Task 237 to a dirty live dogfood branch. Use the live repository for
  preview evidence and an isolated clone for apply/idempotence evidence.
- 2026-07-12 - Preserve Task 237 as a completed archive and use Task 244's fail-closed source
  derivation for terminal readiness; do not recreate the former ACTIVE compatibility projection.
