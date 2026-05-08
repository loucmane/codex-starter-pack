---
id: prepare-compaction
name: Prepare Compaction
title: Prepare Compaction
role: trigger
type: trigger
domain: session
stability: stable
status: stable
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
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


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

3. **Create continuation checkpoint**:
   ```bash
   python3 scripts/codex-task compaction checkpoint \
     --task <id> \
     --slug <task-slug> \
     --summary "<one-line current work state>" \
     --next-step "<exact next action after compaction>" \
     --last-completed "<completed item>" \
     --open-item "<remaining item>"
   ```

   The helper appends the active session and tracker entries, writes the manifest and resume message, creates the compaction Serena memory file, updates the handoff note, and records `.plan_state/compaction-history.jsonl`.

4. **Update TodoWrite if active**:
   - Mark current task as in_progress with note
   - Add checkpoint comment to current todo
   - Save exact subtask position

5. **Review generated continuation message**:
   ```markdown
   ## 🔄 Ready for Compaction
   
   **To continue in new chat, use the generated resume message**:
   ```
   Continue from compaction checkpoint [memory-name].
   Read sessions/current, plans/current, the tracker, and the generated resume message.
   Resume [specific task] at [exact point].
   ```
   
   **Current state preserved**:
   ✓ All work saved to disk
   ✓ Session and tracker updated with checkpoint
   ✓ Handoff position marked
   ✓ Manifest, resume message, memory file, and history entry created
   
   **I was working on**: [one-line summary]
   **Next step will be**: [specific next action]
   ```

6. **Do NOT**:
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/session/prepare-compaction.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
- **2026-05-08 15:03** — [S:20260508|W:task31-compaction-protocol|H:templates/handlers/triggers/session/prepare-compaction.md|E:docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/designs/compaction-protocol-scope-reconciliation.md] Made `codex-task compaction checkpoint` the canonical handler action so compaction state is captured by a repeatable helper.
