---
id: validate-comments
name: Validate Comments
role: operator
domain: docs
stability: stable
triggers:
  - "are these comments good"
  - "check comment quality"
  - "review documentation"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: validate-comments {#validate-comments}
**Triggers**: "are these comments good", "check comment quality", "review documentation"
**Target Pattern**: Comments to validate
**Pre-conditions**: 
- Comments present
- Quality standards defined
**Process**:
1. Read comments in context
2. **PRIMARY**: Validate against principles:
   - Explain WHY not WHAT
   - Add value beyond code
   - Stay up-to-date
   - Be concise
3. Check for anti-patterns:
   - Obvious comments
   - Outdated information
   - TODO without dates
4. Assess overall quality
5. Suggest improvements
**Success**: Comments assessed with feedback
**Failure**: No clear standards
**Examples**:
- "review these comments" → Quality assessment
- "are comments appropriate" → Check value-add