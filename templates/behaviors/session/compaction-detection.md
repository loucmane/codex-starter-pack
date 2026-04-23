---
trigger: DEPRECATED - See session-end.md and compaction-preparation.md
title: Session Compaction Detection [DEPRECATED]
action: DEPRECATED - Separated into two distinct behaviors
blocks: DEPRECATED - Use new separated behaviors
category: session
type: behavior
enforcement: deprecated
status: stable
version: 2.0.0
---

# Session Compaction Detection [DEPRECATED]

> ⚠️ **DEPRECATED**: This behavior has been split into two separate behaviors:
> - **[compaction-preparation.md](./compaction-preparation.md)** - For context limit handling
> - **[session-end.md](./session-end.md)** - For actual session ending
> 
> This file is preserved for reference only. Use the new separated behaviors.

## Original Trigger Conditions
This behavior fires when detecting:
- "X% left" (memory warnings)
- "let's end here"
- "thanks" (session conclusion)
- "compaction" mentioned
- "stop here" or "wrap up"
- "good stopping point"
- End of work signals
- Memory limit approaching

## Required Action
```
MUST complete ALL items before session end:

1. Update sessions/:
   - Add final timestamp to progress log
   - Update session status
   - Note completion state

2. Update HANDOFF.md:
   - Current exact state
   - Next immediate steps
   - Open questions/blockers

3. Update TRACKER.md:
   - Check all completed todos
   - Update progress log
   - Note any incomplete items

4. Create session memory:
   - Filename: session_YYYY-MM-DD_description.md
   - Location: .serena/memories/
   - Content: Key accomplishments and context

5. Generate TWO required messages:
   - Initialization message for next session
   - Git commit message for work done
```

## Blocking Gate
**CANNOT END** session without providing:
- ✓ Initialization message
- ✓ Git commit message  
- ✓ All work files updated
- ✓ Session memory created
- ✓ Completion checklist shown

## Required Output Format
```markdown
## 📦 Session End / Compaction Ready

**Initialization Message**:
```
mcp__serena__activate_project project="starter-pack-monorepo", 
read memory session_YYYY-MM-DD_description and sessions/.
[One line about what to continue].
```

**Git Commit Message**:
```
gac "type: one-line summary

  Summary:
  - Major change or accomplishment
  - Another significant update
  - Key feature or fix

  Work tracking: active-folder-names"
```

CHECKLIST COMPLETED:
✓ sessions/ updated with final timestamp
✓ HANDOFF.md updated with current state
✓ TRACKER.md checkboxes updated
✓ Session memory created
✓ Both messages provided above
```

## Detailed Steps

### 1. Update sessions/
```markdown
## Progress Log
- **HH:MM** - Session start
- **HH:MM** - [Work done]
- **HH:MM** - Session end, ready for compaction

## Session Status
- Duration: X hours
- Completed: [List achievements]
- Next: [What to continue]
```

### 2. Update HANDOFF.md
```markdown
## Session End State (YYYY-MM-DD HH:MM)

### Work Completed
- [Specific accomplishments]

### Current State
- [Exactly where we stopped]
- [Any partial work status]

### Next Steps
1. [Immediate next action]
2. [Following priority]

### Open Questions
- [Unresolved issues]

### Files Modified
- [List of changed files]
```

### 3. Update TRACKER.md
```markdown
## Todos
- [x] Completed task (HH:MM)
- [►] In progress task (partial)
- [ ] Not started task

## Progress Log
- **HH:MM** - Session end summary
  - Completed: X tasks
  - In progress: Y tasks
  - Remaining: Z tasks
```

### 4. Create Session Memory
```markdown
# Session YYYY-MM-DD: [Description]

## Key Accomplishments
- [Major achievement 1]
- [Major achievement 2]

## Technical Details
- [Important implementation details]
- [Decisions made]
- [Problems solved]

## Context for Continuation
- [What was being worked on]
- [Current approach]
- [Next priorities]

## Important Notes
- [Any warnings or considerations]
- [Dependencies or blockers]
```

## Message Templates

### Initialization Message Components
```
Base: Activate project [full path]
Memory: read memory session_YYYY-MM-DD_description
Current: and sessions/
Context: [One line about what to continue]

Example:
mcp__serena__activate_project project="starter-pack-monorepo",
read memory session_2025-01-27_auth-implementation and sessions/.
Continue implementing JWT refresh token logic.
```

### Git Commit Message Components
```
Format: type: summary
Types: feat|fix|docs|refactor|test|chore
Body: Bullet points of changes
Footer: Work tracking reference

Example:
feat: implement user authentication system

- Add JWT token generation
- Create login/logout endpoints  
- Implement refresh token logic
- Add authentication middleware

Work tracking: 20250127-auth-system-ACTIVE
```

## Cross-References
- [CONVENTIONS.md#session-management](../../templates/conventions/)
- [work-tracking/update-tracker.md](../work-tracking/update-tracker.md)
- [timestamps/before-adding.md](../timestamps/before-adding.md)
- [git/before-commit.md](../git/before-commit.md)

## Error Cases
- **Sudden disconnection**: Partial checklist ok
- **No work folder**: Skip work-specific updates
- **Memory not created**: Note and continue
- **Files not updated**: List what wasn't updated

## Why This Gate Exists
- Ensures clean session handoff
- Preserves work context
- Enables smooth continuation
- Documents accomplishments
- Maintains work continuity
- Supports memory compaction

## Special Considerations

### Partial Sessions
If session was brief or exploratory:
- Still provide both messages
- Note "exploratory session" in memory
- Commit can be type "chore" or "docs"

### Multiple Work Streams
If worked on multiple things:
- List all in commit message
- Separate initialization focuses on next priority
- Memory captures all streams

### Emergency End
If ending due to error or issue:
- Note the problem in HANDOFF.md
- Include error context in memory
- Commit message includes "WIP" if incomplete

## Remember
**Every session needs proper closure - these messages enable seamless continuation!**
- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/session/compaction-detection.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
