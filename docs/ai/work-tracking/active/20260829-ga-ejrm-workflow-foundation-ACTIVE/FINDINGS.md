# Findings

- 2026-08-29 — _Pending_ — document new findings here.

## Progress Log

- **2026-08-29 21:10** — [S:20260829|W:ga-ejrm-workflow-foundation|H:workflow-foundation-scope|E:bead:ga-ejrm;docs/operations/repository-and-product-naming.md;plugins/gas-city-workflow/config/projects.json] Confirmed bead authority, transactional lifecycle scope, reusable plugin scope, and the four-way naming boundary without changing permissions or live infrastructure.
- **2026-08-29 23:17 CEST** - [S:20260829|W:ga-ejrm-workflow-foundation|H:plugin-marketplace-layout|E:codex plugin marketplace add;codex plugin add;110 focused tests] Moved the repository marketplace manifest to the Codex-standard .agents/plugins location, retained the plugin at its repo-root-resolved source path, proved a real isolated CLI install, and passed 110 focused regressions.
- **2026-08-29 23:42 CEST** - [S:20260829|W:ga-ejrm-workflow-foundation|H:obsidian-passive-ledger-root-cause|E:journal:aegis-obsidian-reconcile;unit:ProtectHome-read-only;sqlite:WAL] The continuous reconciler was not reboot-stale: active hook writes created WAL coordination state, and a direct SQLite reader attempted `-shm` coordination inside a read-only home mount. Weakening the unit would have violated passive-ledger ownership; a verified private snapshot is the correct boundary.
