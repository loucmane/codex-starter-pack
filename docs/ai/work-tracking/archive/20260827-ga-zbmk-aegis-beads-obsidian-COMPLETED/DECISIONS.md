# Decisions

- 2026-08-27 — Prefer an explicitly supplied bead snapshot over Taskmaster when both exist, retain Taskmaster parsing for historical compatibility, and represent both through one normalized work-record model.
- 2026-08-27 — Gate Obsidian freshness at readiness/closeout and explicit publication only; never require a vault write after every mutation.
- 2026-08-27 — Require an explicit frozen bead JSON/JSONL snapshot rather than discovering a Dolt/Beads store or starting services from the projection. This keeps upgrades portable and makes authority selection reviewable.
- 2026-08-27 — Expose the boundary through the package CLI in this slice; do not add an MCP-only path or couple the gate to provider-specific process state.
- 2026-08-27 — Never publish to the vault root or an existing Gas City project root. The only valid target is an exact Aegis-owned subtree, with ownership proven by `.aegis-vault.json`.
- 2026-08-27 — Archived through the supported archive helper; no evidence was deleted.
