---
trigger: Compaction signals like "X% left", "compaction", "context long"
title: Compaction Preparation Behavior
action: Prepare checkpoint for context continuation
blocks: Cannot compact without saving current state
category: session
type: behavior
enforcement: mandatory
status: stable
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

4. Create the continuation checkpoint with the helper:
   ```bash
   python3 scripts/codex-task compaction checkpoint \
     --task <id> \
     --slug <task-slug> \
     --summary "<one-line current state>" \
     --next-step "<exact next action after compaction>" \
     --last-completed "<completed item>" \
     --open-item "<remaining item>"
   ```

5. Review the generated continuation packet:
   - Manifest JSON and resume Markdown under the active work-tracking reports.
   - Compaction memory under `.serena/memories/`.
   - Session, tracker, handoff, and `.plan_state/compaction-history.jsonl` entries.
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

**To continue in new chat, use the generated resume message**:
```
Continue from compaction checkpoint [memory-name].
Read sessions/current, plans/current, the tracker, and the generated resume message.
Resume [specific task] at [exact point].
```

**Current state preserved**:
✓ All work saved to disk
✓ Session checkpoint entry created
✓ Tracker and handoff position marked
✓ Manifest, resume message, memory file, and history entry saved

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
✓ Session checkpoint entry created
✓ Tracker and handoff position marked
✓ Manifest, resume message, memory file, and history entry saved

**I was working on**: Implementing Footer component for blog
**Next step will be**: Add social media links to footer"
```

## Recovery in New Context
When user provides continuation command:
1. Read the generated resume message
2. Load checkpoint memory
3. Read current session, current plan, and tracker
4. Continue from exact point
5. Maintain same working style

## Important Notes
- Compaction is about context limits, not work completion
- Focus on seamless continuation, not closure
- Preserve momentum and working context
- Make resume as frictionless as possible
- The helper must leave `sessions/current`, `plans/current`, and the ACTIVE work-tracking folder intact

## Cross-References
- [prepare-compaction handler](../../handlers/triggers/session/prepare-compaction.md)
- [compaction workflow](../../workflows/session/compaction.md)
- [session-resolver](../../engine/core/session-resolver.md)

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/session/compaction-preparation.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
- **2026-05-08 15:03** — [S:20260508|W:task31-compaction-protocol|H:templates/behaviors/session/compaction-preparation.md|E:docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/designs/compaction-protocol-scope-reconciliation.md] Replaced manual compaction-memory instructions with the Task 31 `codex-task compaction checkpoint` helper workflow.
