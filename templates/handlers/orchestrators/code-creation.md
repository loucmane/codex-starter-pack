---
id: code-creation
name: Code Creation
title: Code Creation
role: orchestrator
type: orchestrator
domain: development
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/code-creation.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
