---
id: check-progress
name: Check Progress
title: Check Progress
role: trigger
type: trigger
domain: workflow
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/workflow/check-progress.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
