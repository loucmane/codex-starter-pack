---
id: session-continuation-patterns
type: pattern
category: session
title: Session Continuation Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - patterns/session/session-patterns.md
  - patterns/session/state-patterns.md
related:
  - patterns/work-tracking/work-patterns.md
version: 1.0.0
status: stable
---

# Session Continuation Patterns

## Pattern Description
Patterns for continuing work across sessions, resuming interrupted tasks, and maintaining continuity in development workflows. These patterns ensure smooth transitions and minimal context loss.

## Pattern Structure
1. Identify continuation point
2. Restore previous context
3. Verify state consistency
4. Resume operations
5. Bridge any gaps
6. Continue forward progress

## When to Use
- Resuming after breaks
- Continuing next day's work
- Recovering from interruptions
- Switching between tasks
- Returning to paused work

## When NOT to Use
- Starting fresh work
- One-time operations
- Completed tasks
- Abandoned work

## Continuation Types

### Direct Continuation
Immediate resume from exact point:
```markdown
## Direct Resume
Last position: auth.js:145
Last operation: Added token validation
Resume from: Line 146, error handling
No gaps, continue directly
```

### Bridged Continuation
Resume with context rebuild:
```markdown
## Bridged Resume
Time gap: 18 hours
Need to:
1. Review last changes
2. Check test results
3. Verify dependencies
4. Continue from tests
```

### Reconstructed Continuation
Rebuild from available info:
```markdown
## Reconstructed Resume
Session data lost
Reconstructing from:
- Git diff shows changes
- Work folder has notes
- Tests indicate progress
Resume point identified
```

## Continuation Context Patterns

### Minimal Context
Just enough to continue:
```markdown
## Quick Context
- File: user.controller.js
- Task: Add validation
- Line: 234
- Next: Error handling
```

### Full Context
Complete state restoration:
```markdown
## Full Context Restoration
### Previous Session
- Date: 2025-01-14
- Duration: 4 hours
- Completed: Login, logout

### Current State
- Branch: feature/auth
- Modified: 5 files
- Tests: 8/10 passing
- Blockers: None

### Decision History
- JWT for tokens: Decided
- 15min expiry: Confirmed
- Redis storage: Implemented

### Resume Point
- File: refresh.js
- Function: handleRefresh
- Line: 45
- Task: Add error handling
```

### Progressive Context
Build context as needed:
```markdown
## Progressive Context Loading
1. Basic: What file and task
2. If needed: Recent changes
3. If complex: Full history
4. If blocked: Debug info
```

## Continuation Strategies

### Hot Continuation
Resume immediately:
```markdown
## Hot Resume
- Memory still fresh
- Context retained
- No review needed
- Continue directly
Time gap: < 1 hour
```

### Warm Continuation
Brief review then resume:
```markdown
## Warm Resume
- Quick context scan
- Review last changes
- Check current state
- Resume work
Time gap: 1-24 hours
```

### Cold Continuation
Full context rebuild:
```markdown
## Cold Resume
- Read all notes
- Review code changes
- Understand decisions
- Test current state
- Then resume
Time gap: > 24 hours
```

## Continuation Checkpoints

### Save Points
Regular continuation markers:
```markdown
## Checkpoint Alpha
Time: 14:30
Status: Login complete
Next: Start refresh
State: All tests pass
Notes: Consider rate limiting
```

### Breakpoints
Natural pause points:
```markdown
## Natural Breakpoint
- Feature complete ✓
- Tests passing ✓
- Documented ✓
- Ready to merge ✓
Good stopping point
```

### Handoff Points
Prepared for transition:
```markdown
## Handoff Ready
Completed:
- Core functionality
- Basic tests
- Error handling

Ready for next person:
- Docs need update
- Performance testing
- Security review
```

## Gap Bridging Patterns

### Time Gap Bridge
Handle time discontinuity:
```markdown
## Bridging 3-Day Gap
1. Check what changed:
   - Dependencies updated
   - Team made changes
   - Requirements evolved
2. Sync latest code
3. Review new context
4. Adjust plan
5. Continue work
```

### Knowledge Gap Bridge
Fill missing information:
```markdown
## Knowledge Recovery
Missing: How refresh works
Actions:
1. Read implementation
2. Check documentation
3. Review tests
4. Understand flow
5. Continue development
```

### State Gap Bridge
Restore missing state:
```markdown
## State Recovery
Lost: Current task context
Recovery:
1. Check TodoWrite
2. Read tracker.md
3. Review git status
4. Examine recent edits
5. Rebuild context
```

## Continuation Validation

### Consistency Check
Ensure valid continuation:
```markdown
## Continuation Validation
- Branch correct? ✓
- Tests still pass? ✓
- Dependencies OK? ✓
- No conflicts? ✓
Safe to continue
```

### Smoke Test
Quick functionality check:
```markdown
## Smoke Test Before Continue
1. Run basic tests
2. Check core functions
3. Verify connections
4. Test happy path
All systems go
```

### Full Validation
Comprehensive checks:
```markdown
## Full Validation
- Unit tests: 45/45 ✓
- Integration: 12/12 ✓
- Lint: No errors ✓
- Build: Success ✓
- Deploy: Ready ✓
```

## Continuation Patterns

### Task Chain Continuation
Resume task sequence:
```markdown
## Task Chain Resume
Completed: [A, B, C]
Current: D (50% done)
Remaining: [D, E, F, G]
Resume: Complete D, start E
```

### Parallel Work Continuation
Resume multiple streams:
```markdown
## Parallel Resume
Stream 1: Frontend (continue component)
Stream 2: Backend (continue API)
Stream 3: Tests (continue integration)
Sync points: Every 2 hours
```

### Iterative Continuation
Resume iteration cycle:
```markdown
## Iteration Resume
Last iteration: 3 (complete)
Current iteration: 4
- Done: Planning
- Current: Implementation
- Next: Testing
Resume: Continue implementation
```

## Failure Recovery Patterns

### Crash Recovery
Resume after unexpected stop:
```markdown
## Crash Recovery
Unexpected termination at 14:45
Last save: 14:40
Lost work: ~5 minutes
Recovery:
1. Check auto-saves
2. Review terminal history
3. Reconstruct last 5 min
4. Continue from 14:40 state
```

### Corruption Recovery
Handle corrupted state:
```markdown
## Corruption Recovery
State file corrupted
Fallback:
1. Try backup state
2. Use git history
3. Check work notes
4. Rebuild minimum state
5. Continue with caution
```

### Conflict Resolution
Handle conflicting changes:
```markdown
## Conflict Resolution
Changes while away:
- Team modified auth.js
- Conflicts in 3 files
Resolution:
1. Pull latest changes
2. Resolve conflicts
3. Re-test everything
4. Continue development
```

## Anti-Patterns to Avoid

1. **Cold start**: Not checking previous context
2. **Assumption continue**: Assuming nothing changed
3. **State ignore**: Not validating state before continuing
4. **Gap denial**: Ignoring time/knowledge gaps
5. **Forced continuation**: Continuing without proper context

## Examples

### Good Continuation
```markdown
## Resuming Work: 2025-01-15 09:00

### Previous Session Summary
Yesterday completed:
- User authentication
- Token generation
- Basic tests

### Current State Check
- Branch: feature/auth ✓
- Tests: 8/8 passing ✓
- No conflicts ✓

### Resuming From
File: auth/refresh.js:45
Task: Implement refresh logic
Context restored, continuing...
```

### Poor Continuation
```markdown
Just continuing from yesterday.
Not sure exactly where.
Will figure it out.
```

## Related Patterns
- [Session Patterns](session-patterns.md) - Session management
- [State Patterns](state-patterns.md) - State tracking
- [Work Patterns](../work-tracking/work-patterns.md) - Work continuation

## Handler References
Continuation logic is embedded in work management handlers