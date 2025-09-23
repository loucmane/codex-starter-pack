---
id: check-progress
name: Check Progress
role: trigger
domain: workflow
stability: stable
triggers:
  - "where are we?"
  - "what's left?"
  - "show progress"
dependencies: []
tools:
  - TodoRead
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Handler: check-progress {#check-progress}
**Triggers**: "where are we?", "what's left?", "show progress"
**Target Pattern**: Optional scope filter
**Pre-conditions**: 
- Active todos exist
- Work context established  
**Process**:
1. Read current todos
2. Calculate completion percentage
3. Identify blockers
4. Show completed/remaining breakdown
5. Highlight next priorities
**Success**: Clear progress summary shown
**Failure**: No active tasks found
**Examples**:
- "where are we?" → Overall progress summary
- "what's left on auth?" → Filtered progress view