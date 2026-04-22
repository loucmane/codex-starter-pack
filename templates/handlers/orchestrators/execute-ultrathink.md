---
id: execute-ultrathink
name: Execute Ultrathink
title: Execute Ultrathink
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
triggers:
  - "Start of ANY development request"
dependencies:
  - resolve-session-void
  - resolve-work-void
  - resolve-handler-void
tools:
  - date
version: 1.0.0
---

#### Pattern: execute-ultrathink {#execute-ultrathink}
**Triggers**: Start of ANY development request
**Pre-conditions**: 
- Development signal detected in user request
- No ULTRATHINK output yet
**Process**:
1. Output: "Let me ultrathink about this... [S:X|W:Y|H:Z|E:steps/"criteria"]"
2. Determine S (Session):
   - Run `date '+%Y%m%d'` for today's date
   - Check sessions/ for matching entry
   - If no match → S = VOID→conventions
3. Determine W (Work context):
   - Analyze request type and domain
   - Check active work folders
   - Apply W VOID rules:
     - Direct folder match → W = folder-name
     - Search/analysis → W = "investigating"
     - Review request → W = "reviewing"
     - Planning → W = "planning"
     - No match → W = VOID→workflows
4. Determine H (Handler):
   - Extract keywords from request
   - Search REGISTRY for matches
   - If unclear → H = VOID→registry
5. For each VOID value:
   - Route to appropriate resolver
   - Cannot proceed until resolved
6. Output final valid [S:W:H]
7. Continue to matched handler
**Success**: Valid [S:W:H] obtained and handler executed
**Failure**: Cannot resolve one or more values
**Examples**:
- "Create a login component" → [S:20250726|W:auth-feature|H:create-component]
- "Fix the bug" → [S:20250726|W:VOID→workflows|H:fix-bug]
- First request of day → [S:VOID→conventions|W:?|H:?]

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/execute-ultrathink.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
