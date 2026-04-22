---
id: ambiguous-request
name: Ambiguous Request
title: Ambiguous Request
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
triggers:
  - "vague terms like \"it\""
  - "that"
  - "this"
  - "the thing"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Pattern: ambiguous-request {#ambiguous-request}
**Triggers**: vague terms like "it", "that", "this", "the thing"
**Pre-conditions**: Context unclear
**Process**:
1. Check TodoWrite for active context
2. Check recent operations
3. If still unclear → Ask for clarification
**Success**: Context resolved
**Failure**: "Could you clarify what you're referring to?"
**Examples**:
- "Fix it" → Check what "it" refers to
- "Update that" → Resolve "that" from context

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/ambiguous-request.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
