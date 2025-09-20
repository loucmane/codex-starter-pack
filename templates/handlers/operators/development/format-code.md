---
id: format-code
name: Format Code
role: operator
domain: development
stability: stable
triggers:
  - "format X properly"
  - "fix formatting"
  - "clean up style"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: format-code {#format-code}
**Triggers**: "format X properly", "fix formatting", "clean up style"
**Target Pattern**: Code needing formatting
**Pre-conditions**: 
- Code readable
- Format rules clear
**Process**:
1. Identify code boundaries
2. **PRIMARY**: Determine format rules:
   - Language-specific
   - Project preferences
   - Linter config
3. Apply formatting:
   - Fix indentation
   - Adjust line breaks
   - Align elements
4. Preserve functionality
5. Show before/after
**Success**: Code properly formatted
**Failure**: Formatter conflicts
**Examples**:
- "format this function" → Apply standard style
- "fix indentation" → Correct spacing