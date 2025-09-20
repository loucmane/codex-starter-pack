---
id: progress-measurement-patterns
type: pattern
category: work-tracking
title: Progress Measurement Patterns
pattern_type: operational
complexity: simple
dependencies:
  - patterns/work-tracking/work-patterns.md
related:
  - patterns/work-tracking/documentation-patterns.md
version: 1.0.0
status: stable
---

# Progress Measurement Patterns

## Pattern Description
Approaches and methods for measuring, tracking, and reporting progress on development work. These patterns ensure progress is visible, measurable, and actionable.

## Pattern Structure
1. Define progress metrics
2. Establish checkpoints
3. Track completion status
4. Measure velocity
5. Report progress
6. Identify blockers

## When to Use
- Tracking task completion
- Measuring development velocity
- Reporting work status
- Identifying bottlenecks
- Planning next steps

## When NOT to Use
- Exploratory work without clear goals
- Research without deliverables
- Creative brainstorming
- Undefined scope work

## Progress Metrics

### Completion Metrics
- **Tasks completed**: Number of finished tasks
- **Features delivered**: Functional features shipped
- **Tests passing**: Test success rate
- **Code coverage**: Percentage of code tested
- **Documentation complete**: Docs written

### Velocity Metrics
- **Lines per hour**: Code production rate
- **Tasks per session**: Task completion rate
- **Bugs fixed per day**: Issue resolution rate
- **Features per sprint**: Feature delivery rate

### Quality Metrics
- **Bug density**: Bugs per lines of code
- **Test coverage**: Percentage tested
- **Code review pass rate**: First-time approval rate
- **Performance benchmarks**: Speed/efficiency measures

## Progress Tracking Levels

### Task-Level Progress
Individual task tracking:
```markdown
## Task: Implement login endpoint
- [x] Create route handler
- [x] Add input validation
- [x] Implement authentication
- [ ] Add error handling
- [ ] Write tests
Progress: 60% complete
```

### Feature-Level Progress
Feature completion tracking:
```markdown
## Feature: User Authentication
- [x] Login endpoint (100%)
- [x] Logout endpoint (100%)
- [x] Register endpoint (100%)
- [ ] Password reset (0%)
- [ ] Two-factor auth (0%)
Overall: 60% complete
```

### Project-Level Progress
Overall project status:
```markdown
## Project: E-commerce Platform
- Planning: 100% ✓
- Backend API: 75% 
- Frontend UI: 50%
- Testing: 25%
- Documentation: 10%
Overall: 52% complete
```

## Progress Measurement Patterns

### Percentage Completion Pattern
Calculate based on subtasks:
```
Total tasks: 10
Completed: 7
Progress: 70%

Formula: (completed / total) × 100
```

### Weighted Progress Pattern
Weight by importance/complexity:
```
Task A (weight: 3): 100% = 3.0
Task B (weight: 2): 50% = 1.0
Task C (weight: 1): 0% = 0.0
Total weight: 6
Progress: 4.0/6.0 = 67%
```

### Milestone Progress Pattern
Track against milestones:
```
Milestone 1: ✓ Complete
Milestone 2: ✓ Complete
Milestone 3: ⟳ In Progress (60%)
Milestone 4: ○ Not Started
Progress: 2.6/4 = 65%
```

## Progress Reporting Formats

### Simple Status Format
```markdown
**Status**: In Progress
**Completed**: 5/8 tasks
**Percentage**: 62.5%
**Blocked**: None
**ETA**: 2 hours
```

### Detailed Progress Report
```markdown
## Progress Report - [Date]

### Completed Today
- ✓ Implemented user model
- ✓ Created auth middleware
- ✓ Added validation rules

### In Progress
- ⟳ Writing unit tests (70%)
- ⟳ Documentation (30%)

### Upcoming
- ○ Integration tests
- ○ Performance optimization

### Metrics
- Tasks: 5/10 complete
- Code: 500 lines added
- Tests: 8/15 passing
- Coverage: 65%
```

### Visual Progress Indicators
```markdown
Progress: ████████░░ 80%
Tasks:    [#####...] 5/8
Tests:    [########] 8/8 ✓
Docs:     [##......] 2/8
```

## Checkpoint Patterns

### Regular Checkpoints
Fixed interval progress checks:
```markdown
## Hourly Checkpoint - 14:00
- Completed: 2 tasks
- In progress: 1 task
- Blockers: None
- Next hour: Complete current + start next
```

### Milestone Checkpoints
Progress at key points:
```markdown
## Milestone: API Complete
- All endpoints implemented ✓
- Basic tests written ✓
- Documentation drafted ✓
- Performance tested ✗
Status: 75% complete
```

### Daily Summaries
End-of-day progress:
```markdown
## Daily Summary - 2025-01-15
**Started**: 5 tasks
**Completed**: 3 tasks
**Carried over**: 2 tasks
**Blockers encountered**: 1
**Tomorrow's priority**: Complete carried tasks
```

## Velocity Tracking Patterns

### Simple Velocity
Track completion rate:
```
Day 1: 3 tasks
Day 2: 4 tasks
Day 3: 2 tasks
Average: 3 tasks/day
```

### Weighted Velocity
Account for complexity:
```
Day 1: 10 story points
Day 2: 15 story points
Day 3: 8 story points
Average: 11 points/day
```

### Trending Velocity
Show improvement/decline:
```
Week 1: 20 tasks (baseline)
Week 2: 25 tasks (+25%)
Week 3: 30 tasks (+20%)
Trend: Improving
```

## Blocker Identification Patterns

### Blocker Documentation
```markdown
## Blocker
**Issue**: Cannot access external API
**Impact**: Auth integration blocked
**Detected**: 2025-01-15 10:30
**Resolution**: Waiting for API keys
**Workaround**: Mock API for now
**ETA**: 2 hours
```

### Blocker Categories
1. **Technical**: Code/system issues
2. **Dependencies**: Waiting on others
3. **Resources**: Missing tools/access
4. **Knowledge**: Need information
5. **Decision**: Awaiting approval

### Blocker Impact Assessment
```markdown
Blocker: Database connection issue
Impact:
- 3 tasks blocked
- 2 developers affected
- 4 hour delay estimated
Priority: HIGH
```

## Progress Visualization

### Burndown Pattern
Track remaining work:
```
Start: 100 tasks
Day 1: 90 remaining
Day 2: 75 remaining
Day 3: 60 remaining
Trend: On track
```

### Burnup Pattern
Track completed work:
```
Target: 100 tasks
Day 1: 10 complete
Day 2: 25 complete
Day 3: 40 complete
Projection: Complete by Day 8
```

### Kanban Pattern
Track work states:
```
Todo: 5 tasks
In Progress: 3 tasks
Review: 2 tasks
Done: 10 tasks
Flow: Healthy
```

## Anti-Patterns to Avoid

1. **Fake progress**: Don't report false completion
2. **No measurements**: Always track something
3. **Vague status**: Be specific about progress
4. **Hidden blockers**: Report issues immediately
5. **No timestamps**: Always include when

## Examples

### Good Progress Tracking
```markdown
[2025-01-15 14:30 CEST]
**Progress Update**
- Completed: Login endpoint (2 hours)
- Completed: Input validation (30 min)
- In Progress: Error handling (50% done)
- Blocked: Tests (need test database)
- Overall: 3/5 tasks (60%)
- Velocity: 1.5 tasks/hour
```

### Poor Progress Tracking
```markdown
Made some progress on auth stuff.
Will continue tomorrow.
```

## Related Patterns
- [Work Patterns](work-patterns.md) - Work organization
- [Documentation Patterns](documentation-patterns.md) - Progress documentation
- [Session Patterns](../session/session-patterns.md) - Session progress

## Handler References
Progress tracking is embedded in work management handlers