# Task 242 Extract The Managed-Update Slice From The Aegis Installer – Implementation Notes

## Delivered Workstreams

- Added `aegis_foundation.managed_update`, a stdlib-only core for the managed asset value type, shared/client asset assembly, target-aware entrypoint and hook materialization, checksum recovery, fail-closed update planning, and deterministic summaries.
- Kept installer-owned policy constants, concrete renderers, JSON/schema I/O, report emission, apply orchestration, and rollback behavior in `scripts/_aegis_installer.py`.
- Preserved the installer `Asset` export and private compatibility functions so source-root, packaged, MCP, existing tests, and downstream callers retain their invocation shape.
- Preserved the installer-level legacy checksum monkeypatch seam after a focused regression exposed it during extraction.
- Mechanically synchronized the packaged installer mirror and proved live/package generated assets and plans are identical.
- Added deterministic golden plans for fresh Codex and known-stale HP-Fetcher/Blog targets, including project-owned entrypoint and hook preservation.
- Reconciled the extracted core with current main's first-class Codex adapter: shared Claude/Codex runtime assets are emitted once, Codex-only installs receive dispatcher-rendered shared hooks, semantically identical owner-created hook JSON is adopted byte-for-byte, and managed/unowned divergence remains fail-closed.

## Acceptance Coverage

- Codex golden plan: 38 creates, two safe structural modifications, zero skips/conflicts/manual reviews; digest `4367457a215ea7d0c08321e8fa5cddb51b52da107a3e8e3784a9a8be4c7f57d3`.
- HP-Fetcher golden plan: two safe modifications, 30 skips, zero creates/conflicts/manual reviews; digest `0be616403ea8b4d6c614d12de8153726e6daa456b0da8244bc394d5ad37b2a66`.
- Blog golden plan: two safe modifications, 40 skips, zero creates/conflicts/manual reviews; digest `314290cb214c29b5f4aaaa36d538bf73725495cecae84eb1258e15541bb97ba1`.
- Dry-run plans preserve target bytes; unknown local divergence remains `manual-review` and unsafe.
- Live read-only downstream previews stayed fail-closed and reported no unsafe operation.
- Wheel CLI and basic wheel MCP stdio paths load the extracted package implementation successfully.
- Rollback requires reverting the Task 242 commit only; no installed repository needs a repair or migration.

## Current-Main Reconciliation

- Current main installer: 14,349 lines; reconciled installer: 13,942 lines (-407). The extracted stdlib-only core is 870 lines.
- Installer delta against current main: 128 additions and 535 deletions; live and packaged copies are byte-identical.
- Focused verification: 10 managed-update/golden tests, 49 Codex-hook/parity tests, and 155 installer/release tests passed; three release smokes remain explicit opt-ins.
- The `/tmp` full-suite run produced 2,030 passes, four expected skips, and only the known checkout-location assertion; that assertion passes under a non-temp repository context. Final exact-tree verification is required from a real non-temp checkout.
