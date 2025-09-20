---
id: state-tracking-patterns
type: pattern
category: session
title: State Tracking Patterns
pattern_type: operational
complexity: moderate
dependencies:
  - patterns/session/session-patterns.md
related:
  - patterns/session/continuation-patterns.md
  - patterns/work-tracking/work-patterns.md
version: 1.0.0
status: stable
---

# State Tracking Patterns

## Pattern Description
Approaches for tracking and managing state across sessions, operations, and system interactions. These patterns ensure state is preserved, accessible, and consistent.

## Pattern Structure
1. Identify state components
2. Choose storage mechanism
3. Capture state changes
4. Persist state data
5. Restore state when needed
6. Validate state consistency

## When to Use
- Managing complex workflows
- Tracking multi-step operations
- Preserving context between sessions
- Coordinating parallel work
- Debugging state issues

## When NOT to Use
- Stateless operations
- Single atomic actions
- Read-only operations
- Temporary explorations

## State Types

### Application State
System-level state:
```markdown
## Application State
- Environment: development
- Version: 2.1.0
- Config: config/dev.json
- Database: connected
- Services: all running
```

### Session State
Current session context:
```markdown
## Session State
- Session ID: 20250115
- User: developer
- Work context: auth-feature
- Active tools: [Edit, Grep, Task]
- Current task: implement-refresh
```

### Work State
Task and progress state:
```markdown
## Work State
- Current iteration: 3
- Tasks completed: 5/8
- Active blockers: 0
- Test status: 7/10 passing
- Documentation: 40% complete
```

### Tool State
Tool-specific contexts:
```markdown
## Tool State
- TodoWrite: 3 active tasks
- Git: feature/auth branch
- Editor: auth/jwt.js:145
- Terminal: /src/auth
- Database: test_db
```

## State Storage Patterns

### File-Based State
Persistent state in files:
```markdown
# state.json
{
  "session": "20250115",
  "work": "auth-implementation",
  "progress": {
    "completed": ["login", "logout"],
    "current": "refresh",
    "pending": ["2fa", "reset"]
  }
}
```

### Memory State
Runtime state tracking:
```javascript
const state = {
  currentFile: 'auth.js',
  currentFunction: 'authenticate',
  lastOperation: 'edit',
  undoStack: [...],
  redoStack: [...]
};
```

### Distributed State
State across components:
```markdown
## Distributed State
- Frontend: user logged in
- Backend: session active
- Cache: user data cached
- Database: session recorded
- Queue: 0 pending tasks
```

## State Tracking Patterns

### Checkpoint Pattern
Regular state snapshots:
```markdown
## Checkpoint: 2025-01-15 14:00
- Location: auth/refresh.js:45
- Operation: Adding error handler
- Variables: {token: valid, user: authenticated}
- Stack depth: 3
- Memory usage: 45MB
```

### Event-Driven State
State changes as events:
```markdown
## State Events
[10:00] STATE_CHANGE: session.start
[10:15] STATE_CHANGE: task.begin(login)
[10:45] STATE_CHANGE: task.complete(login)
[11:00] STATE_CHANGE: task.begin(refresh)
[11:30] STATE_CHANGE: error.encountered
```

### Delta State Pattern
Track only changes:
```markdown
## State Delta
Previous: {tasks: 5, tests: 7}
Changes: 
  + tasks.completed: logout
  + tests.passed: 2
  - blockers: api-key-issue
Current: {tasks: 6, tests: 9}
```

## State Consistency Patterns

### State Validation
Ensure state is valid:
```javascript
function validateState(state) {
  return {
    valid: state.session && state.work,
    complete: state.progress !== undefined,
    consistent: state.tasks.length === state.total,
    current: state.timestamp > Date.now() - 3600000
  };
}
```

### State Recovery
Restore from corruption:
```markdown
## State Recovery Procedure
1. Check primary state file
2. If corrupted, try backup
3. If no backup, reconstruct from:
   - Git history
   - Work folders
   - Session logs
4. Validate recovered state
5. Create new checkpoint
```

### State Synchronization
Keep state consistent:
```markdown
## Sync Points
- Every operation completion
- Every 5 minutes (auto-save)
- Before context switch
- On error occurrence
- At session end
```

## State Transition Patterns

### Linear State Transitions
Sequential state changes:
```
INIT → LOADING → READY → WORKING → SAVING → COMPLETE
```

### Branching State Transitions
Multiple possible paths:
```
        ┌→ SUCCESS → COMPLETE
WORKING ├→ ERROR → RETRY → WORKING
        └→ BLOCKED → WAITING → WORKING
```

### Cyclic State Transitions
Repeating state cycles:
```
IDLE ←→ PROCESSING ←→ VALIDATING
  ↑                      ↓
  └──────COMPLETE────────┘
```

## State Query Patterns

### Current State Query
Get present state:
```markdown
## Query: Current State
- What task am I on? → "refresh-token"
- What's completed? → ["login", "logout"]
- Any blockers? → None
- Last action? → "Added validation"
```

### Historical State Query
Access past states:
```markdown
## Query: State at 14:00
- Task: "login-endpoint"
- Status: "testing"
- Tests: 3/5 passing
- Next: "Fix validation error"
```

### Projected State Query
Estimate future state:
```markdown
## Query: Projected State
Current velocity: 2 tasks/hour
Remaining tasks: 4
Projected completion: 16:00
Confidence: 75%
```

## State Persistence Patterns

### Incremental Persistence
Save changes as they occur:
```markdown
[10:00] SAVE: session.start
[10:05] SAVE: task.update
[10:10] SAVE: progress.increment
[10:15] SAVE: checkpoint.create
```

### Batch Persistence
Save at intervals:
```markdown
## Batch Save: 15:00
Changes since 14:00:
- Tasks: +2 completed
- Tests: +4 passed
- Docs: +150 lines
Saving... Done.
```

### Lazy Persistence
Save only when needed:
```markdown
## Lazy Save Triggers
- Context switch
- Session end
- Error occurrence
- Explicit save request
- Memory pressure
```

## Common State Patterns

### Undo/Redo State
Track reversible operations:
```javascript
{
  current: "state-v3",
  undoStack: ["state-v2", "state-v1"],
  redoStack: ["state-v4"],
  maxStackSize: 50
}
```

### Breadcrumb State
Navigation tracking:
```markdown
## Navigation Breadcrumbs
Home → Projects → Auth → Implementation → JWT → Refresh
Current: refresh.js:45
Can go back: 5 levels
```

### Flag State
Boolean state tracking:
```markdown
## Feature Flags
- debugMode: true
- verboseLogging: false
- experimentalFeatures: true
- autoSave: true
- darkMode: false
```

## State Anti-Patterns

1. **Global state pollution**: Keep state scoped
2. **State mutation**: Use immutable updates
3. **Stale state**: Regularly refresh state
4. **State bloat**: Only track necessary state
5. **Lost state**: Always persist critical state

## Examples

### Good State Management
```markdown
## State Checkpoint
Time: 2025-01-15 14:30:00
Session: 20250115-auth
Location: auth/jwt.js:145
Operation: Adding refresh logic
Stack: [main, auth, jwt, refresh]
Memory: {token: "...", expiry: 900}
Next: Error handling
Saved: ✓
```

### Poor State Management
```markdown
Currently working on something.
Some progress made.
State unclear.
```

## Related Patterns
- [Session Patterns](session-patterns.md) - Session management
- [Continuation Patterns](continuation-patterns.md) - State continuation
- [Work Patterns](../work-tracking/work-patterns.md) - Work state

## Handler References
State tracking is embedded throughout the handler system