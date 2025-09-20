---
id: check-docs-needed
name: Check Documentation Needed
role: operator
domain: docs
stability: stable
triggers:
  - "does X need documentation"
  - "should I document Y"
  - "docs required?"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: check-docs-needed {#check-docs-needed}
**Triggers**: "does X need documentation", "should I document Y", "docs required?"
**Target Pattern**: Code element to assess
**Pre-conditions**: 
- Code element identified
- Documentation standards exist
**Process**:
1. Identify element type:
   - Public API
   - Complex logic
   - Configuration
   - User-facing feature
2. **PRIMARY**: Check requirements:
   - Public interfaces → Yes
   - Complex algorithms → Yes
   - Non-obvious behavior → Yes
   - Internal helpers → Maybe
3. Use Serena to check existing docs
4. Provide recommendation
**Success**: Clear yes/no with reasoning
**Failure**: Edge case, explain factors
**Examples**:
- "does this API need docs" → Check public interface
- "document this helper?" → Assess complexity