---
id: request-analysis-patterns
type: pattern
category: routing
title: Request Analysis Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - patterns/routing/meta-routing.md
related:
  - patterns/routing/intent-detection.md
  - patterns/selection/handler-selection.md
version: 1.0.0
status: stable
---

# Request Analysis Patterns

## Pattern Description
Patterns for analyzing and parsing user requests to extract actionable information, resolve ambiguity, and break down complex requests into manageable operations.

## Pattern Structure
1. Parse request for key terms and context
2. Identify ambiguous references
3. Resolve or clarify unclear elements
4. Extract actionable components
5. Route to appropriate handlers

## When to Use
- Request contains vague references ("it", "that", "this")
- Multiple operations requested in single input
- Context needs to be resolved from previous operations
- Request structure needs decomposition

## When NOT to Use
- Request is clear and unambiguous
- Single, well-defined operation requested
- Context is already established

## Ambiguous Request Pattern

### Structure
**Triggers**: vague terms like "it", "that", "this", "the thing"
**Pre-conditions**: Context unclear

### Process
1. Check TodoWrite for active context
2. Check recent operations
3. If still unclear → Ask for clarification

### Success Criteria
Context successfully resolved from available information

### Failure Mode
"Could you clarify what you're referring to?"

### Examples
- "Fix it" → Check what "it" refers to from recent context
- "Update that" → Resolve "that" from previous operations
- "The thing we discussed" → Check conversation history

## Multi-Step Request Pattern

### Structure
**Triggers**: "and then", "after that", multiple verbs, compound sentences
**Pre-conditions**: Multiple operations requested

### Process
1. Parse into separate tasks
2. Create TodoWrite entries for each task
3. Execute in sequence
4. Track completion of each step

### Success Criteria
All steps completed in correct order

### Failure Mode
Ask user to break down complex request

### Examples
- "Find bug and fix it" → Two separate operations: search then repair
- "Test, fix, and commit" → Three-step process with dependencies
- "Create component then add tests" → Sequential development tasks

## Request Decomposition Strategy

### For Compound Requests
1. Identify action verbs (create, update, fix, test)
2. Extract objects (files, components, features)
3. Note sequencing words (then, after, before)
4. Build operation dependency graph
5. Execute in topological order

### For Ambiguous References
1. Build context window from:
   - Current TodoWrite state
   - Recent file operations
   - Active work folder
   - Previous request/response
2. Score potential matches
3. Select highest confidence match
4. Confirm if confidence < 80%

## Variations

### Quick Resolution
When context is recent and obvious, skip extensive searching

### Deep Context Search
For unclear references, search through:
- Work tracking files
- Session history
- Git history
- Recent operations

### Interactive Clarification
When automated resolution fails:
1. Present potential matches
2. Ask for specific selection
3. Remember choice for session

## Related Patterns
- [Meta-Routing](meta-routing.md) - High-level routing decisions
- [Intent Detection](intent-detection.md) - Understanding user goals
- [Session Patterns](../session/session-patterns.md) - Maintaining context

## Handler References
[Handler: ambiguous-request migrated to handlers/orchestrators/request-clarifier.md]
[Handler: multi-step-request migrated to handlers/orchestrators/multi-step-executor.md]