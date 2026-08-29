# Findings

- 2026-08-29 — _Pending_ — document new findings here.

## Progress Log

- **2026-08-29 21:10** — [S:20260829|W:ga-ejrm-workflow-foundation|H:workflow-foundation-scope|E:bead:ga-ejrm;docs/operations/repository-and-product-naming.md;plugins/gas-city-workflow/config/projects.json] Confirmed bead authority, transactional lifecycle scope, reusable plugin scope, and the four-way naming boundary without changing permissions or live infrastructure.
- **2026-08-29 23:17 CEST** - [S:20260829|W:ga-ejrm-workflow-foundation|H:plugin-marketplace-layout|E:codex plugin marketplace add;codex plugin add;110 focused tests] Moved the repository marketplace manifest to the Codex-standard .agents/plugins location, retained the plugin at its repo-root-resolved source path, proved a real isolated CLI install, and passed 110 focused regressions.
- **2026-08-29 23:42 CEST** - [S:20260829|W:ga-ejrm-workflow-foundation|H:obsidian-passive-ledger-root-cause|E:journal:aegis-obsidian-reconcile;unit:ProtectHome-read-only;sqlite:WAL] The continuous reconciler was not reboot-stale: active hook writes created WAL coordination state, and a direct SQLite reader attempted `-shm` coordination inside a read-only home mount. Weakening the unit would have violated passive-ledger ownership; a verified private snapshot is the correct boundary.
- **2026-08-30 00:20** — [S:20260830|W:ga-ejrm-workflow-foundation|H:ci-and-continuation-findings|E:run:33277398311;test_aegis_release_distribution.py;scripts/codex-task:sessions-continue] Found one stale canonical repository assertion in PR #310 and a bead-native daily continuation gap: sessions continue accepted only numeric Taskmaster IDs despite bead authority.
- **2026-08-30 00:44 CEST** — [S:20260830|W:ga-ejrm-workflow-foundation|H:terminal-audit|E:cutover-r2:pass;obsidian-epoch:equal;supervisor-epoch:equal;residue:zero] The repository rename, canonical plugin activation, and continuous Obsidian migration compose cleanly: every held consumer digest transitioned exactly once, while legacy work and unrelated live epochs remained unchanged.
- 2026-08-30 — Archive preconditions were satisfied and the completed bundle was preserved.
