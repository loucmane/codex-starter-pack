---
id: check-naming
name: Check Naming
role: operator
domain: development
stability: stable
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