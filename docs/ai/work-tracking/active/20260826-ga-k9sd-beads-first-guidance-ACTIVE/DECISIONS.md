# Decisions

- 2026-08-26 — Gas City rig-scoped beads are authoritative for new work; Taskmaster is retained only as a named historical compatibility boundary during migration.
- 2026-08-26 — Do not bypass the work-tracking guard or fabricate a numeric task. Add a bead-native source kickoff that preserves the existing plan/tracker/session invariants without invoking Taskmaster.
- 2026-08-26 — Track the advertised-but-missing override separately as `ga-hoaq`; do not conflate it with the bead-native authority migration.
- 2026-08-26 — Keep reboot recovery observational: the logon task runs the read-only doctor and never resumes rigs, starts Gas City lifecycle components, or repairs state.



## Progress Log

- **2026-08-26 16:15** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:claude-readiness:bead-native|E:.claude/engine/claude-readiness.md] Kept bead readiness source-checkout-only and retained installed Aegis and historical Taskmaster compatibility contracts unchanged.
