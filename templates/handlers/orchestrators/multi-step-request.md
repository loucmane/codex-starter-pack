---
id: multi-step-request
name: Multi-step Request
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "and then"
  - "after that"
  - "multiple verbs"
dependencies: []
tools:
  - TodoWrite
version: 1.0.0
---

#### Pattern: multi-step-request {#multi-step-request}
**Triggers**: "and then", "after that", multiple verbs
**Pre-conditions**: Multiple operations requested
**Process**:
1. Parse into separate tasks
2. Create TodoWrite entries
3. Execute in sequence
**Success**: All steps completed
**Failure**: Ask to break down request
**Examples**:
- "Find bug and fix it" → Two separate operations
- "Test, fix, and commit" → Three-step process