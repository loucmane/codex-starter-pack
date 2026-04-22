---
id: record-decision
name: Record Decision
title: Record Decision
role: trigger
type: trigger
domain: docs
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/docs/record-decision.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
