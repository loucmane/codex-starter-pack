# Task 231 Unified Aegis project update command – Handoff Summary

## Current State
- Implemented `project_update()` in the shared installer and synced the managed asset
  copy. The command composes runtime pointer update, install plan/apply, verification
  reporting, and computed capsule compile/check.
- Package CLI: `aegis update --target-dir . [--apply]`.
- Repo wrapper: `python3 scripts/codex-task aegis update --target-dir . [--apply]`.
- MCP surface: `aegis.update` with dry-run read-only behavior and explicit apply.
- Update docs now document the composed command as the normal single-repo update path.
- Task 230's completed ACTIVE folder was archived through
  `python3 scripts/codex-task work-tracking archive --folder ...` because it was already
  done and was blocking active-envelope audit for Task 231.

## Next Steps
- Commit/PR this slice if the diff remains limited to Task 231 implementation,
  Taskmaster/task-tracking files, the Task 230 archive move, and the earlier PR-4 fixture
  decision docs.
- Do not include unrelated local drift such as `.codex/deep-work.config.toml`,
  `.aegis/`, `.agents/`, `.codex/agents/`, or `.codex/hooks.json`.
- Later follow-ups: fleet registry/update, MCP restart orchestration, update PR mode,
  rollback automation, and PR-4 replacement/retirement.
