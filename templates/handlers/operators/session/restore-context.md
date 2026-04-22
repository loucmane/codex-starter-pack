---
id: restore-context
name: Restore Context State
title: Restore Context State
role: operator
type: operator
domain: session
stability: stable
status: stable
triggers:
  - "resume work"
  - "continue from"
  - "pick up where"
dependencies: []
tools:
  - work folder files
version: 1.0.0
---

#### Handler: restore-context {#restore-context}
**Triggers**: "resume work", "continue from", "pick up where"
**Target Pattern**: Previous state to restore
**Pre-conditions**: 
- Saved state exists
- No conflicting active work
**Process**:
1. **PRIMARY**: Read work folder files
2. Load todos and progress
3. Restore file context
4. Show last actions
**Success**: Context restored, ready to continue
**Failure**: Partial restore, need user guidance
**Examples**:
- "continue yesterday's work" → Load from work folder
- "resume feature X" → Restore full context

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/session/restore-context.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
