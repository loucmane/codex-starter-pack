# Findings

- 2026-08-27 — The existing Aegis vault is already deterministic, atomic, out-of-repository, and read-only, but its work graph and authority prose are Taskmaster-only even though the source workflow now supports bead-native kickoff.
- 2026-08-27 — The real Obsidian vault is `/home/loucmane/vaults/main`; publication must remain an explicit validated boundary because the vault is a durable knowledge surface, not execution authority.
- 2026-08-27 — The existing Gas City vault contract already reserves `Tasks/` for its bead projector and `Docs/worklogs/` for agents. Aegis therefore owns only a disjoint `Aegis/` subtree and refuses unknown or edited files inside that subtree.
- 2026-08-27 — Real-source dogfood projected 2,242 legacy documents and 207 high-signal events within existing limits. This confirms the gate can cover the current operations history without importing raw low-level mutation traffic.
- 2026-08-27 — Initial dogfood exposed an owner email in the structured bead note. The default content policy now excludes assignee/owner identity alongside title, description, and labels; all remain available only through explicit opt-in.
- 2026-08-27 — Obsidian CLI access currently depends on the desktop app being open, but the Aegis projection and gate are filesystem-native and deterministic, so readiness/closeout verification does not depend on a live GUI process.
- 2026-08-27 — PR #290's first hosted witness run found a migration seam: readiness accepted `codex/ga-*`, while the delivery witness still recognized only `task-*`; the repository brief also omitted `.mcp.json`, `README.md`, and `templates/`. The corrected witness derives `ga-zbmk` directly from the bead branch and accounts every changed path without relying on an unavailable CI ledger.
