# 2026-04-21 Task 91 Kickoff

## Context
- Branch: `feat/task-91-standardize-template-metadata`
- Session: `sessions/2026/04/2026-04-21-002-task91-kickoff.md`
- Taskmaster Task 91 status: `in-progress`
- Task 90 active work-tracking archived to `docs/ai/work-tracking/archive/20260421-task90-complete-engine-migration-COMPLETED/`.
- New active folder: `docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/`.

## Kickoff Findings
- Initial inventory across `templates/**/*.md` found 42 files with no frontmatter, 115 missing `title`, 85 missing `type`, and 121 missing `status`.
- The repo currently mixes three classes: fully annotated modular templates, partially annotated modular templates, and aggregate/reference docs with no frontmatter.
- The best first-pass targets are modular templates with partial frontmatter; aggregate/generated docs should be handled under a separate policy decision.

## Kickoff Decisions
- Treat `title`, `type`, and `status` as the initial canonical rollout keys for Task 91.
- Keep the first-pass rollout focused on modular template files before deciding what to require from aggregate/generated docs.

## Next Steps
- Define the canonical metadata schema for the in-scope modular template families.
- Batch-update the highest-volume template families.
- Extend guard coverage and tests once the schema boundary is explicit.
