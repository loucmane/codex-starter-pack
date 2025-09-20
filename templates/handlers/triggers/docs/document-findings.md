---
id: document-findings
name: Document Findings
role: trigger
domain: docs
stability: stable
triggers:
  - "I discovered X"
  - "found that Y"
  - "learned Z"
dependencies: []
tools:
  - Edit
version: 1.0.0
---

#### Handler: document-findings {#document-findings}  
**Triggers**: "I discovered X", "found that Y", "learned Z"
**Target Pattern**: Discovery or insight
**Pre-conditions**: 
- Work context exists
- Finding is significant
**Process**:
1. Open FINDINGS.md
2. Categorize finding
3. Add with context
4. Link to evidence
5. Note implications
**Success**: Finding documented
**Failure**: Finding too vague
**Examples**:
- "discovered the bug source" → Root cause doc
- "found performance issue" → Technical finding