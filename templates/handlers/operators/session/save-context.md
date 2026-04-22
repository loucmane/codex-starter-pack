---
id: save-context
name: Save Context State
title: Save Context State
role: operator
type: operator
domain: session
stability: stable
status: stable
triggers:
  - "save state"
  - "checkpoint progress"
  - "switching tasks"
dependencies: []
tools:
  - work tracking files
  - memory snapshot
version: 1.0.0
---

#### Handler: save-context {#save-context}
**Triggers**: "save state", "checkpoint progress", switching tasks
**Target Pattern**: Current state needs preservation
**Pre-conditions**: 
- Active work in progress
- State worth preserving
**Process**:
1. Gather current context (todos, files, decisions)
2. **PRIMARY**: Update work tracking files
3. **FALLBACK**: Create memory snapshot
4. Mark resumption point
**Success**: State saved for easy resume
**Failure**: Partial save with warnings
**Examples**:
- Before switching tasks → Save to handoff.md
- Mid-session checkpoint → Update tracker.md

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/session/save-context.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
