# Decisions

- 2026-07-11 - Run a convergence program before Task 210. No broad PR-4 deletion pass is
  authorized by Task 236.
- 2026-07-11 - Make managed agent instructions truthful and mode-aware before asking for more
  dogfood; stale strict ceremony is itself a product defect.
- 2026-07-11 - Apply one universal default output budget of 60 lines and 8 KiB, with full detail
  in artifacts and intentional detail flags.
- 2026-07-11 - Audit worktree/subagent capture before implementing a fix. The consumer report is
  accepted as a real observation, not yet as a proven root cause.
- 2026-07-11 - Treat the deterministic witness as the canonical delivery boundary after context
  budgets and worktree attribution are established.
- 2026-07-11 - Decompose only the managed-update slice of the installer and preserve generated
  behavior; a rewrite or target-repository migration is out of scope.
- 2026-07-11 - Keep hash chaining, an Aegis policy language, an Aegis OS sandbox, and PR-3
  narration outside this program unless later evidence changes the requirement.
- 2026-07-11 - Gate Task 210 directly on Task 243. Task 243 transitively requires Tasks 237-242
  and must issue row-by-row go/no-go decisions with proof and rollback.
- 2026-07-11 - Do not fabricate upstream `.aegis/state/current-work.json` to satisfy closeout.
  Retain Task 236 as the sole completed ACTIVE compatibility projection, create Task 244 for a
  fail-closed repository-derived completion path, and make Task 243 depend on it.
