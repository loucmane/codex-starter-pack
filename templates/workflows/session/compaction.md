---
id: session-compaction
type: workflow-component
category: session
title: Context Compaction Workflow
dependencies:
  - ./lifecycle.md
related:
  - ./continuation.md
  - ../memory/serena-patterns.md
version: 1.0.0
status: stable
---

# Context Compaction Workflow

## Purpose

Context compaction occurs when the conversation becomes too long. The AI needs to restore state and continue seamlessly.

## Signs Compaction is Needed

1. **From User**: "Context is getting long, let me create a new chat"
2. **From System**: Slow responses, errors about context length
3. **From AI**: Noticing degraded performance

## Critical Safeguards

### Before Compaction

1. **Complete Current Work Unit**
   - Finish the current subtask/file/operation
   - Don't leave anything half-done
   - Save all work to disk

2. **Update sessions/**
   ```markdown
   ### 📝 Progress Log
   - **[HH:MM]** - ⚠️ Context approaching limit, preparing for compaction
   - **[HH:MM]** - Completing current subtask before handoff
   - **[HH:MM]** - All work saved, ready for new context
   ```

3. **Create Checkpoint**
   - Run all tests to verify current state
   - Document exact stopping point
   - Note any in-progress thoughts/plans

## During Compaction

### User Actions
1. User creates new chat window
2. User provides activation: "Continue from [checkpoint]"
3. User may paste relevant context

### AI Recovery Process

1. **Immediate State Recovery**
   ```bash
   # First commands in new context
   pwd
   git status
   git branch --show-current
   date "+%Y-%m-%d %H:%M %Z"
   ```

2. **Read Critical Files**
   - sessions/ (ENTIRE file)
   - Current work tracker (if exists)
   - Most recent Serena memory
   - Current todo list state

3. **Reconstruct Context**
   ```
   Based on sessions/, I can see:
   - We're working on: [specific task]
   - Last completed: [specific achievement]
   - Currently on: [specific subtask]
   - Next steps: [specific actions]
   ```

4. **Verify Understanding**
   ```
   Before continuing, let me verify:
   - Current task: [task]
   - Last action: [action]
   - Should I continue with: [next step]?
   ```

## After Compaction

### Continuity Verification

1. **Check Nothing Lost**
   - All todos still tracked
   - File states match expectations
   - Tests still pass

2. **Resume Exactly**
   - Pick up at documented stopping point
   - Don't redo completed work
   - Continue with same approach/style

3. **Document Transition**
   ```markdown
   ### 📝 Progress Log
   - **[HH:MM]** - 🔄 Context restored after compaction
   - **[HH:MM]** - Verified all previous work intact
   - **[HH:MM]** - Continuing from subtask X.Y
   ```

## Best Practices

### For User
- Signal compaction need early (don't wait for errors)
- Let AI complete current work unit
- Provide clear continuation instruction

### For AI
- Always finish current operation
- Document stopping point explicitly
- Verify restoration before proceeding

## Example Compaction Flow

```
[Original Context]
User: "Context is getting long, let me compact"

AI: "I'll prepare for compaction:
    1. Completing current subtask (implementing auth)
    2. Running tests... ✅ passing
    3. Updating sessions/ with checkpoint
    4. Saving todo state
    
    Ready for new context. Start next chat with:
    'Continue task 7 from subtask 7.4, sessions/ shows status'"

[New Context]
User: "Continue task 7 from subtask 7.4, sessions/ shows status"

AI: [Reads sessions/]
    "I can see we're on Task 7: Core Layout Components
    Completed: 7.1, 7.2, 7.3
    Starting: 7.4 Footer Component
    
    Shall I proceed with the Footer implementation?"
```

## Common Compaction Mistakes

1. **❌ Starting fresh** - Always read sessions/ first
2. **❌ Redoing work** - Check what's already complete
3. **❌ Losing context** - Use Serena memories for continuity
4. **❌ Breaking flow** - Maintain same working style

## Recovery Checklist

- [ ] Read sessions/ completely
- [ ] Check git status and branch
- [ ] Review current todos
- [ ] Verify last completed work
- [ ] Identify exact continuation point
- [ ] Confirm understanding with user
- [ ] Resume from correct point