---
id: create-test-checkpoint
name: Create Test Checkpoint
title: Create Test Checkpoint
role: trigger
type: trigger
domain: test
stability: stable
status: stable
triggers:
  - "test X"
  - "create tests for Y"
  - "add test coverage"
dependencies: []
tools:
  - Write
  - Edit
version: 1.0.0
---

#### Handler: create-test-checkpoint {#create-test-checkpoint}
**Triggers**: "test X", "create tests for Y", "add test coverage"
**Target Pattern**: Feature or component to test
**Pre-conditions**: 
- Code exists to test
- Test framework available
**Process**:
1. Analyze code structure
2. Identify test scenarios
3. Create test structure
4. Write test cases
5. Run and verify
6. Update coverage metrics
**Success**: Tests pass, coverage improved
**Failure**: Test framework issues
**Examples**:
- "test the auth flow" → Integration tests
- "add unit tests" → Component testing

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/test/create-test-checkpoint.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
