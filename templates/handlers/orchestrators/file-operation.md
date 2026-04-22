---
id: file-operation
name: File Operation
title: File Operation
role: orchestrator
type: orchestrator
domain: file
stability: stable
status: stable
triggers:
  - "edit"
  - "update"
  - "modify"
  - "add to"
  - "append"
  - "change"
dependencies: []
tools: []
version: 1.0.0
---

#### Pattern: file-operation {#file-operation}
**Triggers**: edit, update, modify, "add to", append, change
**Pre-conditions**: Target file identifiable
**Process**:
1. Extract filename from request
2. Check templates/conventions/#{filename}-editing-rules
3. If special file → Apply specific rules:
   - tracker.md → Append to Progress Log only
   - findings.md → Append to appropriate section
   - sessions/ → Append after Current Focus
4. Else → Standard edit flow
**Success**: Correct edit rules applied
**Failure**: Ask which file to edit
**Examples**:
- "Update tracker" → Append-only rules
- "Fix typo in code" → Standard edit
- "Add to findings" → Append to discoveries

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/file-operation.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
