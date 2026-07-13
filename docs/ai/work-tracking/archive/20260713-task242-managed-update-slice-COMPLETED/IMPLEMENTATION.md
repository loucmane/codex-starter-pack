# Task 242 Extract The Managed-Update Slice From The Aegis Installer – Implementation Notes

## Delivered Workstreams

- Added `aegis_foundation.managed_update`, a stdlib-only core for the managed asset value type, shared/client asset assembly, target-aware entrypoint and hook materialization, checksum recovery, fail-closed update planning, and deterministic summaries.
- Kept installer-owned policy constants, concrete renderers, JSON/schema I/O, report emission, apply orchestration, and rollback behavior in `scripts/_aegis_installer.py`.
- Preserved the installer `Asset` export and private compatibility functions so source-root, packaged, MCP, existing tests, and downstream callers retain their invocation shape.
- Preserved the installer-level legacy checksum monkeypatch seam after a focused regression exposed it during extraction.
- Mechanically synchronized the packaged installer mirror and proved live/package generated assets and plans are identical.
- Added deterministic golden plans for fresh Codex and known-stale HP-Fetcher/Blog targets, including project-owned entrypoint and hook preservation.

## Acceptance Coverage

- Codex golden plan: 26 creates, two safe structural modifications, zero skips/conflicts/manual reviews; digest `fa94284a05f90f51fbf23ed8b9a59c1a595bbbf1cb6f8d156a2c9808b79e7c10`.
- HP-Fetcher golden plan: two safe modifications, 30 skips, zero creates/conflicts/manual reviews; digest `0be616403ea8b4d6c614d12de8153726e6daa456b0da8244bc394d5ad37b2a66`.
- Blog golden plan: two safe modifications, 40 skips, zero creates/conflicts/manual reviews; digest `314290cb214c29b5f4aaaa36d538bf73725495cecae84eb1258e15541bb97ba1`.
- Dry-run plans preserve target bytes; unknown local divergence remains `manual-review` and unsafe.
- Live read-only downstream previews stayed fail-closed and reported no unsafe operation.
- Wheel CLI and basic wheel MCP stdio paths load the extracted package implementation successfully.
- Rollback requires reverting the Task 242 commit only; no installed repository needs a repair or migration.
