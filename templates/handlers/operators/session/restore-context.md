---
id: restore-context
name: Restore Context State
role: operator
domain: session
stability: stable
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