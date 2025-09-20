---
id: check-conventions-first
name: Check Conventions First
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "Internal trigger before any action that has conventions"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: check-conventions-first {#check-conventions-first}
**Triggers**: Internal trigger before any action that has conventions
**Target Pattern**: Action type to check conventions for
**Pre-conditions**: 
- About to perform an action
- Convention may exist for action
**Process**:
1. **MANDATORY FIRST STEP**: Identify action type:
   - Git operations → Check Git Conventions
   - File naming → Check Naming Conventions
   - Code writing → Check Code Conventions
   - Tool usage → Check Tool Router
   - Timestamps → Check timestamp format
2. **PRIMARY**: Read relevant convention section
3. Extract specific rules for action
4. Apply rules to intended action
5. Proceed only if compliant
**Success**: Convention checked before action
**Failure**: No convention check → STOP and check
**Examples**:
- Before commit message → Check git conventions first
- Before creating file → Check naming conventions first
- Before using tool → Check tool router first