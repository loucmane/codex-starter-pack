---
id: refactor-code
name: Refactor Code
title: Refactor Code
role: trigger
type: trigger
domain: development
stability: stable
status: stable
triggers:
  - "refactor X"
  - "clean up Y"
  - "improve Z code"
dependencies: []
tools:
  - Read
  - Edit
version: 1.0.0
---

#### Handler: refactor-code {#refactor-code}
**Triggers**: "refactor X", "clean up Y", "improve Z code"
**Target Pattern**: Code location or pattern to refactor
**Pre-conditions**: 
- Code exists and is working
- Tests exist (or will be added first)
**Process**:
1. Analyze current implementation
2. Identify refactoring opportunities
3. Ensure tests cover current behavior
4. Apply refactoring patterns
5. Verify tests still pass
6. Update documentation
**Success**: Cleaner code, same behavior, tests pass
**Failure**: No tests exist, add tests first
**Examples**:
- "refactor the auth service" → Service pattern improvements
- "clean up the API calls" → Extract to service layer

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/development/refactor-code.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
