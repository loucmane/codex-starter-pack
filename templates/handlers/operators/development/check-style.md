---
id: check-style
name: Check Style
title: Check Style
role: operator
type: operator
domain: development
stability: stable
status: stable
triggers:
  - "does X follow conventions"
  - "check style of Y"
  - "review code style"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: check-style {#check-style}
**Triggers**: "does X follow conventions", "check style of Y", "review code style"
**Target Pattern**: Code to style-check
**Pre-conditions**: 
- Code accessible
- Style rules defined
**Process**:
1. Read code section
2. **PRIMARY**: Apply style checks:
   - Indentation (spaces/tabs)
   - Line length
   - Brace style
   - Comment format
3. Use Serena for pattern comparison
4. Check against linter rules
5. List all violations found
**Success**: Style issues identified
**Failure**: Style rules unclear
**Examples**:
- "check function style" → Validate formatting
- "does this follow conventions" → Full style review

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/development/check-style.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
