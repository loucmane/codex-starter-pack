# Project Update Command Design

## Scope

Task 231 adds a first-slice `aegis update --target-dir . [--apply]` command for one
installed target repository. It composes existing safe primitives rather than creating a
parallel updater:

- runtime pointer preview/apply (`runtime update`)
- managed asset plan/apply (`plan-install` / `install --apply`)
- verification reporting (`verify`)
- computed capsule compile/check (`brief`)

Fleet registry, MCP process restart, update-PR automation, rollback automation, and PR-4
retirement of old session/plan/tracker scaffolding remain out of scope.

## Behavior Contract

Dry-run writes no target files and reports what would change. Apply refuses unsafe
overwrite or manual-review install operations, preserves the target's enforcement mode,
updates only installer-managed assets plus installer-owned reports/state, writes
`.aegis/reports/update-report.json`, and compiles the capsule.

Strict verification failures are included in the report but do not make a successful
managed update fail. This preserves the HP-Fetcher Task 80 lesson: stale workflow-state
gates should be visible evidence, not a reason to block a safe runtime/capsule refresh.
