---
id: session-continuation-workflow
type: workflow-component
category: session
title: Session Continuation Workflow
dependencies:
  - templates/patterns/session/continuation-patterns.md
  - templates/handlers/orchestrators/work-continuation.md
  - templates/handlers/operators/session/restore-context.md
related:
  - templates/workflows/session/lifecycle.md
  - templates/workflows/session/state-management.md
version: 1.0.0
status: stable
---
> **Codex Equivalent:** Continuation requires the active plan (Taskmaster alignment) and tracker to be in sync; use `python3 scripts/codex-task plan sync` to refresh hashes and treat Taskmaster subtasks as the primary work queue.


# Session Continuation Workflow

## Purpose
Ensure smooth resumption of in-progress work without losing context, evidence, or state.

## Preconditions
- Previous session entry exists in `sessions/`
- Work-tracking folder contains current state
- Serena memory (if used) recorded for last checkpoint

## Steps
1. **Confirm continuation request**
   - Identify session ID (`sessions/current` or ULTRATHINK S field)
   - Verify task/work context with user
2. **Load prior context**
   - Read latest session log section (including Next Actions)
   - Review work-tracking tracker + handoff
   - Read latest Serena memory (if available)
3. **Restore state**
   - For a new daily session on an already-active task, run `python3 scripts/codex-task sessions continue --task <id> --slug <slug> --title "<title>"`. This creates a fresh session while reusing the task-scoped ACTIVE work-tracking folder and existing plan.
   - Do not rerun `python3 scripts/codex-task wizard kickoff` for an already-active multi-day task; kickoff is for initial task scaffolding and will try to create a new ACTIVE work-tracking folder.
   - Do not archive active work tracking just to start a new daily session. Archive only after the task/PR is complete.
   - After continuation state exists, use `python3 scripts/codex-task sessions update ...` for progress entries.
   - Ensure `python3 scripts/codex-task plan sync` has been recorded this session (plan-step scope/updates)
   - Review Taskmaster task status (`task-master show <id>`) and set active subtasks to `in-progress`
   - Execute `python3 scripts/codex-guard validate --include-untracked` before editing
4. **Bridge gaps**
   - Compare Git diff vs. documented work and plan scope
   - Run targeted tests or scanners if time gap or divergence detected
   - Update work-tracking (tracker, findings, decisions) with new context
5. **Resume work**
   - Execute handler chain (`work-continuation` orchestrator → session operators + continuation validation behavior)
   - Confirm S:W:H:E is current and reference continuation guard log
   - Begin next subtask with evidence logging (session + tracker entries)

## Evidence Requirements
- Session log entry referencing continuation handler + timestamp (include guard command used)
- Tracker update indicating resumed subtask and guard status
- Guard log stored under `reports/session-continuation/` for the resumption
- Serena memory reference when Serena is active (record ID in MEMORY-REFS)
- Tests or scanner outputs when gap exceeded 4 hours or code changed elsewhere

## Failure Modes & Recovery
- **Missing session entry** → run `resolve-session-void`
- **Missing `sessions/current` with an existing ACTIVE work-tracking folder** → run `python3 scripts/codex-task sessions continue --task <id> --slug <slug>`; do not infer the latest historical session.
- **Work context unclear** → consult `work-patterns` and Taskmaster history (plan + tracker)
- **State mismatch** → reconcile Git diff, rerun tests, update documentation
- **Serena memory missing** → reconstruct from session + tracker, document in Findings

## Completion Criteria
- Active session log updated with current time + "continuing" (including guard evidence)
- Tracker reflects resumed status, guard validation, and next steps
- Plan/tracker sync recorded in `.plan_state/sync.log` after continuation
- Serena memory (if applicable) updated after new work segment

## Related Handlers & Patterns
- `handlers/orchestrators/work-continuation.md`
- `handlers/operators/session/restore-context.md`
- `patterns/session/continuation-patterns.md`

## Progress Log

- **2026-05-08 13:52** — [S:20260508|W:task42-session-management-system|H:templates/workflows/session/continuation.md|E:docs/ai/work-tracking/active/20260508-task42-session-management-system-ACTIVE/designs/session-management-scope-reconciliation.md] Documented `sessions continue` as the safe multi-day task continuation path and clarified that active task work tracking must not be archived just to start a new daily session.
