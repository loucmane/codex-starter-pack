---
id: code-creation
name: Code Creation
role: orchestrator
domain: development
stability: stable
triggers:
  - "create"
  - "write"
  - "generate"
  - "implement"
  - "build component"
dependencies: []
tools:
  - Edit
  - Write
version: 1.0.0
---

#### Pattern: code-creation {#code-creation}
**Triggers**: create, write, generate, implement, build component
**Pre-conditions**: Clear what to create
**Process**:
1. Check existing patterns/conventions
2. Use Edit/Write tools (NEVER Serena)
3. Follow TDD if applicable
**Success**: Code created following conventions
**Failure**: Ask for specifications
**Examples**:
- "Create login component" → Write with conventions
- "Generate test file" → Follow test patterns