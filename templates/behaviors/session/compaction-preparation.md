---
trigger: Compaction signals like "X% left", "compaction", "context long"
action: Prepare checkpoint for context continuation
blocks: Cannot compact without saving current state
category: session
enforcement: mandatory
version: 1.0.0
---

# Compaction Preparation Behavior

## Trigger Conditions
This behavior fires when detecting:
- "X% left" or "X% until compaction"
- "compaction" or "compact" mentioned
- "context getting long"
- "need new chat"
- "memory limit" warnings
- System performance degradation

## Required Action
```
MUST complete checkpoint preparation:

1. Save current work state:
   - Complete current operation
   - Save all open files
   - Don't leave anything half-done

2. Create checkpoint marker in session:
   - Mark exact stopping point
   - Note current work context
   - Save active thoughts/plans

3. Update todos if active:
   - Mark current task position
   - Add checkpoint note
   - Save subtask progress

4. Create checkpoint memory:
   - Filename: checkpoint_YYYY-MM-DD_HH-MM_description.md
   - Location: .serena/memories/
   - Content: Exact state and resume instructions

5. Generate continuation message:
   - Exact command to resume
   - Current state summary
   - Next action to take
```

## Blocking Gate
**CANNOT COMPACT** without:
- ✓ Current work unit completed
- ✓ All files saved
- ✓ Checkpoint created
- ✓ Continuation message provided

## Required Output Format
```markdown
## 🔄 Ready for Compaction

**To continue in new chat, use**:
```
Continue from checkpoint_YYYY-MM-DD_HH-MM_description.
Read sessions/current and resume [specific task] at [exact point].
```

**Current state preserved**:
✓ All work saved to disk
✓ Session checkpoint created
✓ Todo position marked
✓ Memory checkpoint saved

**I was working on**: [one-line summary]
**Next step will be**: [specific next action]
```

## What This Does NOT Do
- ❌ Does NOT end the session
- ❌ Does NOT create handoff documents
- ❌ Does NOT generate commit messages
- ❌ Does NOT archive anything
- ❌ Does NOT clear work state

## Difference from Session End
| Compaction | Session End |
|------------|-------------|
| Preserves state for continuation | Closes and archives work |
| Creates checkpoint | Creates handoff |
| Generates resume command | Generates commit message |
| Work continues in new context | Work stops until next session |
| Session stays active | Session gets archived |

## Example Flow
```
User: "20% left, need to compact"

AI: "Preparing for compaction at 20% capacity...

## 🔄 Ready for Compaction

**To continue in new chat, use**:
```
Continue from checkpoint_2025-08-09_15-30_template-migration.
Read sessions/current and resume task 7.4 at Footer component implementation.
```

**Current state preserved**:
✓ All work saved to disk
✓ Session checkpoint created
✓ Todo position marked
✓ Memory checkpoint saved

**I was working on**: Implementing Footer component for blog
**Next step will be**: Add social media links to footer"
```

## Recovery in New Context
When user provides continuation command:
1. Load checkpoint memory
2. Read current session
3. Restore todo state
4. Continue from exact point
5. Maintain same working style

## Important Notes
- Compaction is about context limits, not work completion
- Focus on seamless continuation, not closure
- Preserve momentum and working context
- Make resume as frictionless as possible

## Cross-References
- [prepare-compaction handler](../../handlers/triggers/session/prepare-compaction.md)
- [compaction workflow](../../workflows/session/compaction.md)
- [session-resolver](../../engine/core/session-resolver.md)