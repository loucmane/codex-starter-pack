---
id: refactor-code
name: Refactor Code
role: trigger
domain: development
stability: stable
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