---
id: check-commit-msg
name: Check Commit Message
title: Check Commit Message
role: operator
type: operator
domain: git
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/git/check-commit-msg.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
