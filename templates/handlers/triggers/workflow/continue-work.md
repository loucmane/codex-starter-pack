---
id: continue-work
name: Continue Work
title: Continue Work
role: trigger
type: trigger
domain: workflow
stability: stable
status: stable
triggers:
  - "continue with X"
  - "back to Y"
  - "resume Z"
dependencies: []
tools:
  - TodoRead
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Handler: continue-work {#continue-work}
**Triggers**: "continue with X", "back to Y", "resume Z"
**Target Pattern**: Extract work identifier after key verb
**Pre-conditions**: 
- Existing work folder must exist
- sessions/ has record of work
**Process**:
1. Search for matching work folder
2. Read current state from TRACKER.md
3. Check TodoWrite for in-progress items
4. Show current status to user
5. Resume from last checkpoint
**Success**: Previous context restored, work resumed
**Failure**: No matching work found, show available options
**Examples**:
- "continue with auth" → Finds *-authentication-ACTIVE folder
- "back to the flow creator" → Resumes meta-flow-creator work

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/workflow/continue-work.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
