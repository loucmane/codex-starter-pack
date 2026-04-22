---
id: lost-context
name: Lost Context
title: Lost Context
role: orchestrator
type: orchestrator
domain: session
stability: stable
status: stable
triggers:
  - "I'm lost"
  - "what was I doing"
  - "confused state"
dependencies: []
tools:
  - TodoWrite
  - git
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Pattern: lost-context {#lost-context}
**Triggers**: "I'm lost", "what was I doing", confused state
**Pre-conditions**: User needs orientation
**Process**:
1. Check TodoWrite state
2. Check recent work folders
3. Run git status
4. Provide current context summary
**Success**: User reoriented
**Failure**: Suggest starting fresh
**Examples**:
- "I'm lost" → Show current state
- "What was I working on?" → Display active tasks

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/lost-context.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
