---
id: evidence-check
name: Evidence Check
title: Evidence Check
role: orchestrator
type: orchestrator
domain: analysis
stability: stable
status: stable
triggers:
  - "the system"
  - "it uses"
  - "the code"
  - "claims about implementation"
dependencies:
  - gather-evidence
tools: []
version: 1.0.0
---

#### Pattern: evidence-check {#evidence-check}
**Triggers**: "the system", "it uses", "the code", claims about implementation
**Pre-conditions**: Making assertion about codebase
**Process**:
1. Flag: NEED_EVIDENCE = true
2. Load CONVENTIONS.md#gather-evidence
3. Search for proof before claiming
4. Include file:line reference
**Success**: Evidence found and cited
**Failure**: "I need to verify this"
**Examples**:
- "The system uses JWT" → Must find JWT usage
- "It implements caching" → Must locate cache code

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/evidence-check.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
