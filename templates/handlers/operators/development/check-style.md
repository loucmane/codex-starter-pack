---
id: check-style
name: Check Style
role: operator
domain: development
stability: stable
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