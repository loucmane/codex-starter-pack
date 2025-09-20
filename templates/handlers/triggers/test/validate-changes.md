---
id: validate-changes
name: Validate Changes
role: trigger
domain: test
stability: stable
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