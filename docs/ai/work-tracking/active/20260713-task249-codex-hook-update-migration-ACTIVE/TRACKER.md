# Task 249 Fix pre-adapter Codex manifest update migration Tracker

**Started**: 2026-07-13
**Status**: ACTIVE
**Last Updated**: 2026-07-13

## Goals
- [x] Reproduce the pre-adapter manifest apply-order failure with a deterministic fixture
- [x] Preserve manual-review refusal for divergent operator-owned Codex hook files
- [x] Allow supported migration to produce a current-schema manifest and managed hook candidate
- [ ] Verify idempotence, strict validation, source/package parity, and hosted CI

## Progress Log
- **2026-07-13 23:32** — [S:20260713|W:task249-codex-hook-update-migration|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-07-13 23:32 CEST`
- **2026-07-13 23:32** — [S:20260713|W:task249-codex-hook-update-migration|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/TRACKER.md] Scaffolded the Task 249 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-07-13 23:32** — [S:20260713|W:task249-codex-hook-update-migration|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 249 in progress and updated only its generated task file
- **2026-07-13 23:32** — [S:20260713|W:task249-codex-hook-update-migration|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 249 kickoff
- **2026-07-13 23:34** — [S:20260713|W:task249-codex-hook-update-migration|H:design|E:docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/designs/update-migration-order.md] Defined install-before-runtime sequencing as the minimal fail-closed fix for the Blog pre-adapter manifest migration
- **2026-07-13 23:36** — [S:20260713|W:task249-codex-hook-update-migration|H:scripts/_aegis_installer.py|E:tests/meta_workflow_guard/test_codex_hook_adapter.py] Reordered project update apply and added legacy-manifest plus divergent-hook regressions
- **2026-07-13 23:38** — [S:20260713|W:task249-codex-hook-update-migration|H:blog-snapshot-replay|E:docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/reports/codex-hook-update-migration/task-verification.md] Replayed the patched updater against Blog Task 40 in a disposable snapshot and passed all 42 strict checks
- **2026-07-13 23:45** — [S:20260713|W:task249-codex-hook-update-migration|H:pytest:full-suite|E:docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/reports/codex-hook-update-migration/task-verification.md] Passed 1,957 full-suite tests locally; retained hosted CI as the required non-/tmp proof for the single known location-sensitive assertion
- **2026-07-13 23:46** — [S:20260713|W:task249-codex-hook-update-migration|H:serena/memory|E:.serena/memories/2026-07-13_task249_codex_hook_update_migration.md] Captured the migration-order decision, safety boundary, and Blog rollout checkpoint in same-day Serena memory
- **2026-07-13 23:51** — [S:20260713|W:task249-codex-hook-update-migration|H:source-workflow-verification|E:cmd`python3 scripts/codex-task plan sync && python3 scripts/codex-task work-tracking audit && python3 scripts/codex-task taskmaster health && task-master validate-dependencies && python3 scripts/codex-guard validate`] Passed plan/tracker parity, work-tracking audit, full-graph Taskmaster health, dependency validation, and S:W:H:E guard checks; hosted CI remains the required non-`/tmp` proof

## Plan Compliance Checklist
- [x] plan-step-scope — Define alignment prerequisites and scope
- [x] plan-step-implement — Update workflow/guard/docs and capture tests
- [ ] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
