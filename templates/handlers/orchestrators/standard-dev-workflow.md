---
id: standard-dev-workflow
name: Standard Development Workflow
title: Standard Development Workflow
role: orchestrator
type: orchestrator
domain: development
stability: stable
status: stable
triggers:
  - "implement X"
  - "add feature Y"
  - "create functionality Z"  
dependencies:
  - start-new-work
tools:
  - TodoWrite
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Handler: standard-dev-workflow {#standard-dev-workflow}
**Triggers**: "implement X", "add feature Y", "create functionality Z"
**Target Pattern**: Feature specification after action verb
**Pre-conditions**: 
- Clear feature requirements
- Work folder exists or will be created
**Process**:
1. If no work folder, route to start-new-work first
2. Break down into implementation steps
3. Create detailed todos
4. Begin with research/exploration
5. Follow TDD if applicable
6. Document as you go
**Success**: Feature implemented with tests and docs
**Failure**: Requirements unclear, needs clarification
**Examples**:
- "implement user login" → Full auth flow
- "add dark mode" → Theme system implementation

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/standard-dev-workflow.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
