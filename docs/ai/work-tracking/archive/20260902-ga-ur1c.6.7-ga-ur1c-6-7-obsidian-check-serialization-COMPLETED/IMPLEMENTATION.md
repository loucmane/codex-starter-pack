# Bead ga-ur1c.6.7 Serialize Obsidian health checks with active reconciliation – Implementation Notes

## Planned Workstreams
- `aegis_foundation/obsidian_reconciler.py` — add a bounded monotonic wait to the shared lock
  helper and use it only from `check_registry()`; preserve zero-wait writer behavior.
- `aegis_foundation/obsidian_reconcile_cli.py` — expose and validate the check-only timeout.
- `tests/claude_adapter/test_obsidian_reconciler.py` — prove wait-then-stable-check,
  fail-closed timeout, unchanged concurrent-writer no-op, and CLI scoping.
- Operator documentation — explain the reader/writer contract and the `lock-timeout`
  disposition without prescribing doctor retries.
