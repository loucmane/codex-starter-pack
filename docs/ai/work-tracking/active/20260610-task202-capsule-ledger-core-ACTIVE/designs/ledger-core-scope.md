# PR-1a scope — passive ledger core (ledger_lib.py)

Binding contract: `docs/aegis/AEGIS_CAPSULE_SPEC.md` §1.2 (row 1a) and §2. This note pins
the implementation boundary for Task 202; decided items in spec §6 are not re-litigated.

## Deliverables

1. `aegis_foundation/assets/.claude/scripts/ledger_lib.py` — new standalone module,
   **stdlib-only, no aegis_foundation imports** (bootstrap fallback must work without the
   runtime). Ships next to `gate_lib.py` in the assets tree only; the codex repo's live
   `.claude/scripts/` copy is NOT touched in PR-1a (no hook registration, zero behavior
   change in any governed repo).
2. `docs/aegis/LEDGER_SCHEMA.md` — the documented ledger schema (the deliverable spec §6
   defers `aegis ask` in favor of).
3. `aegis ledger path` CLI subcommand + ledger path line in `aegis status` output
   (spec §2 discoverability: out-of-worktree state must never be invisible).
4. Unit tests extending the existing pytest layout (`tests/claude_adapter/` importlib
   `spec_from_file_location` loading pattern; fixtures under `tests/fixtures/`).

## Store decision (spec §2, decided)

- Append-only SQLite at `${XDG_STATE_HOME:-~/.local/state}/aegis/<sha1-of-git-common-dir>/ledger.db`.
- Keyed on the git **common** dir so all worktrees of a repo share one store.
- WAL mode + busy_timeout on every open.
- **No hash chain** (killed by adversarial review; append-only rows with timestamps).

## Event schema (v1 fields)

`schema_version, event_id, ts (UTC ISO), session_id, branch, cwd, event_type, tool_name,
handler, paths (normalized JSON array), outcome (pass|fail|interrupted|unknown),
duration_ms, agent_id, agent_type, exit_class, payload_digest, extra (JSON)` — nullable
where the hook payload lacks the field (degrade gracefully, never crash). Exact column
notes live in LEDGER_SCHEMA.md.

## Redaction (record-time layer, decided)

Default pattern list in `ledger_lib.py`: `wrangler secret put`, `Authorization:` headers,
`sk_*` tokens, `Bearer ` tokens, `eyJ*` JWT shapes. Extensible via `redact_extra`
(consumed from `.aegis/brief.json` by callers in PR-1d; ledger_lib takes patterns as an
argument so it stays config-agnostic). Redaction is applied to recorded command/argument
text before append.

## Fallback contract (defined now, not "if needed")

Per-session JSONL shards with the SAME event schema, same append semantics, same reader
merge behavior. The reader API in `ledger_lib.py` is backend-agnostic from day one, and
the full test suite runs against BOTH backends.

## Test matrix

- Schema round-trip (append → read; all fields, null degradation).
- Append/read under concurrent writers (multi-process, WAL + busy_timeout).
- Redaction patterns (each default pattern + a redact_extra pattern).
- Store-path resolution including worktrees (two worktrees of one repo resolve to the
  same store; XDG_STATE_HOME override honored).
- JSONL fallback backend passes the identical suite.
- `aegis ledger path` prints the resolved path; `aegis status` includes it.

## Explicitly out of scope (later PRs)

Hook registration / installer settings rendering (1b), gate-decisions dual-write (1c),
gate registry + command normalization + `.aegis/brief.json` (1d), `aegis brief` (2a/2b),
narration (3), witness (3.5), retirement (4). Volume guards beyond schema affordances
(rotation at 64 MB is a constant + helper here; enforcement wiring lands with 1b).

## Merge gate (spec §1.2)

Unit tests green. Nothing observable changes in any target repo.
