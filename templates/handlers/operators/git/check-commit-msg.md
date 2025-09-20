---
id: check-commit-msg
name: Check Commit Message
role: operator
domain: git
stability: stable
triggers:
  - "is this commit message valid"
  - "check commit format"
  - "validate message"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: check-commit-msg {#check-commit-msg}
**Triggers**: "is this commit message valid", "check commit format", "validate message"
**Target Pattern**: Commit message to validate
**Pre-conditions**: 
- Message provided
- Format rules defined
**Process**:
1. Parse message structure
2. **PRIMARY**: Check format:
   - Type prefix (feat/fix/etc)
   - Scope (optional)
   - Description length
   - Body format
3. Validate against conventional commits
4. Check project-specific rules
5. Provide pass/fail with fixes
**Success**: Message validated
**Failure**: Format violations found
**Examples**:
- "check: feat: add auth" → Validate prefix format
- "is this message ok" → Full format check