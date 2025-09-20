---
id: save-context
name: Save Context State
role: operator
domain: session
stability: stable
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