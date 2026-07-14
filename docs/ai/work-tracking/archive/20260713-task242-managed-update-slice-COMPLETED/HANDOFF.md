# Task 242 Extract The Managed-Update Slice From The Aegis Installer – Handoff Summary

## Current State
- Task 242's managed-update extraction is implemented behind compatibility adapters. `aegis_foundation/managed_update.py` now owns the deterministic asset model, asset assembly, target materialization, prior-byte recovery, fail-closed operation classification, and summaries.
- `scripts/_aegis_installer.py` remains the orchestration/rendering/report adapter and preserves legacy private names. Its packaged mirror is byte-identical.
- Against current main, the installer moves from 14,349 to 13,942 lines (-407); the reconciled stdlib-only core is 870 lines. No target layout, manifest schema, runtime state, or ledger migration changed.
- Golden Codex, HP-Fetcher, and Blog plans pass with fixed operation digests. The Codex fixture now reflects the first-class shared hook adapter: 38 creates and two safe structural modifications. The earlier read-only downstream previews found no conflict, manual-review, or unsafe overwrite and were not rerun as mutations.
- Focused current-main compatibility passes: 10 managed-update/golden tests, 49 Codex-hook/parity tests, and 155 installer/release tests with three explicit opt-in skips. Isolated Ruff/Black, mirror parity, and `git diff --check` pass.
- The complete repository suite reports 1,765 passed, four opt-in smokes skipped, and one unchanged reconcile assertion whose source checkout location premise is invalid in a `/tmp` worktree. The exact assertion fails identically on untouched Task 240, so it is recorded rather than weakened.
- The exit-zero local regression gate then passed 1,765 tests with four opt-in skips and only that proven baseline assertion deselected; hosted CI must execute it in a normal checkout.
- The optional real-target wheel MCP lifecycle smoke also fails identically on Task 240 because the harness attempts kickoff before acknowledging the required client-reload marker. Basic wheel CLI and MCP stdio smokes pass.
- Taskmaster Task 242 is `done`; full-graph health reports 250 tasks, 383 subtasks, 435 valid dependency references, and zero invalid references. This evidence bundle remains archived and a July 14 continuation session records mainline reconciliation.

## Next Steps
- Commit the current-main reconciliation, verify the exact signed tree from a real checkout outside `/tmp`, retarget the existing draft PR to `main`, and require exact-head hosted Python/guard/witness checks.
- Rollback is a single reviewed revert and requires no downstream migration.
- Archived on 2026-07-13 18:39 CEST — Folder moved to archive and tracker marked COMPLETED.
