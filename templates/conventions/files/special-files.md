---
id: special-files
type: convention
category: files
title: Special Files (sessions/, TRACKER.md, HANDOFF.md)
applies_to: documentation
enforcement: required
dependencies:
  - work-tracking/tracker-format
  - work-tracking/handoff-format
version: 1.0.0
status: stable
---

# Special Files Convention

## Convention
Special documentation files (sessions/, TRACKER.md, HANDOFF.md) must follow strict formats and update patterns to maintain continuity and traceability.

## sessions/ Standards

### Critical Entry Order Rule
```yaml
SESSION ENTRIES MUST BE:
  - At the TOP of the file (after Current Focus)
  - In reverse chronological order (newest first)
  - NEVER appended at the bottom
  
❌ WRONG: Adding new session at end of file
✅ RIGHT: Adding new session after Current Focus section
```

### Required Structure
```markdown
# AI Development Session Log (or # Session Documentation)

## Current Focus
[Brief description of what we're currently working on]

## Session: [TODAY'S DATE] <- NEW ENTRIES GO HERE
**AI Assistant**: Claude (model) ✓
**Developer**: [from git config]
**Task**: [from user's exact words]
...session content...

## Previous Session: [OLDER DATE]  
...older session content...
```

### Required Information Sources
```yaml
MUST BE REAL DATA:
  - Date/time: From 'date' command only
  - Git user: From 'git config user.name'
  - Branch: From 'git branch --show-current'
  - Task: From user's exact words

NEVER GUESS OR ASSUME:
  - Task IDs without verification
  - Timestamps from memory
  - Developer names
  - Work completed
```

### Progress Log Format
```markdown
### 📋 Progress Log
- **[HH:MM]** - Regular work entry (use `date '+%H:%M'`)
- **[HH:MM]** - 🎭 Orchestration: Deploying specialist
- **[HH:MM]** - 🧪 CHECKPOINT: Awaiting user test
- **[HH:MM]** - 👤 User feedback: "Issue description"
- **[HH:MM]** - ✅ Complete: Feature approved
```

## TRACKER.md Standards

### Required Structure
```markdown
# [Project/Feature] Tracker

**Started**: [Date from date command]
**Status**: [ACTIVE|COMPLETE|BLOCKED|PAUSED]
**Last Updated**: [Date from date command]

## Goals
- [ ] Primary goal with checkboxes
- [ ] Secondary goal
- [x] Completed goal

## Progress Log
[Chronological entries with timestamps]

## Current State
[Present status - REPLACE when updating]

## Next Steps
[Upcoming actions - REPLACE when updating]
```

### Update Rules
```yaml
CRITICAL: When updating TRACKER.md:
  - Progress Log: APPEND new timestamped entries
  - Current State: UPDATE/REPLACE with current status
  - Next Steps: UPDATE/REPLACE with new priorities
  - NEVER append to Current State section!
```

## HANDOFF.md Standards

### Required Structure
```markdown
# Handoff Document

**Last Session**: [Date and time]
**Last Worked By**: [Developer name]
**Current State**: [Brief status]

## What Was Done
- Bullet points of completed work
- Include file references

## Current Issues/Blockers
- Any problems encountered
- Unresolved questions

## Next Steps
1. Numbered priority list
2. Clear actionable items
3. Any dependencies

## Important Context
- Key decisions made
- Rationale for approaches
- Things to be aware of

## How to Continue
Exact commands or steps to resume work
```

## Examples

### Good sessions/ Entry
```markdown
## Session: 2025-07-10 14:30 CEST
**AI Assistant**: Claude 3.5 Sonnet ✓
**Developer**: John Doe
**Task**: "Implement authentication system"
**Task Source**: User request
**Branch**: feat/004-auth-system

### Session Validation ✓
- [x] Date from `date` command: 2025-07-10 14:30 CEST
- [x] Task verified by: user request
- [x] Git status checked: Yes - feat/004-auth-system

### 🎯 Session Goals
- [ ] Set up OAuth providers
- [ ] Create login component
- [ ] Add session management
```

### Good TRACKER.md Update
```markdown
## Progress Log
- **2025-07-10 14:30** - Started OAuth implementation
- **2025-07-10 15:15** - Google OAuth configured
- **2025-07-10 16:00** - 🧪 CHECKPOINT: Testing OAuth flow

## Current State
OAuth partially implemented. Google provider working, GitHub pending.

## Next Steps
1. Complete GitHub OAuth setup
2. Add error handling
3. Create user session storage
```

## Anti-patterns

### Wrong Patterns
```markdown
❌ Appending session at bottom
## Previous Session: 2025-07-09
...
## Session: 2025-07-10  # WRONG - should be at top

❌ Guessed timestamp
**2025-07-10 14:30** - Started work  # Did not run date command

❌ Appending to Current State
## Current State
OAuth working.
Added GitHub provider.  # WRONG - should replace, not append

❌ Missing Current Focus
# Session Documentation
## Session: 2025-07-10  # Missing Current Focus section
```

## Critical Timestamp Rule

### Always Use Commands
```bash
# For full timestamps
date "+%Y-%m-%d %H:%M %Z"

# For time only
date '+%H:%M'

# For date only
date +%Y%m%d
```

### Never Type Manually
- ❌ "2025-07-10 14:30" (typed from memory)
- ✅ `date "+%Y-%m-%d %H:%M %Z"` (command output)

## Rationale

### Why These Conventions

1. **Entry Order**: Newest first aids quick status checks
2. **Real Data**: Prevents errors and ensures accuracy
3. **Structure**: Consistent format enables tooling
4. **Timestamps**: Accurate timing crucial for debugging
5. **Update Patterns**: Clear rules prevent confusion

### Benefits
- **Continuity**: Any developer can pick up work
- **Traceability**: Clear audit trail of changes
- **Accuracy**: Real data prevents errors
- **Efficiency**: Standard structure speeds updates
- **Tooling**: Consistent format enables automation