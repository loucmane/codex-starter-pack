# Findings

- 2026-08-31 — The installed registry has one entry with ID `gas-city` targeting `/home/loucmane/gas-city-ops`. The continuity auditor correctly reports an Operations project-ID mismatch, an unconfirmed live index, and no entries for Gas City, HPFetcher, or Blog.
- 2026-08-31 — The current reconciler already supports multiple explicit projects and the installer derives a narrow `ReadWritePaths` allowlist from their output parents. The missing layer is deterministic generation/validation of those entries, not a second daemon per project.
- 2026-08-31 — Unchanged reconciliations deliberately record `not-run-no-change`, which makes periodic filesystem freshness pass while the live-index surface becomes stale/unknown. A read-only probe on no-change cycles closes this gap without causing reload churn.
- 2026-08-31 — The continuity auditor is already the only classifier for Current/Next/Blocked/orphans. The Obsidian dashboard must consume its report rather than reimplement classification logic.
- 2026-08-31 — The first live installation refused safely because the generated registry inferred
  every Bead store as `city/rigs/<rig>` even though HPFetcher and Blog use external registered rig
  roots; the first successful project publication then exhausted an overly narrow 15-second live
  read. File rollback was exact, but transient private state and a failed oneshot result required
  explicit reconciliation. Repair bead `ga-ve57` therefore makes rig roots declarative and the
  entire user-level transaction rollback-exact.
- 2026-08-31 — The merge-bound retry restored files, state, and outputs exactly but exposed two
  controller-level timing assumptions: the 30-second subprocess deadline was shorter than a valid
  four-project reconciliation, and restarting an elapsed `OnUnitActiveSec` timer does not schedule
  a future trigger. The predecessor was restored to waiting after one normal old-runtime cycle;
  v0.6.2 uses a 360-second whole-cycle bound plus activation/inactivity timer semantics and verifies
  the exact timer substate during rollback.
- 2026-08-31 — The vault is missing the direct `GasCity/gas-city` parent while the managed root itself is safe. The installer now permits only one direct `<project-id>` parent beneath the declared managed root and removes a newly created empty or solely managed parent on rollback; it cannot create arbitrary ancestors.
- 2026-08-31 — Local full-suite execution reached the editable-package invocation tests, which require fetching a build dependency. Network-enabled package installation was correctly refused by the runtime safety boundary. All in-scope tests and adjacent offline integration modules pass; hosted CI remains the authority for those two network-dependent tests.
- 2026-08-31 — The v0.6.2 live gate restored every installed byte, private-state manifest,
  and managed output after HPFetcher's real history exceeded the legacy 2,000-agent ceiling
  (`2421 > 2000`). Per-project reloads also produced two bounded 30-second read timeouts, and
  `Persistent=true` made the predecessor timer briefly `elapsed` during rollback catch-up. The
  WSL Obsidian process never changed PID or start tick; the missing-process observation was a
  transient reload window, and a direct CLI read succeeded afterward.
- 2026-08-31 — v0.6.3 aligns the agent ceiling with the existing 5,000-edge safety ceiling,
  defers all live-index observations until every project/dashboard build finishes, coalesces
  reloads by Obsidian executable and vault, and waits for rollback catch-up to settle before a
  final byte-exact state/output restore.
- 2026-08-31 — A later Codex sandbox check saw neither the WSL Obsidian process nor a reachable
  CLI while the operator directly observed the WSL-native window still open. Process/CLI absence
  in a restricted observer is therefore not application-liveness evidence. The runtime already
  classifies this surface as `observer-limited`; host user-systemd execution and operator-visible
  WSL state remain authoritative for live-index acceptance, and no relaunch or close is warranted.
- 2026-08-31 — The v0.6.3 live transaction proved all four project publications and host live
  reads, then refused because the dashboard had been captured while project live-index state was
  still provisional and was checked after that state became confirmed. Its rollback restored every
  byte/output and the exact service/timer/Obsidian/rig state, but called `reset-failed` before the
  predecessor timer had reloaded the restored unit. v0.6.4 fixes both ordering defects without
  weakening the dashboard gate or accepting a partial rollback.
