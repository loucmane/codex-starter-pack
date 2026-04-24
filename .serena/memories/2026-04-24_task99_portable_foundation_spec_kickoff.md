# Task 99 Portable Foundation Specification Kickoff

- Branch: `feat/task-99-portable-foundation-spec`
- Session: `sessions/2026/04/2026-04-24-006-task99-portable-foundation-spec.md`
- Plan: `plans/2026-04-24-task99-portable-foundation-spec.md`
- Active folder: `docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/`

## Taskmaster status
Task 99 is `in-progress` after kickoff. Description: define the reusable contract for metadata, guard, session, and work-tracking behavior so core logic is separated from repo-local configuration.

## Kickoff context
- Task 98 active work-tracking was archived to `docs/ai/work-tracking/archive/20260424-task98-externalize-repo-structure-config-COMPLETED/` before starting Task 99.
- `sessions/current`, `plans/current`, and `sessions/state.json` now point to Task 99.
- Kickoff used `templates/metadata/template-metadata-policy.json` as the initial handler target because Task 99 builds on the metadata/policy model from Task 91.

## Important note
The Task 99 plan and tracker are structurally valid but still contain the generic wizard wording (wizard flow / helper integration / generic scope). As with Task 98, the first real Task 99 step is to rewrite the plan/tracker/design baseline around the actual portable foundation specification:
- required metadata contract
- guard/enforcement semantics
- session and work-tracking lifecycle expectations
- boundary between core logic and repo-local adapter configuration

## Next steps
1. Rewrite Task 99 plan/tracker/design baseline for the portable foundation specification.
2. Inventory the existing specification sources: Task 91 metadata policy, Task 98 repo-structure config contract, guard semantics, session/work-tracking rules.
3. Draft the portable foundation spec before making any follow-on structural changes.
