# Decisions

- 2026-08-26 — Gas City rig-scoped beads are authoritative for new work; Taskmaster is retained only as a named historical compatibility boundary during migration.
- 2026-08-26 — Do not bypass the work-tracking guard or fabricate a numeric task. Add a bead-native source kickoff that preserves the existing plan/tracker/session invariants without invoking Taskmaster.
- 2026-08-26 — Track the advertised-but-missing override separately as `ga-hoaq`; do not conflate it with the bead-native authority migration.
- 2026-08-26 — Keep reboot recovery observational: the logon task runs the read-only doctor and never resumes rigs, starts Gas City lifecycle components, or repairs state.



## Progress Log

- **2026-08-26 16:15** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:claude-readiness:bead-native|E:.claude/engine/claude-readiness.md] Kept bead readiness source-checkout-only and retained installed Aegis and historical Taskmaster compatibility contracts unchanged.
- **2026-08-26 17:14** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:windows-bootstrap:principal-sid|E:scripts/windows/install-gas-city-wsl-bootstrap.ps1] Treat the canonical Windows SID as principal authority; retain the user-facing account string only for task creation and evidence.
- **2026-08-26 17:55** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:windows-bootstrap:powershell51|E:scripts/windows/gas-city-wsl-bootstrap.ps1] Target Windows PowerShell 5.1 explicitly and treat the waited Process.ExitCode plus redirected streams as the native-process authority.
- **2026-08-26 18:08** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:windows-bootstrap:shared-custody|E:scripts/windows/gas-city-wsl-bootstrap.ps1] Use USERPROFILE as the cross-context custody boundary; do not place scheduled-task executables or evidence under packaged-app-virtualized LocalAppData.
- 2026-08-27 — Archived through the supported archive helper; no evidence was deleted.
