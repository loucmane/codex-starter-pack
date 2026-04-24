# Task 101 kickoff

- Branch: `feat/task-101-cross-project-compatibility-fixtures`
- Taskmaster status: `101` is `in-progress`
- Active folder: `docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/`
- Session: `sessions/2026/04/2026-04-24-008-task101-cross-project-compatibility-fixtures.md`
- Plan: `plans/2026-04-24-task101-cross-project-compatibility-fixtures.md`

## Current state
- Task 100 has been archived before kickoff.
- Guided kickoff created the Task 101 session/plan/tracker and repointed `sessions/current`, `plans/current`, and `sessions/state.json`.
- The generic wizard wording was rewritten around the actual Task 101 scope.
- `designs/cross-project-fixture-matrix.md` defines the initial matrix: product-web, game/tool, docs-heavy, and utility/library repo shapes.

## Next steps
1. Add reusable repo-shape fixtures under the test suite.
2. Wire those fixtures into bootstrap, guard, and path-resolution coverage.
3. Keep the suite config-driven so it validates alternate roots and template scopes rather than this repo's defaults.
4. Rerun `python3 scripts/codex-task plan sync ...` and `python3 scripts/codex-guard validate --include-untracked` after updating tracker/session with this memory reference.
