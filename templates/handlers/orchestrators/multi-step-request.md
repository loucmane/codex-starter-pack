---
id: multi-step-request
name: Multi-step Request
title: Multi-step Request
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
triggers:
  - "and then"
  - "after that"
  - "multiple verbs"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Pattern: multi-step-request {#multi-step-request}
**Triggers**: "and then", "after that", multiple verbs
**Pre-conditions**: Multiple operations requested
**Process**:
1. Parse into separate tasks
2. Create TodoWrite entries
3. Execute in sequence
**Success**: All steps completed
**Failure**: Ask to break down request
**Examples**:
- "Find bug and fix it" → Two separate operations
- "Test, fix, and commit" → Three-step process

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/multi-step-request.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
