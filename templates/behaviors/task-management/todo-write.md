---
trigger: Starting any multi-step task or development work
action: Create comprehensive task list with TodoWrite
blocks: Cannot start work without task breakdown
category: task-management
enforcement: mandatory
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Todo Write Enforcement

## Trigger Conditions
This behavior fires whenever:
- Starting new development work
- Beginning feature implementation
- Initiating bug fixes
- Starting any multi-step task
- Planning investigation or research
- Beginning refactoring work
- Starting test implementation

## Required Action
```
IMMEDIATELY upon work start:

1. Break down work into specific tasks:
   - Research/investigation tasks
   - Implementation tasks
   - Testing tasks
   - Documentation tasks
   - Validation tasks

2. Create todos with TodoWrite:
   - Each task must be actionable
   - Each task must be specific
   - No compound tasks (do X and Y)
   - Include all steps needed

3. Mark first task as in_progress

4. Update as work proceeds:
   - Mark completed when done
   - Add new tasks as discovered
   - Never skip the todo update
```

## Blocking Gate
**CANNOT PROCEED** with work until:
- Task list created
- Tasks are specific and actionable
- First task marked in_progress
- All phases represented (research, implement, test)

## Satisfaction Criteria
✓ TodoWrite invoked at work start
✓ Tasks broken down appropriately
✓ Each task independently completable
✓ Active task marked in_progress
✓ Completed tasks marked done immediately

## Task Breakdown Patterns

### Feature Implementation
```
TodoWrite:
- [ ] Research existing patterns
- [ ] Design component structure
- [ ] Implement core functionality
- [ ] Add error handling
- [ ] Write unit tests
- [ ] Update documentation
- [ ] Integration testing
- [ ] Code review prep
```

### Bug Fix
```
TodoWrite:
- [ ] Reproduce the issue
- [ ] Investigate root cause
- [ ] Document findings
- [ ] Implement fix
- [ ] Test fix locally
- [ ] Check for regressions
- [ ] Update tests if needed
- [ ] Document solution
```

### Refactoring
```
TodoWrite:
- [ ] Identify refactoring targets
- [ ] Ensure test coverage exists
- [ ] Run tests (baseline)
- [ ] Perform refactoring
- [ ] Run tests (verify)
- [ ] Update documentation
- [ ] Check performance impact
```

### Investigation/Research
```
TodoWrite:
- [ ] Define investigation scope
- [ ] Search existing code
- [ ] Document current behavior
- [ ] Identify patterns
- [ ] Research alternatives
- [ ] Document findings
- [ ] Make recommendations
```

## Task Management Rules

### Task Specificity
```
❌ Bad: "Implement feature"
✅ Good: "Create UserProfile component with props interface"

❌ Bad: "Fix bugs"
✅ Good: "Fix null reference error in login handler"

❌ Bad: "Write tests"
✅ Good: "Add unit test for password validation function"
```

### Task Granularity
- Each task should take 5-30 minutes
- Break larger tasks into subtasks
- One clear outcome per task
- Independently verifiable

### Task Updates
```
When starting task:
- [►] Mark as in_progress

When completed:
- [x] Mark as completed immediately

When blocked:
- [ ] Keep unchecked, add note

When no longer needed:
- [~] Mark as cancelled with reason
```

## Common Patterns

### Immediate Start Pattern
```
User: "Fix the navigation bug"
AI:
1. TodoWrite with investigation and fix tasks
2. Mark first task in_progress
3. Begin investigation
```

### Discovery Pattern
```
During work, discover new requirements:
1. Add new todos for discovered work
2. Continue current task
3. Address new todos in sequence
```

### Checkpoint Pattern
```
Every 30 minutes:
1. Update completed tasks
2. Add any new discovered tasks
3. Mark current task in_progress
```

## Managing Large Todo Lists

### When Exceeding 20 Tasks
```
Required actions:
1. Review all tasks for relevance
2. Complete or cancel stale tasks
3. Group related tasks
4. Consider splitting into phases
5. Clean up before adding more
```

### Organizing by Priority
```
TodoWrite with sections:
## Critical (Do First)
- [ ] Security fix
- [ ] Breaking bug fix

## Important (Do Next)
- [ ] Feature implementation
- [ ] Performance improvement

## Nice to Have (If Time)
- [ ] Refactoring
- [ ] Documentation updates
```

## Cross-References
- [WORKFLOWS.md#task-management](../../templates/workflows/)
- [work-tracking/update-tracker.md](../work-tracking/update-tracker.md)
- [validation/evidence-claims.md](../validation/evidence-claims.md) - Before marking complete

## Error Cases
- **Forgot to create todos**: Stop and create immediately
- **Task too vague**: Break down into specific subtasks
- **Too many tasks**: Review and consolidate
- **Task not completable**: Split or clarify

## Special Considerations

### For Quick Fixes
Even "quick" fixes need todos:
```
TodoWrite:
- [ ] Locate issue
- [ ] Apply fix
- [ ] Verify fix works
```

### For Exploration
Open-ended work still needs structure:
```
TodoWrite:
- [ ] Define exploration goals
- [ ] Time-box investigation (30 min)
- [ ] Document findings
- [ ] Determine next steps
```

### For Reviews
Code review tasks:
```
TodoWrite:
- [ ] Read through changes
- [ ] Check logic correctness
- [ ] Verify test coverage
- [ ] Check documentation
- [ ] Leave review comments
```

## Why This Gate Exists
- Provides clear work structure
- Enables progress tracking
- Prevents scope creep
- Captures all necessary steps
- Creates accountability
- Supports work handoffs

## Remember
**No work without todos - structure enables success!**