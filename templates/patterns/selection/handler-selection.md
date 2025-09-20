---
id: handler-selection-patterns
type: pattern
category: selection
title: Handler Selection Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - templates/REGISTRY.md
  - patterns/routing/intent-detection.md
related:
  - patterns/selection/tool-selection.md
  - patterns/selection/agent-selection.md
version: 1.0.0
status: stable
---

# Handler Selection Patterns

## Pattern Description
Patterns for choosing the right handler based on user request, context, and system state. These patterns ensure the most appropriate handler is selected for each situation.

## Pattern Structure
1. Parse request for handler signals
2. Search REGISTRY for matches
3. Score candidates by relevance
4. Consider context and constraints
5. Select best match
6. Load and execute handler

## When to Use
- Selecting between multiple possible handlers
- Request matches multiple handler triggers
- Context affects handler choice
- Handler capabilities need matching to requirements

## When NOT to Use
- Direct handler invocation requested
- Only one possible handler matches
- Emergency or error conditions (use fallback)

## Selection Criteria

### Primary Criteria
1. **Trigger Match**: Does request match handler triggers?
2. **Capability Match**: Can handler fulfill the request?
3. **Context Match**: Is handler appropriate for current context?
4. **Availability**: Is handler accessible and stable?

### Secondary Criteria
1. **Specificity**: More specific handlers preferred over general
2. **Stability**: Stable handlers preferred over experimental
3. **Performance**: Faster handlers for time-sensitive requests
4. **Recency**: Recently updated handlers for new features

## Selection Process

### Step 1: Candidate Discovery
```
1. Extract keywords from request
2. Search REGISTRY.md for keyword matches
3. Build candidate list with all matches
4. Filter by basic constraints (stability, availability)
```

### Step 2: Scoring
For each candidate handler:
- **Trigger match score** (0-40 points)
  - Exact match: 40
  - Partial match: 20
  - Keyword match: 10
- **Context score** (0-30 points)
  - Perfect context: 30
  - Related context: 15
  - No context needed: 10
- **Specificity score** (0-20 points)
  - Highly specific: 20
  - Moderately specific: 10
  - General purpose: 5
- **Stability score** (0-10 points)
  - Stable: 10
  - Beta: 5
  - Experimental: 2

### Step 3: Selection
1. Rank candidates by total score
2. If top score > 70: Select winner
3. If top scores tied: Apply tiebreakers
4. If all scores < 50: Request clarification

## Handler Categories

### Trigger Handlers
- Respond to specific user phrases
- High specificity, direct mapping
- Example: "create component" → create-component handler

### Orchestrator Handlers
- Coordinate multiple operations
- Complex workflows, multiple steps
- Example: "migrate system" → migration-orchestrator

### Operator Handlers
- Perform specific technical tasks
- Tool-focused, single responsibility
- Example: "search code" → code-search-operator

## Conflict Resolution

### Multiple High Scores
When multiple handlers score similarly:
1. Prefer more specific handler
2. Prefer stable over experimental
3. Prefer handler with better context match
4. If still tied, ask user to choose

### No Good Matches
When no handler scores well:
1. Check for typos or variations
2. Try broader search terms
3. Suggest closest matches
4. Offer to create new handler

## Examples

### Clear Selection
- Request: "Create a React component"
- Candidates: create-component (95), generic-create (60)
- Selection: create-component (clear winner)

### Ambiguous Selection
- Request: "Fix the issue"
- Candidates: fix-bug (65), fix-error (63), fix-typo (60)
- Action: Ask "What type of issue?"

### Context-Dependent Selection
- Request: "Continue"
- Context: In testing workflow
- Selection: continue-testing (context boost)

## Optimization Strategies

### Caching
- Cache frequently used handler mappings
- Invalidate on REGISTRY updates
- Store session-specific preferences

### Learning
- Track successful selections
- Adjust scoring weights based on success
- Build user-specific preferences

### Fallback Chain
1. Primary: Exact handler match
2. Secondary: Pattern-based match
3. Tertiary: General purpose handler
4. Final: Ask for clarification

## Variations

### Quick Selection
For obvious matches, skip scoring and select immediately

### Deep Analysis
For complex requests, perform full scoring with context analysis

### Interactive Selection
Present top candidates to user for manual selection

## Related Patterns
- [Tool Selection](tool-selection.md) - Choosing appropriate tools
- [Agent Selection](agent-selection.md) - Selecting specialist agents
- [Intent Detection](../routing/intent-detection.md) - Understanding request intent

## Handler References
[Handler: Multiple handlers implement selection logic internally]