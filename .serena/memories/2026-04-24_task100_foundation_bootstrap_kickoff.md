# Task 100 kickoff

- Branch: `feat/task-100-foundation-bootstrap-layer`
- Taskmaster status: `100` is `in-progress`
- Active folder: `docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/`
- Session: `sessions/2026/04/2026-04-24-007-task100-foundation-bootstrap-layer.md`
- Plan: `plans/2026-04-24-task100-foundation-bootstrap-layer.md`

## Current state
- Task 99 was archived before kickoff.
- Guided kickoff created the Task 100 session/plan/tracker and repointed `sessions/current`, `plans/current`, and `sessions/state.json`.
- The generic wizard wording was rewritten around the actual Task 100 scope.
- `designs/foundation-bootstrap-layer-outline.md` defines the initial direction: keep bootstrap under `scripts/codex-task`, generate starter config/policy assets, and keep behavior migration-safe for repos with pre-existing workflow files.

## Next steps
1. Implement the bootstrap command surface inside `scripts/codex-task`.
2. Add starter asset generation for repo-local config/policy/workflow roots.
3. Add tests for empty-repo and existing-repo bootstrap behavior.
4. Rerun `python3 scripts/codex-task plan sync ...` and `python3 scripts/codex-guard validate --include-untracked` after adding the Serena tracker reference.
