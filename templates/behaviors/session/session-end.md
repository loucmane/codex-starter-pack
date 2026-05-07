---
trigger: Session end signals like "let's end", "thanks", "wrap up", "done for today"
title: Session End Behavior
action: Complete session end status and provide handoff messages
blocks: Cannot end session without proper status
category: session
type: behavior
enforcement: mandatory
status: stable
version: 1.0.0
---

# Session End Behavior

## Trigger Conditions
This behavior fires when detecting:
- "let's end here" or "end session"
- "thanks" or "thank you" (session conclusion)
- "wrap up" or "let's wrap up"
- "done for today" or "finish for now"
- "stop here" or "good stopping point"
- End of work signals
- Task completion with no follow-up

## Required Action
```
MUST complete session end status format:

1. Add final progress log entry with 🏁 marker
2. Create Session End Status section
3. Generate session metrics
4. Document next session priorities
5. Provide handoff messages
```

## Required Output Format
```markdown
### 📝 Progress Log
- **[HH:MM]** - [Final work items]
- **[HH:MM]** - 🏁 Session ending - [main achievement summary]

### 🚦 Session End Status
**SESSION COMPLETED** - [Main Achievement Title]:
- ✅ [Major accomplishment 1]
- ✅ [Major accomplishment 2]
- ✅ [Major accomplishment 3]
- 🎯 [Ready state for next session]

### 📊 Session Metrics
- Duration: [calculated hours]
- Tasks completed: [X/Y]
- Files modified: [count]
- [Other relevant metrics]

### 📋 Next Session Should:
1. [Priority 1 - specific action]
2. [Priority 2 - specific action]
3. [Priority 3 - specific action]

### 🔄 Handoff Messages

**Initialization** (for next session):
```
mcp__serena__activate_project project="starter-pack-monorepo"
read memory session_YYYY-MM-DD_description and sessions/current.
[Specific continuation instruction].
```

**Git/GitHub Disposition**:
```
direct-git-execution:
git add -A
git commit -m "type(scope): main achievement summary" -m "Summary:
- Detailed change 1
- Detailed change 2
- Detailed change 3

Work tracking: active-folder-name"
git push -u origin <branch>

full-gac-command only when the user explicitly asks for "the gac".
message-payload-only only when the user asks for a message.
auth-refresh-required when SSH/GPG cache is expired.
```
```

## Blocking Gate
**CANNOT END** session without:
- ✓ Session End Status section
- ✓ Session Metrics calculated
- ✓ Next Session priorities listed
- ✓ Both handoff messages provided
- ✓ Session memory created

## What This INCLUDES
- ✓ Full session closure with status
- ✓ Work metrics and achievements
- ✓ Clear next steps
- ✓ Handoff preparation
- ✓ Git/GitHub disposition using the correct response mode

## Difference from Compaction
| Session End | Compaction |
|-------------|------------|
| 🏁 Session ending marker | ⚠️ Compaction checkpoint |
| 🚦 Session End Status | 🔄 Ready for Compaction |
| Creates full handoff | Creates checkpoint only |
| Work stops completely | Work continues in new context |
| Uses direct Git/GitHub execution unless explicit fallback is requested | Generates resume command |

## Additional Requirements

### 1. Update Work Tracking Files
If active work folder exists:
- Update HANDOFF.md with final state
- Check all todos in TRACKER.md
- Note completion percentages

### 2. Create Session Memory
```bash
Write .serena/memories/session_YYYY-MM-DD_description.md
```
With content:
```markdown
# Session YYYY-MM-DD: [Achievement Title]

## Key Accomplishments
[List from Session End Status]

## Technical Details
- [Important decisions]
- [Problems solved]
- [Approaches taken]

## Next Priorities
[From Next Session Should section]

## Session Metrics
[Copy from metrics section]
```

### 3. Update sessions/state.json
```json
{
  "current": null,
  "paused": [],
  "updated_at": "[ISO timestamp]"
}
```
- Remove the ended session from any arrays and clear `current`
- If a new session will start immediately, set `current` accordingly

## Example Complete Output
```
### 📝 Progress Log
- **14:30** - Completed Phase 2 handler updates
- **15:00** - Discovered Phase 3 already done
- **15:30** - Created separate compaction handlers
- **15:45** - 🏁 Session ending - Session integration complete

### 🚦 Session End Status
**SESSION COMPLETED** - Template Migration Session Integration:
- ✅ Updated 5 session handlers to v2.0.0
- ✅ Integrated session-resolver module
- ✅ Discovered migration already complete
- ✅ Created separate compaction/end handlers
- 🎯 Ready for remaining optimization tasks

### 📊 Session Metrics
- Duration: ~3.5 hours
- Handlers updated: 5
- Phases completed: 2 (Phase 2 & 3)
- Files created: 3 new handlers/behaviors
- Validation: 100% pass rate

### 📋 Next Session Should:
1. Create 3 missing handlers (analyze-code, run-tests, test-implementation)
2. Consider consolidating 8+ overlapping handler pairs
3. Delete obsolete files after validation

### 🔄 Handoff Messages

**Initialization** (for next session):
```
mcp__serena__activate_project project="starter-pack-monorepo"
read memory session_2025-08-09_session-integration and sessions/current.
Continue with creating missing handlers and system optimization.
```

**Git/GitHub Disposition**:
```
direct-git-execution:
git add -A
git commit -m "feat: complete session integration and separate compaction" -m "Summary:
- Update 5 session handlers to use sessions/ directory
- Integrate session-resolver module across all handlers
- Create prepare-compaction handler for context limits
- Separate session-end from compaction-preparation behaviors

Work tracking: 20250730-template-migration-ACTIVE"
git push -u origin <branch>
```
```

## Important Notes
- The 🚦 Session End Status is the key identifier
- Always include the 🏁 marker in final progress log
- Metrics should be specific and measurable
- Next session priorities should be actionable
- Git/GitHub disposition must name the selected response mode

### Safe Symlink Handling (No rm*)
- To clear `sessions/current` without risking the target file:
  ```bash
  test -L sessions/current && unlink sessions/current || echo "no current symlink"
  ```
- To re-point atomically when starting a new session:
  ```bash
  ln -sfn "sessions/YYYY/MM/YYYY-MM-DD-NNN-title.md" sessions/current
  ```
These operations modify only the symlink, never the target.

## Cross-References
- [end-session handler](../../handlers/triggers/session/end-session.md)
- [session lifecycle](../../workflows/session/lifecycle.md)
- [compaction-preparation](./compaction-preparation.md)

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/session/session-end.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
