# Task 42 Session Management Scope Reconciliation

**Captured**: 2026-05-08 13:40 CEST (`date '+%Y-%m-%d %H:%M:%S %Z %z'`)

## Context

Task 42 was created before the portable foundation work matured. Its original wording calls for a broad "SessionManager class" with persistence, restoration, archival, search, handoff, analytics, and crash recovery. The current repository already has most of that behavior spread across the portable workflow system:

- `python3 scripts/codex-task wizard kickoff` creates a compliant session file, active plan, active work-tracking folder, `sessions/current`, `plans/current`, and `sessions/state.json`.
- `python3 scripts/codex-task sessions update` and `work-tracking update --log-session` append S:W:H:E entries to current artifacts.
- `python3 scripts/codex-task work-tracking archive` moves completed task work tracking from `active/` to `archive/`.
- `python3 scripts/codex-task plan sync`, `work-tracking audit`, and `scripts/codex-guard validate --include-untracked` enforce plan/tracker/session consistency.
- `.claude/scripts/readiness.sh` now uses branch, Taskmaster, session, plan, and active work-tracking state to gate Claude mutations.

Task 42 should therefore reconcile old wording against current behavior and implement only the proven current gap.

## Original Scope Reconciliation

| Original Task 42 requirement | Current foundation state | Task 42 decision |
| --- | --- | --- |
| Create `SessionManager` class with state persistence | `sessions/state.json`, `sessions/current`, `plans/current`, and work-tracking folders already provide persisted workflow state. | Do not introduce a parallel manager class. Extend `scripts/codex-task` because it is the existing workflow entry point. |
| Implement session creation/restoration | Initial task kickoff exists, but there is no safe helper for starting a new daily session for an already-active multi-day task without recreating or archiving the task work-tracking folder. | Implement a session continuation/start helper for existing active task state. |
| Add session metadata tracking | Session frontmatter and `sessions/state.json` already record `session_id`, date, title, current pointer, and timestamp. | Reuse the existing metadata shape. |
| Create session archival process | Completed task archival already happens through `work-tracking archive`; historical session files remain under `sessions/YYYY/MM/`. | Do not move session files into a separate archive path. Keep sessions as historical records and archive task work tracking after merge. |
| Implement session search capabilities | `session-resolver.md` documents resolution formats, but runtime search is still limited and mostly internal. | Out of scope for this narrow slice; future task can add listing/search if needed. |
| Add session handoff mechanism | `HANDOFF.md`, tracker progress logs, session logs, and Serena memories are already the handoff system. | Keep using those artifacts; update this task's handoff after implementation. |
| Create session analytics | Metrics/reporting tasks already cover foundation reporting. | Out of scope. |
| Implement session recovery after crashes | Guard/audit detect missing or stale session pointers, but helpers can still infer the latest historical session when `sessions/current` is missing. | Harden current-session resolution so missing `sessions/current` does not silently write to old sessions. |

## Proven Gap

Two current behaviors need a system-level fix:

1. **Multi-day active task continuation**: The guided kickoff path always scaffolds a new active work-tracking folder. That is correct for a new task, but wrong for an existing multi-day task because task work tracking is task-scoped, not session-scoped. Agents need a helper that creates a fresh daily session while reusing the existing Task 42 work-tracking folder and active plan.
2. **Unsafe historical fallback**: `_resolve_current_session()` falls back to the latest session markdown when `sessions/current` is missing. That fallback can cause updates to land in an old session after an intentional closeout or crash. Current workflow should fail closed unless the caller explicitly passes `--session-file`.

## Implementation Boundary

Task 42 implementation should:

- Add a `python3 scripts/codex-task sessions continue` helper that:
  - validates the current branch matches `feat/task-<id>`;
  - resolves the existing active work-tracking folder for that task;
  - reuses an existing plan (`plans/current`, `--plan`, or an unambiguous task plan);
  - creates a new daily session file under `sessions/YYYY/MM/`;
  - repoints `sessions/current` to the new session and `plans/current` to the reused plan;
  - updates `sessions/state.json`;
  - logs continuation entries in the new session and tracker;
  - runs plan sync so continuation state is immediately guard-compatible.
- Harden `_resolve_current_session()` so `sessions update` refuses to infer a session from history when `sessions/state.json` exists but `sessions/current` is missing.
- Update session workflow documentation to point multi-day continuation at the helper instead of re-running `wizard kickoff` or archiving task work tracking.
- Add focused regression tests for parser support, successful continuation artifact creation, and the fail-closed missing-current behavior.

Task 42 should not:

- Create a new standalone `SessionManager` abstraction.
- Archive work tracking just to start a new daily session.
- Broaden repo-level guard semantics beyond the current task.
- Add analytics or generalized session search before the continuation safety gap is closed.

## Acceptance Evidence

- `tests/meta_workflow_guard/test_codex_task.py` covers `sessions continue` and fail-closed session updates.
- `python3 -m pytest tests/meta_workflow_guard/test_codex_task.py` passes.
- `python3 scripts/codex-task work-tracking audit` and `python3 scripts/codex-guard validate --include-untracked` pass with evidence stored under `reports/session-management-system/`.
- Taskmaster subtask `42.1` records this reconciliation, and `42.2` records the implementation/test evidence.
