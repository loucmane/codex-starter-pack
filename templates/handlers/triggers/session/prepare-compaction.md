---
id: prepare-compaction
name: Prepare Compaction
role: trigger
domain: session
stability: stable
triggers:
  - "compaction"
  - "compact"
  - "% left"
  - "% until compaction"
  - "context getting long"
  - "need new chat"
  - "memory limit"
dependencies:
  - session-resolver
tools:
  - Edit
  - Read
  - TodoWrite
  - Write
version: 1.0.0
priority: high
---

#### Handler: prepare-compaction {#prepare-compaction}
**Triggers**: "compaction", "X% left", "context getting long", "need new chat"
**Target Pattern**: Optional specific checkpoint name
**Pre-conditions**: 
- Active work in progress
- Context approaching limits
- Need to preserve state for continuation
**Process**:
1. **Acknowledge compaction need**:
   ```
   Preparing for context compaction at X% capacity.
   I'll save our current state for seamless continuation.
   ```

2. **Complete current work unit**:
   - Finish the current line/function/paragraph
   - Don't leave anything half-implemented
   - Save all files with pending changes
   - Run any partial tests if applicable

3. **Update current session via session-resolver**:
   ```markdown
   ### ⚠️ Compaction Checkpoint: [HH:MM ZONE]
   
   **Context Status**: [X]% used, preparing for new chat
   **Current Work**: [specific task/subtask being worked on]
   **Stopping Point**: [exact location in work]
   
   **State Saved**:
   - Last action: [what was just completed]
   - Next action: [what to do when resuming]
   - Open files: [list any files being edited]
   - Active thoughts: [any incomplete reasoning]
   ```

4. **Update TodoWrite if active**:
   - Mark current task as in_progress with note
   - Add checkpoint comment to current todo
   - Save exact subtask position

5. **Create checkpoint memory**:
   ```bash
   # Create checkpoint file
   Write .serena/memories/checkpoint_YYYY-MM-DD_HH-MM_description.md
   ```
   With content:
   ```markdown
   # Compaction Checkpoint: [Description]
   
   ## Exact State
   - Working on: [specific task with ID]
   - File: [current file and line number]
   - Operation: [what was being done]
   
   ## Context to Restore
   - Approach: [current solution approach]
   - Decisions: [recent decisions made]
   - Blockers: [any current issues]
   
   ## Resume Instructions
   1. Load this checkpoint
   2. Read current session
   3. Continue from: [exact point]
   ```

6. **Generate continuation message**:
   ```markdown
   ## 🔄 Ready for Compaction
   
   **To continue in new chat, use**:
   ```
   Continue from checkpoint_YYYY-MM-DD_HH-MM_description. 
   Read sessions/current and resume [specific task] at [exact point].
   ```
   
   **Current state preserved**:
   ✓ All work saved to disk
   ✓ Session updated with checkpoint
   ✓ Todo position marked
   ✓ Memory checkpoint created
   
   **I was working on**: [one-line summary]
   **Next step will be**: [specific next action]
   ```

7. **Do NOT**:
   - End the session
   - Archive anything
   - Clear symlinks
   - Create handoff documents
   - Generate commit messages
   - Close any work

**Success**: State preserved, ready for new context, work continues seamlessly
**Failure**: Incomplete work that can't be checkpointed
**Examples**:
- "15% left" → Create checkpoint, prepare continuation
- "need compaction" → Save state, generate resume command
- "context getting long" → Checkpoint and guide for new chat

**Key Difference from end-session**:
- This prepares for continuation in a new context window
- Session remains active and work continues
- No closure, just preservation
- Focus on seamless resume, not handoff