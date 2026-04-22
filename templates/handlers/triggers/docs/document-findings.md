---
id: document-findings
name: Document Findings
title: Document Findings
role: trigger
type: trigger
domain: docs
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/docs/document-findings.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
