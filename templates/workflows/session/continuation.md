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
   - Run `python3 scripts/codex-task sessions update --resume`
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
