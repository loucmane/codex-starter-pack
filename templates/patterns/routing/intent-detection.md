---
id: intent-detection-patterns
type: pattern
category: routing
title: Intent Detection Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - patterns/routing/request-analysis.md
related:
  - patterns/routing/meta-routing.md
  - patterns/selection/handler-selection.md
version: 1.0.0
status: stable
---

# Intent Detection Patterns

## Pattern Description
Patterns for detecting user intent from natural language requests, identifying the underlying goal beyond the literal words, and mapping intent to appropriate system capabilities.

## Pattern Structure
1. Extract keywords and phrases
2. Identify action verbs and objects
3. Analyze context signals
4. Map to intent categories
5. Score confidence levels
6. Route to appropriate handler

## When to Use
- User request needs interpretation
- Multiple possible interpretations exist
- Intent affects handler selection
- Context changes meaning

## When NOT to Use
- Direct command with clear intent
- System command or specific handler invoked
- Intent is explicitly stated

## Intent Categories

### Development Intent
**Signals**: create, build, implement, write, generate, develop
**Context**: Files, components, features, code
**Routes to**: Creation handlers, implementation workflows

### Investigation Intent
**Signals**: find, search, where, how, why, what
**Context**: Code, architecture, bugs, patterns
**Routes to**: Search handlers, analysis tools

### Modification Intent
**Signals**: change, update, fix, refactor, improve
**Context**: Existing code, files, configuration
**Routes to**: Edit handlers, refactoring workflows

### Validation Intent
**Signals**: test, check, verify, validate, ensure
**Context**: Code, features, requirements
**Routes to**: Testing handlers, validation tools

### Documentation Intent
**Signals**: document, explain, describe, comment
**Context**: Code, architecture, decisions
**Routes to**: Documentation handlers, explanation generators

## Detection Strategies

### Keyword Matching
1. Build intent keyword map
2. Score based on keyword presence
3. Weight by keyword position (earlier = higher)
4. Combine scores for intent classification

### Contextual Analysis
1. Check recent operations for context
2. Analyze work folder for domain
3. Review session focus for continuity
4. Adjust intent based on context

### Ambiguity Resolution
When multiple intents detected:
1. Score each possibility
2. If clear winner (>70% confidence) → proceed
3. If close scores → ask for clarification
4. If low scores → request rephrase

## Common Intent Patterns

### "Work on X"
- Primary: Development intent
- Secondary: Could be continuation
- Check: Active work exists?
- Route: work-activity or work-continuation

### "Look at X"
- Primary: Investigation intent
- Secondary: Could be review
- Check: X exists already?
- Route: search or review handlers

### "Handle X"
- Primary: Depends on X
- Secondary: Could be fix or implement
- Check: Is X a bug or feature?
- Route: Based on X nature

## Examples

### Clear Intent
- "Create login component" → Development intent (high confidence)
- "Find all TODO comments" → Investigation intent (high confidence)
- "Fix the auth bug" → Modification intent (high confidence)

### Ambiguous Intent
- "Handle authentication" → Could be create, fix, or document
- "Work on tests" → Could be write new or fix existing
- "Check the component" → Could be review, test, or validate

### Context-Dependent Intent
- "Do it again" → Intent from previous operation
- "Same for the other one" → Pattern repetition intent
- "Now the tests" → Sequential workflow intent

## Confidence Scoring

### High Confidence (>80%)
- Clear action verb + specific object
- Matches known pattern exactly
- Context reinforces interpretation

### Medium Confidence (50-80%)
- Some ambiguity in terms
- Multiple valid interpretations
- Context partially helpful

### Low Confidence (<50%)
- Vague or general terms
- No clear action or object
- Context doesn't help

## Variations

### Fast Detection
For common, clear patterns, use quick keyword matching

### Deep Analysis
For complex requests, perform full contextual analysis

### Learning Mode
Track successful intent resolutions for pattern improvement

## Related Patterns
- [Request Analysis](request-analysis.md) - Breaking down requests
- [Meta-Routing](meta-routing.md) - High-level routing
- [Handler Selection](../selection/handler-selection.md) - Choosing handlers

## Handler References
Intent detection is embedded in various handlers rather than standalone