---
id: file-operation
name: File Operation
role: orchestrator
domain: file
stability: stable
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