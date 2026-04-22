---
id: create-todos
name: Create Todos
title: Create Todos
role: trigger
type: trigger
domain: workflow
stability: stable
status: stable
triggers:
  - "plan out X"
  - "break down Y"
  - "create tasks for Z"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Handler: create-todos {#create-todos}
**Triggers**: "plan out X", "break down Y", "create tasks for Z"
**Target Pattern**: Work item to decompose
**Pre-conditions**: 
- Clear understanding of overall goal
- TodoWrite tool available
**Process**:
1. Analyze work scope
2. Break into logical phases
3. Create hierarchical task structure
4. Set appropriate priorities
5. Add to TodoWrite
6. Show task breakdown to user
**Success**: Comprehensive task list created
**Failure**: Scope unclear, needs discussion
**Examples**:
- "plan out the migration" → Detailed migration steps
- "break down the feature" → Implementation tasks

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/workflow/create-todos.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
