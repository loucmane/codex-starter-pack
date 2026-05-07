# Task 10 Implement Reference Fix Scripts – Handoff Summary

## Current State
- Task 10 is initialized on `feat/task-10-reference-fix-scripts`.
- Scope reconciliation and implementation are complete.
- Added the tracked safe runner at `scripts/template-ssot-scanner/apply_reference_fixes.py`.
- Updated `generate_fixes.py` generated wrappers and README safe usage docs.
- Scanner test suite passed with `133 passed`.
- The current generated reference-fix dry-run was captured as JSON evidence; no template reference fixes were applied.
- Final plan sync, work-tracking audit, codex guard, and `git diff --check` passed.
- Forward-looking architecture note captured in `designs/agent-foundation-portability-options.md`: choose a repo-installed local runtime/CLI with an MCP installer/control-plane wrapper for portability, not MCP-only enforcement.

## Next Steps
- Commit/push with regular Git commands and open the PR.
- After PR merge, archive `20260507-task10-reference-fix-scripts-ACTIVE`.
- Future task candidate: build Agent Foundation installer/manifest/doctor/smoke-test first, then add an MCP wrapper around the stable local CLI/package.
