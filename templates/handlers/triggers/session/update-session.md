---
id: update-session
name: Update Session
role: trigger
domain: session
stability: stable
triggers:
  - "update session"
  - "record progress"
  - "checkpoint session"
  - "update sessions/"
dependencies:
  - session-resolver
tools:
  - Edit
  - Read
version: 2.0.0
---

#### Handler: update-session {#update-session}
**Triggers**: "update session", "record progress", "checkpoint session", "update sessions/"
**Target Pattern**: Optional specific updates
**Pre-conditions**: 
- Active session exists in sessions/
- Work has progressed
**Process**:
1. **Load current session via session-resolver**:
   - Call `get-current-session()` to get active session
   - Returns: session_id, path, metadata, content
   - If no current session, check sessions/current for compatibility
2. **Read current session file**:
   - Use returned path from resolver
   - Parse YAML frontmatter
   - Locate Progress Log section
3. **Gather update information**:
   - Current timestamp: `date "+%H:%M"`
   - Work completed since last update
   - Any blockers or issues
   - Next steps planned
4. **Update Progress Log section**:
   - Add new entry with timestamp:
   ```markdown
   - **[HH:MM]** - [summary of progress]
     - Completed: [specific items]
     - Blocked: [if any]
     - Next: [planned work]
   ```
5. **Update session metadata**:
   - Recalculate line count if needed
   - Update character count
   - Recalculate checksum (optional)
   - Update YAML frontmatter
6. **Write updates to session file**:
   - Preserve YAML frontmatter structure
   - Append to Progress Log
   - Maintain markdown formatting
   - Save to sessions/YYYY/MM/[filename]
7. **Update goal checkboxes if applicable**:
   - Mark completed goals with [x]
   - Add new goals if scope expanded
8. **Backwards compatibility**:
   - If sessions/ referenced, also update it
   - Add note: "See active session: sessions/[path]"
   - Keep sessions/ as read-only mirror
9. **Optional commit**:
   - If requested, suggest commit message
   - Include session file in commit
**Success**: Current session updated with progress
**Failure**: No active session found, guide to start one
**Examples**:
- "update session" → Add progress to current session file
- "record that we fixed the bug" → Specific progress entry
- "checkpoint our work" → Detailed state capture with goals update