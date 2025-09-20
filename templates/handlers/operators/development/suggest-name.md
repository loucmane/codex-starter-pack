---
id: suggest-name
name: Suggest Name
role: operator
domain: development
stability: stable
triggers:
  - "what should I call X"
  - "suggest name for Y"
  - "naming ideas for Z"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: suggest-name {#suggest-name}
**Triggers**: "what should I call X", "suggest name for Y", "naming ideas for Z"
**Target Pattern**: Thing needing a name
**Pre-conditions**: 
- Purpose is clear
- Context available
**Process**:
1. Understand purpose and context
2. **PRIMARY**: Use Serena to find similar items
3. Extract naming patterns
4. Apply conventions:
   - Correct case style
   - Meaningful prefixes
   - Domain terminology
5. Generate 3-5 suggestions
6. Explain reasoning for each
**Success**: Quality name suggestions provided
**Failure**: Need more context
**Examples**:
- "name for auth helper" → `validateToken`, `checkAuth`
- "suggest test file name" → `auth.test.ts`, `auth.spec.ts`