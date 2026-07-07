# Task 231 - Unified Aegis project update command

Task 231 adds a first-slice `aegis update --target-dir . [--apply]` command for one installed target repository. Scope is single-repo update only; fleet registry, MCP restart, update PR mode, rollback automation, and PR-4 scaffold retirement remain out of scope.

Implemented shared installer primitive `project_update()` in `scripts/_aegis_installer.py` and synced the managed asset copy under `aegis_foundation/assets/scripts/_aegis_installer.py`. The primitive composes runtime pointer update, managed install plan/apply, verification reporting, and computed capsule compile/check. Dry-run writes no target files. Apply refuses unsafe/manual-review install plan items, preserves enforcement mode, writes `.aegis/reports/update-report.json`, and compiles `.aegis/capsule/current.{json,md}`.

Wired package CLI `aegis update` in `aegis_foundation/cli.py` and repo wrapper `python3 scripts/codex-task aegis update` in `scripts/codex-task`.

Important contract: strict verification failures are included in the update report but do not fail a successful managed refresh. This preserves the HP-Fetcher Task 80 lesson: stale workflow-state gates should be visible evidence, not blockers for safe runtime/capsule refresh.

Focused tests were added to `tests/meta_workflow_guard/test_aegis_installer.py` for dry-run/no-mutation, apply refresh+capsule compile, manual-review refusal, and wrapper CLI smoke behavior. Full installer test file passed: `105 passed, 1 skipped`.

During verification, Task 230's completed ACTIVE folder was archived to `docs/ai/work-tracking/archive/20260707-task230-computed-capsule-orientation-COMPLETED/` because Taskmaster #230 was already done and its tracker recorded completed validation; it was causing multiple-ACTIVE audit failures for Task 231.