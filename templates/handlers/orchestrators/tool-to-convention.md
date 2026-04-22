---
id: tool-to-convention
name: Tool to Convention Validator
title: Tool to Convention Validator
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
triggers:
  - "Tool usage must follow conventions"
dependencies: []
tools:
  - templates/conventions/ checks
version: 1.0.0
---

#### Handler: tool-to-convention {#tool-to-convention}
**Triggers**: Tool usage must follow conventions
**Target Pattern**: Convention check needed before tool use
**Pre-conditions**: 
- Tool selected for use
- Conventions apply to operation
**Process**:
1. Identify applicable conventions
2. Route to templates/conventions/ checks
3. Validate tool parameters
4. Execute with convention compliance
**Success**: Tool runs with proper conventions
**Failure**: Show convention violations, correct and retry
**Examples**:
- Git commit → Check commit message conventions
- File naming → Validate naming standards

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/tool-to-convention.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
