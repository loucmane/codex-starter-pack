---
id: ambiguous-request
name: Ambiguous Request
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "vague terms like \"it\""
  - "that"
  - "this"
  - "the thing"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---

#### Pattern: ambiguous-request {#ambiguous-request}
**Triggers**: vague terms like "it", "that", "this", "the thing"
**Pre-conditions**: Context unclear
**Process**:
1. Check TodoWrite for active context
2. Check recent operations
3. If still unclear → Ask for clarification
**Success**: Context resolved
**Failure**: "Could you clarify what you're referring to?"
**Examples**:
- "Fix it" → Check what "it" refers to
- "Update that" → Resolve "that" from context