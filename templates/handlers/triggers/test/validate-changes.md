---
id: validate-changes
name: Validate Changes
title: Validate Changes
role: trigger
type: trigger
domain: test
stability: stable
status: stable
triggers:
  - "verify X works"
  - "validate the changes"
  - "confirm Y is working"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: validate-changes {#validate-changes}
**Triggers**: "verify X works", "validate the changes", "confirm Y is working"
**Target Pattern**: Changes to validate
**Pre-conditions**: 
- Changes implemented
- Validation criteria clear
**Process**:
1. Identify validation points
2. Run test suites
3. Manual testing if needed
4. Check edge cases
5. Verify requirements met
6. Document results
**Success**: All validations pass
**Failure**: Issues found, document them
**Examples**:
- "verify auth works" → Full auth validation
- "validate the refactoring" → Behavior preservation

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/test/validate-changes.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
