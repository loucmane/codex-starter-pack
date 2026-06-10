# PR-1c scope — gate-decisions dual-write

Binding contract: `docs/aegis/AEGIS_CAPSULE_SPEC.md` §1.2 (row 1c) and §2
(gate-decisions migration, decided). Builds on PR-1a (ledger core, #200) and PR-1b
(record hooks, #201).

## Deliverables

1. **Dual-write**: every advisory gate decision written by `append_gate_decision()`
   (pretooluse `would_block`/`allow`, stop-gate decisions) is ALSO appended to the
   ledger as an `event_type: gate_decision` event — JSONL at
   `.aegis/reports/gate-decisions.jsonl` remains the primary, untouched surface.
   Ledger append is best-effort and silent-on-failure (same never-break contract as
   the recorder); JSONL write never depends on it.
2. **Session attribution**: `Payload` gains optional `session_id`/`cwd` carried from
   the hook stdin JSON (`load_payload`), so gate-decision events join the same
   session timeline as recorder events. Defaults to None — every existing call site
   and test remains valid.
3. **Event mapping**: extra carries {verdict, reason, mode, hook, source_commit,
   readiness_state when present}; payload_digest matches the JSONL record exactly —
   that digest equality IS the parity key.
4. **Tests**: advisory-repo fixture runs the real gate via subprocess and asserts
   old-vs-new parity — every JSONL record has a ledger twin with identical
   payload_digest/verdict/reason/mode; ledger failure (no git / no ledger_lib) leaves
   JSONL intact; strict mode unchanged (no decisions recorded anywhere, blocks still
   block).

## Explicitly NOT in this PR (per spec §2)

- Freezing the JSONL read-only — that happens one release AFTER dual-write ships.
- Migrating JSONL history into the ledger — never.
- Changing what `aegis enforce status` or existing tests read — they keep reading the
  JSONL today and after.

## Merge gate (spec §1.2 row 1c)

Old-vs-new parity on live decisions (fixture-driven locally; live parity check in this
repo's store rides the dogfood).
