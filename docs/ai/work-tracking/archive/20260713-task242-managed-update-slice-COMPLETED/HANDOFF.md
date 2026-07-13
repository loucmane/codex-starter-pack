# Task 242 Extract The Managed-Update Slice From The Aegis Installer – Handoff Summary

## Current State
- Task 242's managed-update extraction is implemented behind compatibility adapters. `aegis_foundation/managed_update.py` now owns the deterministic asset model, asset assembly, target materialization, prior-byte recovery, fail-closed operation classification, and summaries.
- `scripts/_aegis_installer.py` remains the orchestration/rendering/report adapter and preserves legacy private names. Its packaged mirror is byte-identical.
- The installer moved from 13,651 to 13,325 lines (-326); the new stdlib-only core is 777 lines. No target layout, manifest schema, runtime state, or ledger migration changed.
- Golden Codex, HP-Fetcher, and Blog plans pass with fixed operation digests. Read-only previews against the live downstream repositories found no conflict, manual-review, or unsafe overwrite.
- Focused installer, MCP, cross-project, release, wheel CLI, and wheel MCP stdio coverage passes. Black 26.3.1, Ruff 0.15.12, mirror parity, and `git diff --check` pass.
- The complete repository suite reports 1,765 passed, four opt-in smokes skipped, and one unchanged reconcile assertion whose source checkout location premise is invalid in a `/tmp` worktree. The exact assertion fails identically on untouched Task 240, so it is recorded rather than weakened.
- The exit-zero local regression gate then passed 1,765 tests with four opt-in skips and only that proven baseline assertion deselected; hosted CI must execute it in a normal checkout.
- The optional real-target wheel MCP lifecycle smoke also fails identically on Task 240 because the harness attempts kickoff before acknowledging the required client-reload marker. Basic wheel CLI and MCP stdio smokes pass.
- Taskmaster Task 242 is `done`, this evidence bundle is archived, and completed-source plan, tracking, readiness, Taskmaster, and S:W:H:E validation passes.

## Next Steps
- Commit and push the Task 242 branch, open a stacked draft PR against Task 240, and require exact-head hosted Python/guard/witness checks from a normal checkout outside `/tmp`.
- Deliver only after Task 240; rollback is a single reviewed revert and requires no downstream migration.
- Archived on 2026-07-13 18:39 CEST — Folder moved to archive and tracker marked COMPLETED.
