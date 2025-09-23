---
id: session-management-patterns
type: pattern
category: session
title: Session Management Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - templates/sessions/
  - patterns/work-tracking/work-patterns.md
related:
  - patterns/session/state-patterns.md
  - patterns/session/continuation-patterns.md
version: 1.0.0
status: stable
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Session Management Patterns

## Pattern Description
Patterns for managing development sessions, maintaining context across interactions, and ensuring smooth transitions between work sessions. These patterns help maintain continuity and context.

## Pattern Structure
1. Session initialization
2. Context establishment
3. State management
4. Progress tracking
5. Session handoff
6. Session closure

## When to Use
- Starting new development session
- Resuming previous work
- Switching between tasks
- Ending work session
- Transferring context

## When NOT to Use
- Quick one-off queries
- Stateless operations
- Context-free discussions
- Casual conversations

## Session Lifecycle

### Session Initialization
```markdown
## Session Start: YYYYMMDD

### Context
- Previous session: [date or "first"]
- Continuing: [work/task or "new"]
- Objectives: [session goals]

### Current Focus
[What we're working on]

### Key Information
[Important context to remember]
```

### Session Progression
```markdown
## Progress Updates

[Timestamp]
- Completed: [what was done]
- Current: [what's in progress]
- Next: [what's coming]
```

### Session Closure
```markdown
## Session End: [Timestamp]

### Completed
- [List of completions]

### In Progress
- [Unfinished items]

### Handoff Notes
- [Context for next session]
```

## Session State Management

### State Components
1. **Session ID**: Date-based identifier (YYYYMMDD)
2. **Work Context**: Current work folder/task
3. **Tool State**: Active tools and contexts
4. **Progress State**: What's been done
5. **Decision State**: Choices made

### State Persistence
```markdown
## Session State

### Identifiers
- Session: 20250115
- Work: auth-implementation
- Iteration: 3

### Context
- Task: Implementing JWT refresh
- Stage: Testing phase
- Blockers: None

### Decisions
- Using 15min access tokens
- Refresh tokens in HTTP-only cookies
```

## Context Management Patterns

### Context Capture Pattern
Capture essential context:
```markdown
## Current Context
- **Where**: Working in auth module
- **What**: Adding refresh token endpoint
- **Why**: Security requirement
- **How**: JWT with Redis storage
- **Status**: 70% complete
```

### Context Recovery Pattern
Restore context from previous:
1. Check sessions/ for last entry
2. Review TodoWrite state
3. Check work folder status
4. Read last tracker.md entry
5. Summarize current position

### Context Transfer Pattern
Hand off to next session:
```markdown
## Handoff Context
**Last Action**: Implemented refresh endpoint
**Current State**: Testing refresh flow
**Next Steps**: Add error handling
**Important**: Check token expiry edge case
**Files Modified**: auth.js, refresh.js
```

## Session Patterns

### Daily Session Pattern
For regular daily work:
```markdown
## Session: 20250115

### Morning Focus
- Review yesterday's progress
- Plan today's objectives
- Check blockers

### Work Sessions
- AM: Implementation work
- PM: Testing and documentation

### End of Day
- Log progress
- Update trackers
- Plan tomorrow
```

### Continuation Session Pattern
For multi-day work:
```markdown
## Continuing Session: Day 3

### Recap
- Days 1-2: Built auth system
- Today: Add refresh logic

### Current Position
- File: auth/refresh.js
- Line: 145
- Task: Error handling

### Resume Point
- Continue from refresh error handler
```

### Handoff Session Pattern
For team transitions:
```markdown
## Session Handoff

### Completed by Alice
- User model created
- Basic auth implemented
- Tests written

### For Bob to Continue
- Add refresh tokens
- Implement logout
- Update documentation

### Key Decisions
- JWT for tokens
- 15min expiry
- Redis for storage
```

## Lost Context Pattern

### Pattern Structure
**Triggers**: "I'm lost", "what was I doing", "where were we"
**Process**:
1. Check TodoWrite state
2. Review recent work folders
3. Run git status
4. Check sessions/
5. Provide context summary

### Recovery Steps
```markdown
## Context Recovery

You were working on:
- Task: User authentication
- File: auth/jwt.js
- Progress: 60% complete
- Last: Added token generation
- Next: Add refresh logic

Recent changes:
- Modified: auth/jwt.js
- Added: auth/refresh.js
- Tests: 5/8 passing
```

## Session Memory Patterns

### Short-term Memory
Within current session:
- Current task focus
- Recent operations
- Active decisions
- Temporary state

### Long-term Memory
Across sessions:
- Project goals
- Design decisions
- Completed work
- Learned patterns

### Working Memory
Active context:
```markdown
## Working Memory
- Current file: user.controller.js
- Current function: createUser
- Current issue: Validation error
- Fix approach: Add email check
```

## Session Coordination Patterns

### Single-User Sessions
One developer, multiple sessions:
```markdown
## Session Chain
Session 1: Planning → 
Session 2: Implementation →
Session 3: Testing →
Session 4: Documentation
```

### Multi-User Sessions
Multiple developers, shared work:
```markdown
## Parallel Sessions
Alice (Session A): Frontend work
Bob (Session B): Backend API
Carol (Session C): Testing

Sync points: Daily at 10am
```

### Async Handoffs
Time-shifted collaboration:
```markdown
## Async Handoff
Developer A (UTC+0): Morning work
→ Handoff notes
Developer B (UTC+8): Evening work
→ Handoff notes
Developer A: Next morning continues
```

## Session Anti-Patterns

### Anti-Pattern: No Context
Starting work without checking context:
- Missing previous progress
- Duplicating work
- Breaking continuity

### Anti-Pattern: Context Overload
Too much context information:
- Overwhelming details
- Irrelevant history
- Slow session starts

### Anti-Pattern: Lost Handoffs
Poor session transitions:
- No handoff notes
- Missing state
- Context gaps

## Session Quality Metrics

### Continuity Score
How well sessions connect:
- High: Seamless continuation
- Medium: Some context recovery needed
- Low: Significant gaps

### Context Completeness
Information availability:
- Complete: All context present
- Partial: Some missing pieces
- Minimal: Major gaps

### Handoff Quality
Transition effectiveness:
- Excellent: Next session starts immediately
- Good: Minor clarification needed
- Poor: Significant investigation required

## Examples

### Good Session Management
```markdown
## Session: 20250115

### Continuing From
Session 20250114: Completed user model

### Today's Focus
Implement authentication endpoints

### Progress
10:00 - Started login endpoint
11:30 - Added validation
14:00 - Completed tests
15:30 - Started refresh token

### Handoff
Tomorrow: Complete refresh token logic
Key file: auth/refresh.js:45
Note: Check Redis connection first
```

### Poor Session Management
```markdown
Working on auth stuff.
Made some progress.
Will continue tomorrow.
```

## Related Patterns
- [State Patterns](state-patterns.md) - State management
- [Continuation Patterns](continuation-patterns.md) - Work continuation
- [Work Patterns](../work-tracking/work-patterns.md) - Work organization

## Handler References
[Handler: lost-context migrated to handlers/orchestrators/context-recovery.md]
[Handler: system-improvement migrated to handlers/orchestrators/system-improver.md]