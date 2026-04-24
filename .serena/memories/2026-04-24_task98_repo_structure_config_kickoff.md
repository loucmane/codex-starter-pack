# Task 98 Repo Structure Config Kickoff

- Branch: `feat/task-98-externalize-repo-structure-config`
- Session: `sessions/2026/04/2026-04-24-005-task98-externalize-repo-structure-config.md`
- Plan: `plans/2026-04-24-task98-externalize-repo-structure-config.md`
- Active folder: `docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/`

## Taskmaster status
Task 98 is `in-progress` after kickoff. Description: externalize hardcoded repo-structure assumptions into repo-local configuration so the enforcement foundation can adapt to different project layouts.

## Kickoff state
- Task 97 active work-tracking folder was archived to `docs/ai/work-tracking/archive/20260424-task97-template-metrics-dashboard-COMPLETED/` before starting Task 98.
- `sessions/current`, `plans/current`, and `sessions/state.json` now point to Task 98.
- The kickoff used `scripts/codex-guard` as the initial handler target because it currently centralizes many of the repo-layout assumptions.

## Important note
The wizard-generated Task 98 plan and tracker are structurally valid but still use the generic wizard wording (scope/implement/verify around wizard flow). The first real Task 98 step is to rewrite the plan/tracker/design artifacts around repo-structure configuration, identify the hardcoded path assumptions in `scripts/codex-guard` and related helpers, and then continue implementation from that corrected baseline.

## Next steps
1. Rewrite Task 98 plan/tracker/design baseline for repo-structure configuration rather than wizard behavior.
2. Inventory hardcoded repo roots/path rules in `scripts/codex-guard`, `scripts/codex-task`, and related docs/tests.
3. Decide on the repo-local configuration contract before code changes.
