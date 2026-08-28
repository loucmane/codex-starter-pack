# Decisions

- 2026-08-28 — Keep Beads authoritative and make Obsidian a one-way disposable projection. The reconciler executes only exact registry-pinned read-only source commands and never starts a rig, mutates a bead, or reads truth back from the vault.
- 2026-08-28 — Use one project-registry-driven user timer rather than per-project services or per-edit hooks. New projects require a registry update and deterministic unit refresh only.
- 2026-08-28 — Preserve strict synchronous readiness, closeout, and publication gates. Automatic freshness complements those gates and never bypasses them.



## Progress Log

- **2026-08-28 21:34** — [S:20260828|W:ga-eiyt-obsidian-reconciler|H:aegis_foundation/obsidian_reconciler.py|E:source-digest:363e4e0addec1e5a2d898396153eaae196961b2e5848e998ee115af72f86e27b;files:2730;beads:191;second-pass:changed=false;health:fresh] Decision: retain synchronous readiness/closeout/publication gates as hard boundaries and add one registry-driven user timer as the automatic reconciler; automatic publication never weakens or bypasses the gates.
- 2026-08-28 — Archived through the supported archive helper; no evidence was deleted.
- 2026-08-28 — Derive completed Beads-native source work from five local, fail-closed authorities: branch or default-branch current pointers, plan identity, session identity, one unique contained archive, and a COMPLETED tracker. Do not query the mutable external Beads service from commit hooks.
