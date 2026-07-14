# Task 243 Refresh PR-4 Parity Evidence and Build the Derived Obsidian Vault – Implementation Notes

## Derived Obsidian Vault

- Added `aegis_foundation/obsidian_vault.py` as a deterministic, bounded, read-only projection
  engine.
- Added `aegis vault path|build|check` to the package CLI.
- Default output lives beside the XDG ledger; explicit output inside the source repository is
  rejected.
- Generated notes use YAML properties, path-qualified wikilinks, and native Obsidian `.base`
  views without generating `.obsidian/` settings or requiring plugins.
- High-signal events produce evidence notes. All events contribute only deduplicated
  agent/parent/session/branch/worktree topology, preventing per-call graph churn.
- Legacy S:W:H:E files contribute structural inventory, human-line counts, headings, task links,
  and content hashes while full narrative remains authoritative in Git.
- Builds require a valid exact ownership/hash manifest and publish through staged self-check plus
  atomic directory replacement. Unknown, manually edited, symlinked, in-repository, oversized,
  or unbounded destinations fail closed.
- Corrected sandboxed read-only SQLite fallback so immutable column metadata is established before
  query construction; live and packaged ledger assets remain byte-identical.

## Verification To Date

- 44 focused vault/ledger tests pass.
- 75 package invocation, release-distribution, asset-parity, vault, and ledger tests pass; two
  explicitly opt-in wheel/MCP smoke tests remain skipped for the final verification phase.
- Real source, Blog, and HP-Fetcher builds all pass and produce byte-stable no-op second builds.
- Detailed measurements are stored in `reports/obsidian-vault/dogfood.md`.

## Coexistence And Parity Contract

- Rewrote `docs/aegis/pr-4-replacement-parity-matrix.md` around the reviewed complementarity
  decision.
- Added a required `Remaining unique legacy content` column to all 20 rows.
- Every row now cites current source, Blog, HP-Fetcher, or Tasks 237–252 evidence, names rollback,
  remains `keep` or `shadow`, and marks Task 210 `NO-GO`.
- Strengthened the matrix regression so retirement cannot appear as incidental cleanup.
- Added `reports/coexistence-audit.md` with per-kind human-content measurements and the authority
  split between ledger, capsule, witness, task truth, legacy narrative, and vault.

## Final Read-Only Audit

- Rebuilt fresh source, Blog, and HP-Fetcher vaults under unique `/tmp` destinations and ran
  `aegis vault check` immediately after each build.
- All three passed exact ownership, inventory, hash, and freshness checks.
- Recorded downstream branch, capsule, runtime provenance, enforcement mode, and dirty-state facts
  without updating, staging, repairing, or hiding any downstream path.
- Added `reports/final-cross-repository-audit.md` as the reviewed pre-Gas-Town stopping checkpoint.

## Final Verification

- Full repository suite: 2,045 passed, four explicit opt-in skips, zero failed.
- Local wheel CLI and MCP stdio smokes passed sequentially with task-local sandbox caches.
- Black, Ruff, mypy, byte compilation, live/package parity, Taskmaster health, S:W:H:E guard,
  strict drift, work-tracking audit, capsule, readiness, and diff checks passed.
- Installed-target strict verification correctly refused because the source worktree has no
  managed manifest; no installed state was fabricated.
- Full command context and environment-specific rerun rationale are in
  `reports/task-verification.md`.
