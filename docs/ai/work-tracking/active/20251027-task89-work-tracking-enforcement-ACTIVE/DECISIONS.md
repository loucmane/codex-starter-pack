# Decisions

- 2025-10-27 — Guard must require same-day updates across findings/decisions/changelog and Serena memory logging.
- 2025-10-27 — Guard ignores tracked ACTIVE deletions only when archive folder exists with tracker marked COMPLETED.
- 2025-11-25 — Continue using the original 20251027 ACTIVE folder for Task 89 verification; update guard evidence + plan paths instead of scaffolding a new folder when verification spans later dates.
- 2025-11-25 — Folder-name guard now skips already tracked ACTIVE folders that simply gain new evidence files; multi-day sessions rely on tracker timestamps rather than renaming directories.
- 2026-04-20 — Keep the modern working Codex config as the base and reintroduce only the core MCPs needed for this repo (`serena` and `taskmaster-ai`) instead of restoring the full 2025 backup.
- 2026-04-20 — Do not restore the previous `CODEX_HOME` override or optional MCPs (`context7`, `sequential-thinking`, `firecrawl`, `elevenlabs`, `fpl`, `shadcn`) until there is a current concrete use case and startup verification.
- 2026-04-20 — Run Taskmaster write operations sequentially when they mutate shared task state; parallel reads/writes can produce misleading success output and stale final status.

## Progress Log
- **2025-10-27 18:10** — [S:20251027|W:task89-work-tracking|H:docs/decisions|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/DECISIONS.md] Helper preset demo
- **2025-10-27 18:31** — [S:20251027|W:task89-work-tracking|H:docs/decisions|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/DECISIONS.md] Manual entry
- **2025-11-25 11:53** — [S:20251125|W:task89-work-tracking|H:docs/decisions|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/DECISIONS.md] Documented multi-day folder reuse policy (tracked folders exempt from date-prefix guard)
- **2026-04-20 13:44** — [S:20260420|W:task89-work-tracking|H:docs/decisions|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/DECISIONS.md] Chose minimal current MCP restoration strategy: Serena + Taskmaster only, no full config rollback
- **2026-04-20 14:16** — [S:20260420|W:task89-work-tracking|H:docs/decisions|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/DECISIONS.md] Decided Taskmaster state mutations must be sequential and verified after each batch
