# Task 221 — Drain-layer fix: design scope

Date: 2026-06-14. HP-Coach report 3: draining a pre-#224 read-only pending backlog via
`aegis log --pending-id --plan-step plan-step-verify` accreted each event's evidence into
the plan's required-evidence cell, so closeout.evidence.* required inspection noise
(.scratch/, /tmp/, mcp__playwright__browser_click, =p, 127:). KEY INSIGHT (design+adversarial
workflow): matching-layer demotion (TM 218) is fundamentally insufficient — a read-only path
token is indistinguishable by shape from a real edit; only the originating event's tool knows.
So the fix is at the DRAIN/SOURCE layer.

## Implementation (scripts/_aegis_installer.py + cli.py)
- `_load_target_gate_lib(target_root)`: dynamic import of the TARGET's gate_lib (classify by
  the gate version that recorded the events); fail-None.
- `_stored_event_is_read_only(target_root, event)`: STRICT, fail-KEEP classifier by tool +
  recovered command, never by evidence shape. Edit/Write/etc → keep. Bash: only `cmd`...``
  with bash_is_read_only(inner) → discard (provably safe: bash_is_mutation is the exact
  complement); redirect/verify evidence → keep. MCP: discard ONLY browser namespaces,
  taskmaster discovery suffixes, and MCP_READ_ONLY_TOOL_RE matches; KEEP apply-gated aegis
  (repair/runtime_update/handoff_repair), aegis read-only suffixes (target-dir hole),
  mutation-RE, and unknown.
- Drain-gate in log_work: a read-only `--pending-id` event drains from the queue and returns
  status=purged_read_only WITHOUT writing surfaces or the plan cell.
- `purge_read_only_pending(target_dir, apply=False)` + `aegis repair --purge-read-only-pending`:
  batch-clean a pre-#224 backlog (preview/--apply), fail-KEEP, touches only the queue file.

## Adversarial verification
Design workflow found + closed an apply-gated MCP escape (aegis_repair w/ empty tool_input
reconstructed read-only); implementation classifies name-only so apply-gated tools are kept.
A diff-review sub-agent attacked the implemented classifier and returned SAFE (no mutation
escape). 20 tests incl. the full classifier matrix, fail-keep, purge, and drain integration.

## Honest scope (recovery-scope attack)
Prevents FUTURE accretion + purges the queue backlog; does NOT retroactively clean
already-polluted plan cells, so HP-Coach task 80 stays mark-done (not recovered). Post-#224
read-only never enters the queue, so lasting value is the one-time purge + correctness backstop.

## Boundary
Live scripts/_aegis_installer.py + cli.py + tests. Assets installer copy drift is TM 219
(not synced here). HP-Coach runs the live CLI.
