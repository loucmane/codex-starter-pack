---
id: review-patterns
name: Review Patterns
role: operator
domain: development
stability: stable
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