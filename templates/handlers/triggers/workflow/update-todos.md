---
id: update-todos
name: Update Todos
title: Update Todos
role: trigger
type: trigger
domain: workflow
stability: stable
status: stable
triggers:
  - "mark X as done"
  - "update task Y"
  - "Z is complete"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/workflow/update-todos.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
