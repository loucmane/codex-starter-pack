# Findings

- 2026-07-15 — **Split brain is real, but active-work safety is still unknown** — Read-only
  dogfood found separate normal and Remote Control session stores, two live control-socket
  paths, multiple executable identities, and more than one SQLite root under the normal
  home. The sandbox process namespace exposed no reliable host-complete inventory, so the
  collector correctly reported process scope as unknown and blocked cutover planning.
- 2026-07-15 — **SQLite authority cannot be inferred from directory convention** — The
  normal home currently exposes both `state_5.sqlite` and `sqlite/state_5.sqlite`; the
  isolated Remote home exposes no discovered state database. Task 257 must determine the
  live authoritative database from explicit configuration and open-file ownership before
  choosing `CODEX_SQLITE_HOME`.
- 2026-07-15 — **The wrapper is transitional routing, not durable topology authority** —
  Bounded inspection detected CWD, global-home, Remote-home, and `CODEX_HOME` routing
  signals in `/home/loucmane/.local/bin/codex-wrapper`. The diagnostic emits only its digest
  and classified signals, never wrapper source or permission to retire it.
- 2026-07-15 — **Stale-thread wording requires positive temporal proof** — Durable trust on
  disk is insufficient to claim that a thread predates a trust change. The exact stale
  diagnosis is emitted only when a valid trust timestamp and uniquely owned thread start
  timestamp prove the ordering; all ambiguous cases remain `unknown`.
- 2026-07-15 — **Task 256 preserved all live state** — The implementation performs bounded
  reads only and does not contain process lifecycle, shell-edit, trust-copy, hook-approval,
  session-copy, or host-write operations. Task 257 remains the sole place where a reviewed
  cutover may occur.
- 2026-07-15 — **Regression exceptions are environmental/baseline, not product defects** —
  The runnable suite passed 2,130 tests. Two editable-install tests fail identically on
  untouched main because the sandbox cannot resolve `setuptools>=68`; the local stdio MCP
  integration test times out identically on untouched main; and a repository-location test
  fails only when `REPO_ROOT` itself is the required `/tmp` clone but passes in the
  canonical `/home` checkout. These exceptions are recorded rather than weakened or hidden.
