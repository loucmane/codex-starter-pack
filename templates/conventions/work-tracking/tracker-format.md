---
id: tracker-format
type: convention
category: work-tracking
title: TRACKER.md Format and Required Sections
applies_to: documentation
enforcement: required
dependencies:
  - work-folder-structure
  - handoff-format
version: 1.0.0
status: stable
---

# TRACKER.md Format Standards

## Convention
TRACKER.md files must follow a specific structure to effectively track progress, maintain state, and enable smooth handoffs.

## Required Structure

### File Template
```markdown
# [Project/Feature] Tracker

**Started**: [Date from date command]
**Status**: [ACTIVE|COMPLETE|BLOCKED|PAUSED]
**Last Updated**: [Date from date command]
**Owner**: [Current developer]

## Goals
- [ ] Primary goal with measurable outcome
- [ ] Secondary goal
- [x] Completed goal
- [ ] Stretch goal

## Progress Log
[Chronological entries - APPEND new entries]
- **2025-07-30 14:30**: Started implementation
- **2025-07-30 15:45**: Completed initial setup
- **2025-07-30 16:00**: 🧪 CHECKPOINT: Awaiting user test

## Current State
[Single paragraph - REPLACE when updating]
Currently working on authentication flow. OAuth setup complete for Google, 
GitHub provider pending. Database schema updated.

## Next Steps
[Numbered list - REPLACE when updating]
1. Complete GitHub OAuth integration
2. Add error handling for failed auth
3. Implement session management
4. Create user profile page

## Blockers
- [ ] Waiting for API keys from client
- [x] ~~Database migration issue~~ (resolved)
```

## Section Requirements

### Header Metadata
```markdown
**Started**: 2025-07-30           # From date +%Y-%m-%d
**Status**: ACTIVE                # Current status
**Last Updated**: 2025-07-30      # From date +%Y-%m-%d  
**Owner**: John Doe               # From git config user.name
```

### Goals Section
- Checkbox format required
- Ordered by priority
- Measurable outcomes
- Check off when complete

### Progress Log
```markdown
## Progress Log
# CRITICAL: APPEND entries, never delete
- **YYYY-MM-DD HH:MM**: Regular entry
- **YYYY-MM-DD HH:MM**: 🎭 Orchestration: Deploying specialist
- **YYYY-MM-DD HH:MM**: 🧪 CHECKPOINT: User testing
- **YYYY-MM-DD HH:MM**: ❌ ERROR: Issue encountered
- **YYYY-MM-DD HH:MM**: ✅ COMPLETE: Task finished
- **YYYY-MM-DD HH:MM**: 🔄 RETRY: Attempting again
- **YYYY-MM-DD HH:MM**: 👤 User feedback: "Quote from user"
```

### Current State
- **REPLACE** entire content when updating
- Single paragraph or bullet points
- Present tense
- Factual status only

### Next Steps  
- **REPLACE** entire list when updating
- Numbered priority order
- Actionable items only
- 3-5 items ideal

## Update Rules

### Critical Update Pattern
```yaml
When updating TRACKER.md:
  Progress Log: 
    - APPEND new timestamped entries
    - NEVER delete old entries
    - Add at END of section
    
  Current State:
    - REPLACE entire content
    - Don't append to existing
    - Single update per session
    
  Next Steps:
    - REPLACE entire list
    - Reorder by new priorities
    - Remove completed items
```

### Common Mistake
```markdown
# ❌ WRONG - Appending to Current State
## Current State
OAuth working.
Added GitHub provider.  # Wrong! Should replace, not append

# ✅ CORRECT - Replacing Current State  
## Current State
OAuth fully implemented with Google and GitHub providers. 
All tests passing.
```

## Status Values

### Status Definitions
- **ACTIVE**: Currently being worked on
- **COMPLETE**: All goals achieved
- **BLOCKED**: Cannot proceed due to external factor
- **PAUSED**: Temporarily stopped, will resume
- **ABANDONED**: Permanently stopped
- **IN_REVIEW**: Awaiting review/approval

### Status Progression
```
ACTIVE → BLOCKED → ACTIVE → IN_REVIEW → COMPLETE
       → PAUSED → ACTIVE
       → ABANDONED
```

## Timestamp Requirements

### Always Use Commands
```bash
# For dates
date +%Y-%m-%d

# For timestamps
date "+%Y-%m-%d %H:%M"

# For progress log times
date '+%H:%M'
```

### Never Type Manually
- ❌ "2025-07-30 14:30" (guessed)
- ✅ `date "+%Y-%m-%d %H:%M"` (actual)

## Special Markers

### Progress Log Emojis
```markdown
🎭 Orchestration - Deploying specialist
🧪 Checkpoint - User testing needed
✅ Complete - Task finished
❌ Error - Problem encountered
🔄 Retry - Attempting again
👤 User - Feedback from user
⚠️ Warning - Potential issue
🔍 Investigation - Researching
💡 Idea - New approach
📝 Note - Important observation
```

## Examples

### ✅ Good TRACKER.md
```markdown
# Template Migration Tracker

**Started**: 2025-07-30
**Status**: ACTIVE  
**Last Updated**: 2025-07-30
**Owner**: Alice Smith

## Goals
- [x] Scan all template files
- [x] Extract handler metadata
- [ ] Migrate handlers to new structure
- [ ] Update references
- [ ] Create migration report

## Progress Log
- **2025-07-30 09:00**: Started template scanning
- **2025-07-30 10:30**: Completed scanner implementation
- **2025-07-30 11:00**: ✅ COMPLETE: All templates scanned
- **2025-07-30 14:00**: Started handler migration
- **2025-07-30 15:30**: 🧪 CHECKPOINT: 50% migrated, testing needed
- **2025-07-30 16:00**: 👤 User feedback: "Looks good, continue"

## Current State
Template scanning complete. Handler migration 50% done. 
127 handlers migrated successfully, 130 remaining.

## Next Steps
1. Complete remaining handler migrations
2. Update template references
3. Run validation suite
4. Generate migration report

## Blockers
None
```

### ❌ Poor TRACKER.md
```markdown
# Tracker

Started: sometime last week
Status: working on it

## Tasks
- Do the thing
- Other stuff
- More work

## Notes
Working on stuff. Made progress.
Did more work.
Almost done.

## Next
Finish it
```

## Integration with Other Files

### Relationship Map
```
TRACKER.md (progress tracking)
    ↓
IMPLEMENTATION.md (source of tasks)
    ↓
CHANGELOG.md (completed items)
    ↓
HANDOFF.md (session transitions)
```

## Rationale

### Why These Conventions

1. **Clear Progress**: Chronological log shows evolution
2. **Current Status**: State section gives instant overview
3. **Prioritization**: Next steps maintain focus
4. **Handoff Ready**: Standardized format enables transitions
5. **No Information Loss**: Append-only log preserves history

### Benefits
- **Transparency**: Progress visible at a glance
- **Continuity**: Anyone can continue work
- **Accountability**: Clear ownership and status
- **Planning**: Next steps always defined
- **History**: Complete record of work