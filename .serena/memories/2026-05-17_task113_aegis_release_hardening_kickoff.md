# 2026-05-17 Task 113 Aegis Release Hardening Kickoff

## Context
- Branch: `feat/task-113-aegis-release-hardening`
- Taskmaster Task: `113` - Aegis Release Hardening and Distribution Readiness
- Session: `sessions/2026/05/2026-05-17-004-task113-aegis-release-hardening.md`
- Plan: `plans/2026-05-17-task113-aegis-release-hardening.md`
- Active work tracking: `docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/`

## What Started
- Task 113 was created after Task 112 closed out all 112 prior tasks.
- Task 113 depends on Task 112 and extends the local checkout/editable package invocation contract into release/distribution readiness.
- Task 113 was expanded into eight subtasks covering release contract design, package metadata/versioning, wheel/sdist asset bundling, external CLI invocation, packaged MCP startup, update/rollback/signing policy, CI install templates, and final verification/handoff.
- Task 113 and subtask 113.1 are currently `in-progress`.

## Immediate Guard Fixes
- The kickoff wizard produced a generic `wizard-flow.md` evidence expectation. Replace/fill it with a Task 113-specific release/distribution contract baseline under the active folder's `designs/` directory.
- Tracker must reference this Serena memory in today's progress log for guard/audit compliance.
- After updating plan/tracker/session/design files, run `python3 scripts/codex-task plan sync` and `python3 scripts/codex-guard validate --include-untracked`.

## Scope Reminder
- Preserve Task 112 local checkout and editable package support.
- Do not publish a package in this task; make the repository release-ready and prove local wheel/package-style invocation.
- Key follow-up work is implementation of package metadata, bundled assets, external install snippets, MCP packaged startup, release policy, and CI templates.