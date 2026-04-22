---
id: review-patterns
name: Review Patterns
title: Review Patterns
role: operator
type: operator
domain: development
stability: stable
status: stable
triggers:
  - "is this idiomatic"
  - "check patterns"
  - "review approach"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: review-patterns {#review-patterns}
**Triggers**: "is this idiomatic", "check patterns", "review approach"
**Target Pattern**: Code pattern to review
**Pre-conditions**: 
- Pattern identifiable
- Best practices known
**Process**:
1. Identify pattern type
2. **PRIMARY**: Use Serena to find examples
3. Compare against:
   - Language idioms
   - Framework patterns
   - Project conventions
4. Assess idiomaticity
5. Suggest improvements
**Success**: Pattern assessed with alternatives
**Failure**: Novel pattern, needs discussion
**Examples**:
- "is this React pattern idiomatic" → Check hooks usage
- "review error handling" → Validate try/catch patterns

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/development/review-patterns.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
