---
id: checkpoint-session
name: Checkpoint Session
title: Checkpoint Session
role: operator
type: operator
domain: session
stability: stable
status: stable
triggers: []
dependencies:
  - session-resolver
tools:
  - Edit
  - Read
version: 2.0.0
---

#### Handler: checkpoint-session {#checkpoint-session}
**Role**: Operator (called by other handlers, not directly by user)
**Target Pattern**: Automatic based on time/progress
**Pre-conditions**: 
- Active session exists in sessions/
- Significant progress made or time threshold passed
**Process**:
1. **Silent session resolution**:
   - Use session-resolver's `get-current-session()` 
   - Get current session path quietly
   - No output to user unless error
2. **Determine checkpoint trigger**:
   - Time-based: Every 2 hours of active work
   - Progress-based: Major milestone completed
   - Safety: Before risky operations
   - Called by: Other handlers during execution
3. **Read current session state**:
   - Load session file from resolved path
   - Parse current progress log
   - Check last checkpoint time
4. **Create checkpoint entry**:
   ```markdown
   - **[HH:MM]** - 💾 Checkpoint: [reason]
     - State: [brief status]
     - Changes: [count] files modified
     - Memory: [key points to remember]
   ```
5. **Quick append to Progress Log**:
   - Minimal edit to session file
   - Preserve all existing content
   - Add checkpoint marker inline
   - No YAML frontmatter changes
6. **Optional backup creation**:
   - If major checkpoint, create backup:
     - Copy to: sessions/backups/[session-id]-[timestamp].md
     - Preserve in case of corruption
     - Limit to 3 backups per session
7. **Update metadata minimally**:
   - Update `last_checkpoint` in memory only
   - Don't recalculate checksums (expensive)
   - Keep operation lightweight
8. **Backwards compatibility**:
   - If sessions/ referenced, add checkpoint there too
   - Keep as simple timestamp marker
   - Note: "Checkpoint saved to sessions/[path]"
9. **Return control immediately**:
   - No user interaction
   - No confirmation needed
   - Continue with calling handler's flow
**Success**: Progress preserved without interruption
**Failure**: Silent skip, log error for debugging
**Examples**:
- Called by code-edit after major refactor → Auto-checkpoint
- Called by task-handler after subtask complete → Progress checkpoint
- Called by error-handler before recovery attempt → Safety checkpoint
**Integration Notes**:
- This is an operator, not triggered directly by users
- Other handlers call this during their execution
- Designed to be lightweight and non-intrusive
- Should complete in <1 second

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/session/checkpoint-session.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
