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
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


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
   - Run `codex-task sessions update --resume`
   - Reload active TodoWrite tasks (set current item `in_progress`)
   - Execute `codex-guard validate --include-untracked`
4. **Bridge gaps**
   - Compare Git diff vs. documented work
   - Run targeted tests or scans if time gap or uncertainty
   - Update work-tracking with any newly discovered context
5. **Resume work**
   - Execute handler chain (`work-continuation` orchestrator → session operators)
   - Confirm S:W:H:E is current
   - Begin next subtask with evidence logging

## Evidence Requirements
- Session log entry referencing continuation handler + timestamp
- Tracker update indicating resumed subtask
- Tests or scanner outputs when gap exceeded 4 hours or code changed elsewhere

## Failure Modes & Recovery
- **Missing session entry** → run `resolve-session-void`
- **Work context unclear** → consult `work-patterns` and TodoWrite history
- **State mismatch** → reconcile Git diff, rerun tests, update documentation
- **Serena memory missing** → reconstruct from session + tracker, document in Findings

## Completion Criteria
- Active session log updated with current time + "continuing"
- Tracker reflects resumed status and next steps
- Serena memory (if applicable) updated after new work segment

## Related Handlers & Patterns
- `handlers/orchestrators/work-continuation.md`
- `handlers/operators/session/restore-context.md`
- `patterns/session/continuation-patterns.md`
