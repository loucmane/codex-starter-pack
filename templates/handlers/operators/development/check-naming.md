---
id: check-naming
name: Check Naming
title: Check Naming
role: operator
type: operator
domain: development
stability: stable
status: stable
triggers:
  - "is X named correctly"
  - "check naming of Y"
  - "validate name Z"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: check-naming {#check-naming}
**Triggers**: "is X named correctly", "check naming of Y", "validate name Z"
**Target Pattern**: Name to validate
**Pre-conditions**: 
- Name type identifiable
- Conventions documented
**Process**:
1. Identify name type:
   - File/folder
   - Function/method
   - Variable/constant
   - Component/class
2. **PRIMARY**: Check against conventions:
   - Read naming section
   - Apply specific rules
   - Check similar examples
3. Use Serena to find patterns
4. Compare and validate
5. Provide verdict with reasoning
**Success**: Clear pass/fail with explanation
**Failure**: Ambiguous case, show options
**Examples**:
- "is getUserData named correctly" → Check camelCase convention
- "validate component name" → Check PascalCase rule

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/development/check-naming.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
