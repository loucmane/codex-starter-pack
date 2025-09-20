---
id: meta-routing-patterns
type: pattern
category: routing
title: Meta-Routing Patterns
pattern_type: behavioral
complexity: complex
dependencies:
  - templates/shared/patterns/ultrathink-format.md
  - templates/conventions/
  - templates/REGISTRY.md
related:
  - patterns/routing/request-analysis.md
  - patterns/routing/intent-detection.md
version: 1.0.0
status: stable
---

# Meta-Routing Patterns

## Pattern Description
High-level routing patterns that determine which handler or system component should process a request. These patterns act as the initial router, analyzing requests and delegating to appropriate handlers.

## Pattern Structure

### Pattern Matching Rules
1. Check triggers in order (most specific first)
2. First match wins
3. Load pattern's routing rules
4. Delegate to referenced handlers

### ULTRATHINK Integration
This pattern participates in the ULTRATHINK system:

#### VOID Resolution
- **S = VOID** → Route to [resolve-session-void](../../conventions/#resolve-session-void)
- **W = VOID** → Route to [resolve-work-void](../../workflows/#resolve-work-void)
- **H = VOID** → Route to [resolve-handler-void](../../REGISTRY.md#resolve-handler-void)

Meta-patterns help resolve ambiguous requests. When H = VOID due to unclear intent, these patterns identify the appropriate handler.

## Core Pattern: Execute ULTRATHINK

### When to Use
- Start of ANY development request
- Development signal detected in user request
- No ULTRATHINK output yet

### Process
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

### Success Criteria
Valid [S:W:H] obtained and handler executed

### Failure Modes
Cannot resolve one or more values

## Examples

### Development Request
- Input: "Create a login component"
- Output: [S:20250726|W:auth-feature|H:create-component]

### Ambiguous Request
- Input: "Fix the bug"
- Output: [S:20250726|W:VOID→workflows|H:fix-bug]

### First Request of Day
- Input: Any development request
- Output: [S:VOID→conventions|W:?|H:?]

## Variations
- **Quick routing**: When handler is obvious, skip detailed analysis
- **Deep analysis**: For complex requests, perform thorough keyword extraction
- **Fallback routing**: When primary route fails, use secondary patterns

## Related Patterns
- [Request Analysis](request-analysis.md) - Detailed request parsing
- [Intent Detection](intent-detection.md) - Understanding user intent
- [Handler Selection](../selection/handler-selection.md) - Choosing specific handlers

## Handler References
[Handler: execute-ultrathink migrated to handlers/orchestrators/ultrathink-executor.md]