---
id: end-session
name: End Session
title: End Session
role: trigger
type: trigger
domain: session
stability: stable
status: stable
triggers:
  - "let's wrap up"
  - "end for today"
  - "finish session"
dependencies:
  - session-resolver
tools:
  - Edit
  - Read
  - TodoWrite
version: 2.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Handler: end-session {#end-session}
**Triggers**: "let's wrap up", "end for today", "finish session"
**Target Pattern**: Optional handoff notes
**Pre-conditions**: 
- Active session exists in sessions/
- Changes need preservation
**Process**:
1. **Load current session via session-resolver**:
   - Call `get-current-session()` to get active session
   - If no current session, check sessions/current for compatibility
   - Get session_id, path, and content
2. **Perform final updates**:
   - Run TodoWrite status check if todos exist
   - Gather final progress summary
   - Note any incomplete work
3. **Add session closing section**:
   - Run `date "+%Y-%m-%d %H:%M %Z"` and log the command as an S:W:H:E entry immediately before the closing block. This satisfies the timestamp guard and provides an "ended" timestamp.
   ```markdown
   ### 🎆 Session End: [HH:MM ZONE]
   
   **Summary**:
   - Started: [start time]
   - Ended: [end time]
   - Duration: [calculated]
   
   **Completed**:
   - ✓ [completed item 1]
   - ✓ [completed item 2]
   
   **Remaining**:
   - [ ] [incomplete item 1]
   - [ ] [incomplete item 2]
   
   **Handoff Notes**:
   [Any special instructions for next session]
   
   **Next Session Should**:
   1. [Priority 1]
   2. [Priority 2]
   ```
4. **Update session file metadata**:
   - Add `ended_at` field to YAML frontmatter (must match the recorded `date` command)
   - Update line and character counts
   - Calculate final checksum
   - Mark session as completed
5. **Archive the session (optional)**:
   - If requested, move to sessions/archive/YYYY/MM/
   - Maintain original filename
   - Preserve all metadata
6. **Clear current session symlink (safe, no rm*)**:
   - Only clear the symlink for true between-session closeout after active work tracking is archived or absent.
   - If the task remains active across multiple days, keep `sessions/current` and `plans/current` as recovery anchors; the next daily session should run `python3 scripts/codex-task sessions continue --task <id> --slug <slug>` to repoint them.
   - Remove only the symlink (does not touch target):
     ```bash
     test -L sessions/current && unlink sessions/current || echo "no current symlink"
     ```
   - Or re-point atomically to the next session when starting a new one:
     ```bash
     ln -sfn "sessions/YYYY/MM/YYYY-MM-DD-NNN-title.md" sessions/current
     ```
   - System now in "between sessions" state when `sessions/current` is absent
7. **Update work tracking files**:
   - If docs/ai/work-tracking exists, update status
   - Create handoff notes if needed
   - Update any project-specific tracking
8. **Backwards compatibility**:
9. **Update sessions/state.json**:
   - Mark ended session as `archived` and remove from `current`
   - If no next session and no ACTIVE work-tracking folder remains, omit `current` key or set to null
   - If ACTIVE work tracking remains for a multi-day task, keep the current pointers until the next continuation session repoints them
   - Keep `updated_at` ISO timestamp
   - Append session end marker to sessions/
   - Note: "Session archived to: sessions/[path]"
   - sessions/ remains as historical record
9. **Suggest commit**:
   - Generate commit message:
     ```
     session: end [date] - [main achievement]
     
     - Completed: [summary]
     - Duration: [time]
     - Next: [priority]
     ```
10. **Clean up**:
    - Remove any temporary files
    - Clear any session-specific state
    - Prepare for clean next session
**Success**: Session properly closed, archived if requested, ready for handoff
**Failure**: Uncommitted changes need attention first
**Examples**:
- "let's wrap up" → Full end-session with archive
- "done for today" → Quick close, session remains in place
- "finish and archive" → Move to archive/ directory

## Progress Log

- **2026-05-08 13:52** — [S:20260508|W:task42-session-management-system|H:templates/handlers/triggers/session/end-session.md|E:docs/ai/work-tracking/active/20260508-task42-session-management-system-ACTIVE/designs/session-management-scope-reconciliation.md] Clarified that active multi-day tasks should keep recovery pointers until `sessions continue` creates the next daily session.
- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/session/end-session.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
