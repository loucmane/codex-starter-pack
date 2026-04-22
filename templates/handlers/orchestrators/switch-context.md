---
id: switch-context
name: Switch Context State
title: Switch Context State
role: orchestrator
type: orchestrator
domain: session
stability: stable
status: stable
triggers:
  - "work on something else"
  - "switch to"
  - "pause this"
dependencies:
  - save-context
tools:
  - save-context
  - load target context
version: 1.0.0
---

#### Handler: switch-context {#switch-context}
**Triggers**: "work on something else", "switch to", "pause this"
**Target Pattern**: Change from one context to another
**Pre-conditions**: 
- Current context active
- Target context identified
**Process**:
1. Execute save-context for current
2. Clear active todos
3. Load target context
4. Confirm switch complete
**Success**: Clean context switch
**Failure**: Rollback to previous context
**Examples**:
- "switch to bug fix" → Save feature, load bug context
- "work on PR instead" → Full context swap

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/switch-context.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
