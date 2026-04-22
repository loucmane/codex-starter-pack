---
id: template-navigation-protocol
title: Template Navigation Protocol
type: engine-component
status: stable
---

# Template Navigation Protocol

## Overview
This protocol defines how to navigate the template system to find and execute the right handler for any request.

## Navigation Steps

### 1. Quick Intent Check
```
Is this casual chat? → Skip to natural response
Is this development work? → Continue to step 2
```

**Decision Criteria:**
- Casual chat: General questions, non-technical discussion
- Development work: Any code, file, or system-related request

### 2. Find the Right Handler

#### Initial Search Strategy
```
Search the REGISTRY for the appropriate handler:

First, check Navigation Keywords for common patterns:
mcp__serena__search_for_pattern --substring_pattern "[action keyword]" --relative_path "templates/registry"
```

#### Fallback Search
If no exact match, extract keywords and search more broadly:
- **Extract key verbs**: work, fix, search, edit, etc.
- **Extract key nouns**: bug, feature, component, etc.
- **Search command**: 
  ```
  mcp__serena__search_for_pattern --substring_pattern "[keyword]" --relative_path "templates/registry"
  ```

### 3. Load Handler from Template Using Anchors

#### Direct Loading (Preferred)
Once handler found in REGISTRY, load it using:
```
If exact path known:
Read --file_path "templates/handlers/[role]/[domain]/[handler-name].md"
```

#### Search-Based Loading
If path uncertain:
```
mcp__serena__search_for_pattern --substring_pattern "id: handler-name" --relative_path "templates/handlers/"
```

#### Example: Loading `start-new-work` Handler
```
1. Registry shows: [start-new-work](handlers/triggers/development/start-new-work.md)
2. Direct load: Read --file_path "templates/handlers/triggers/development/start-new-work.md"
3. Or search: mcp__serena__search_for_pattern --substring_pattern "id: start-new-work" --relative_path "templates/handlers/"
```

### 4. Execute Handler Completely
Follow the loaded handler's Process steps exactly, using specified tools and conventions.

## Handler Path Structure

### Path Components
```
templates/handlers/[role]/[domain]/[handler-name].md
```

- **role**: triggers, orchestrators, operators
- **domain**: development, git, search, debug, test, docs, workflow
- **handler-name**: kebab-case identifier

### Role-Based Organization
- **triggers/**: User-facing entry points
- **orchestrators/**: Multi-handler coordinators
- **operators/**: Single-purpose executors

## Search Optimization

### Search Priority
1. **Exact match** in Navigation Keywords
2. **Action verb** matching
3. **Domain noun** matching
4. **Broad pattern** search
5. **Fallback** to templates/patterns/

### Performance Tips
- Cache frequently used handler paths
- Use direct paths when known
- Batch related searches
- Prefer templates/registry with Serena over raw file searches

## Error Recovery

### Handler Not Found
1. Try alternative keywords
2. Check templates/patterns/ for meta-routing
3. Use broader search terms
4. Ask user for clarification

### Invalid Handler Path
1. Verify path structure
2. Check handler ID format
3. Search by content if path fails
4. Report missing handler

## Integration Points

### Dependencies
- **REGISTRY.md**: Master handler index
- **handlers/**: Handler storage
- **templates/patterns/**: Meta-routing patterns
- **templates/conventions/**: Naming standards

### Output Format
After successful navigation:
```
Found: [handler-name] ([template-path]#[anchor])
Loading handler...
Executing [N] steps...
```

## Best Practices

### DO
- Always check REGISTRY first
- Use exact paths when known
- Verify handler exists before loading
- Show search results for transparency

### DON'T
- Skip intent checking
- Guess handler names
- Load without verification
- Hide navigation decisions

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/navigation/template-protocol.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
