---
id: record-decision
name: Record Decision
role: trigger
domain: docs
stability: stable
triggers:
  - "decided to X"
  - "choosing Y approach"
  - "going with Z"
dependencies: []
tools:
  - Edit
version: 1.0.0
---

#### Handler: record-decision {#record-decision}
**Triggers**: "decided to X", "choosing Y approach", "going with Z"
**Target Pattern**: Decision and rationale  
**Pre-conditions**: 
- Decision point reached
- Rationale available
**Process**:
1. Open decisions.md
2. Document decision
3. Add rationale
4. List alternatives considered
5. Note implications
**Success**: Decision preserved
**Failure**: Rationale unclear
**Examples**:
- "decided to use React" → Tech choice
- "going with microservices" → Architecture decision