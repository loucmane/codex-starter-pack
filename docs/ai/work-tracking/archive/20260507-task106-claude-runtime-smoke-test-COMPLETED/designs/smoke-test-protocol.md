# Task 106 Claude Runtime Smoke-Test Protocol

## Purpose

Task 106 validates the Claude runtime adapter in the real Claude Code harness, not only through local unit tests. The acceptance question is behavioral: a fresh Claude session must be blocked from hookable persistent mutations before workflow scaffolding exists, and then must be able to perform allowed work only after the normal session/plan/work-tracking state is present.

## Phase 1: Cold Session Before Scaffold

Initial state:
- Branch: `feat/task-106-claude-runtime-smoke-test`
- Taskmaster Task 106 exists and is `in-progress`
- No `sessions/current`
- No `plans/current`
- No `docs/ai/work-tracking/active/*-ACTIVE/`

Expected behavior:
- Read-only inspection is allowed.
- `bash .claude/scripts/readiness.sh --quick` returns `BLOCKED`.
- `Write` to a normal project file is blocked.
- `Bash` redirect to a normal project file is blocked.
- `Edit` of protected Codex-owned paths is blocked while readiness is `BLOCKED`.
- Claude does not attempt workarounds.

Phase 1 evidence:
- `reports/claude-runtime-smoke-test/phase1-cold-session-2026-05-07.md`

## Phase 2: READY Session After Scaffold

Initial state:
- `python3 scripts/codex-task wizard kickoff` has created the Task 106 session, plan, active work-tracking folder, and current symlinks.
- `bash .claude/scripts/readiness.sh --quick` returns `READY | task=106`.

Expected behavior:
- Allowed writes to Task 106-owned work-tracking evidence files are permitted.
- Protected Codex-owned paths still block with a path-ownership/protected-path reason, independent of readiness.
- Bash writes to protected paths still block.
- Mutating Taskmaster or MCP surfaces that the adapter classifies as guarded either block when not allowed or are explicitly recorded as follow-up limitations.

Phase 2 evidence target:
- `reports/claude-runtime-smoke-test/phase2-ready-session-2026-05-07.md`

## Completion Criteria

- Phase 1 cold-session evidence passes and is recorded.
- Phase 2 READY-state evidence passes or produces explicit follow-up defects.
- Taskmaster subtasks 106.1, 106.2, and 106.3 reflect the actual smoke-test outcome.
- `python3 scripts/codex-task plan sync` passes.
- `python3 scripts/codex-task work-tracking audit` passes or only reports expected active Task 106 state.
- `python3 scripts/codex-guard validate --include-untracked` passes before final commit.
