---
id: update-todos
name: Update Todos
role: trigger
domain: workflow
stability: stable
triggers:
  - "mark X as done"
  - "update task Y"
  - "Z is complete"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---

#### Handler: update-todos {#update-todos}
**Triggers**: "mark X as done", "update task Y", "Z is complete"
**Target Pattern**: Task identifier or description
**Pre-conditions**: 
- Task exists in TodoWrite
- Valid status transition
**Process**:
1. Find matching task(s)
2. Update status appropriately
3. Check for dependent tasks
4. Update any blockers
5. Show updated task list
**Success**: Task status updated
**Failure**: No matching task found
**Examples**:
- "mark auth tests as done" → Updates specific task
- "API integration is complete" → Finds and updates task