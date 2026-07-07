# Task 230 Computed capsule active-task orientation fields – Handoff Summary

## Current State
- Implementation and local verification are complete. The computed capsule now reports deterministic
  active-task orientation under `task_truth` and renders a `Current work` line with
  `next_action`.
- Focused capsule tests passed: `python3 -m pytest tests/claude_adapter/test_brief_lib.py
  tests/claude_adapter/test_capsule_injection.py` (31 passed).
- Taskmaster health, dependency validation, work-tracking audit, guard validation, and
  `git diff --check` passed locally.
- The stale completed Task 217 ACTIVE folder was archived through
  `python3 scripts/codex-task work-tracking archive`, leaving Task 230 as the sole active
  work-tracking envelope.

## Next Steps
- Commit the scoped diff, open a PR, and wait for CI.
