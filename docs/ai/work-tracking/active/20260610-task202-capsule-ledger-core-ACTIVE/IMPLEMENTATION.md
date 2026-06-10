# Task 202 Capsule PR-1a: passive ledger core (store, schema, redaction) – Implementation Notes

## Planned Workstreams
1. Contract check-in — spec + program-doc pointer in one commit (d730a46). DONE.
2. Backlog wiring — nine-PR tasks 202-210 + Phase-0 reconciliation (081a177). DONE.
3. PR-1a build — ledger core + schema doc + discoverability + tests. DONE (this entry).

## What was built

- `aegis_foundation/assets/.claude/scripts/ledger_lib.py` (mirrored byte-identical at
  `.claude/scripts/ledger_lib.py`, same dual-copy convention as gate_lib.py): stdlib-only
  module with SQLite open/append/read at
  `${XDG_STATE_HOME:-~/.local/state}/aegis/<sha1-of-git-common-dir>/ledger.db`
  (WAL + busy_timeout 5000ms), `normalize_event` (v1 schema, graceful null degradation,
  unknown keys folded into `extra`), capture-time redaction (5 default patterns +
  `redact_patterns` extension point), backend-agnostic reader contract with the JSONL
  per-session-shard fallback backend, and `rotate_if_needed` (64 MB constant; enforcement
  wiring deferred to PR-1b). No hash chain (spec section 2 decision).
- `docs/aegis/LEDGER_SCHEMA.md`: the documented-schema deliverable (table DDL, field
  semantics, event_type vocabulary for the whole program, exit-class mapping, redaction
  layers, fallback contract, query recipes).
- `aegis ledger path` subcommand (`aegis_foundation/cli.py`: `_load_ledger_lib` via the
  runtime source root, same pattern as `aegis hook`) and a read-only `ledger` block in
  `aegis status` (`scripts/_aegis_installer.py`: `_ledger_status_block`, best-effort,
  never fatal, present for installed AND not-installed targets).
- Gate classification: `aegis ledger path` added to the read-only aegis remainder in
  `gate_lib.py` (both copies) so the discoverability command works under strict
  enforcement while readiness is BLOCKED — debugging out-of-worktree state is exactly
  the BLOCKED-state use case.
- Tests: `tests/claude_adapter/test_ledger_lib.py` — 29 tests: assets/live parity,
  AST-verified stdlib-only constraint, schema round-trip + null degradation (both
  backends), all five default redaction patterns + redact_extra (both backends), read
  filters/limit, JSONL shard merge ordering, 4-process concurrent SQLite writers,
  worktree store-path sharing via git common dir, XDG override, non-git failure modes,
  backend selection (arg/env/invalid), rotation, CLI `ledger path` happy/sad paths,
  `status` ledger block, gate read-only classification.

## Boundary notes (PR-1a contract)

- NO hook registration; NO settings/renderer/manifest changes; ledger_lib.py is not in
  managed_files, so install/repair does not propagate it yet — zero behavior change in
  governed repos. Nothing writes to the store except tests and explicit callers.
