---
trigger: Progress milestones, discoveries, decisions, or context switches
action: Update relevant work tracking files immediately
blocks: Cannot proceed without documenting progress
category: work-tracking
enforcement: mandatory
version: 1.0.0
---

# Work Tracking Updates

## Trigger Conditions
This behavior fires on multiple work events:

### 1. Starting New Work
- Beginning any development task
- Starting feature implementation
- Initiating bug fix

### 2. Significant Discoveries
- Found bug cause
- Identified pattern
- Discovered solution
- Uncovered insight

### 3. Making Decisions
- Chose approach or tool
- Selected pattern or direction
- Decided on implementation

### 4. Progress Milestones
- Completed todo item
- Reached checkpoint
- Finished component

### 5. Time-Based
- Every 30 minutes of active work
- Before context switch
- At session end

### 6. Test Events
- Test failures
- Test fixes
- Validation results

## Required Actions by Trigger

### Before Starting Work
```
1. Check for work tracking folder:
   mcp__serena__search_for_pattern --substring_pattern "Create Work Tracking" --relative_path "templates/workflows/"
   
2. Create folder structure (ALL CAPS):
   /docs/ai/work-tracking/active/YYYYMMDD-description-ACTIVE/
   
3. Initialize 7 required files:
   - TRACKER.md (checkbox tasks)
   - IMPLEMENTATION.md
   - FINDINGS.md  
   - DECISIONS.md
   - HANDOFF.md
   - MEMORY-REFS.md
   - DISCUSSION.md
   
4. Create subfolders:
   - code/
   - analysis/
   - designs/
   - reports/
   - plans/
```

### After Significant Discovery
```
Update FINDINGS.md within 2 minutes:

### [Timestamp] - [Brief Title]
#### The Discovery
[What was found]

#### Evidence
[Code snippets, error messages, data]

#### Why It Matters  
[Impact and implications]

#### Next Steps
[What this enables or requires]
```

### After Making Decisions
```
Update DECISIONS.md before implementing:

### [Number]. [Decision Title]
**Decision**: [What was decided]
**Rationale**: [Why this choice]
**Alternatives Considered**: [Other options evaluated]
**Evidence**: [What supports this decision]
**Impact**: [Expected outcomes]
```

### After Progress Milestones
```
Update both files immediately:

1. TRACKER.md:
   - Check completed todo: [x]
   - Add progress log entry:
     - **HH:MM** - [What was completed]
   
2. IMPLEMENTATION.md:
   - Document what was built
   - Include file paths
   - Note any deviations from plan
```

### Every 30 Minutes Active Work
```
Checkpoint update in TRACKER.md:

### Progress Log
- **HH:MM** - Checkpoint: [Current status]
  - Active: [What you're working on]
  - Completed: [What's done since last checkpoint]
  - Blockers: [Any issues encountered]
  - Next: [Immediate next steps]
```

### Before Context Switch
```
Update HANDOFF.md with state:

## Current State (HH:MM)
### Stopping Point
[Exactly where work stopped]

### Active Files
- [File path]: [What was being done]

### Next Steps
1. [Immediate next action]
2. [Following action]

### Open Questions
- [Any unresolved issues]

### Notes for Resume
[Any context needed to continue]
```

### When Tests Fail
```
Document in FINDINGS.md:

### [Timestamp] - Test Failure: [Test Name]
#### Error
```
[Exact error message]
```

#### Expected vs Actual
- Expected: [What should happen]
- Actual: [What happened]

#### Initial Hypothesis
[Why might this be failing]

#### Fix Applied
[What was changed]

#### Result
[Did it work?]
```

## Blocking Gate
**CANNOT PROCEED** without updates when:
- Starting work → Work folder must exist
- Finding something → FINDINGS.md must be updated
- Making decision → DECISIONS.md must be updated  
- Completing task → TRACKER.md must be checked
- Switching context → HANDOFF.md must be current
- 30 minutes elapsed → Checkpoint required

## Satisfaction Criteria
✓ Work tracking folder exists (if starting work)
✓ Relevant file updated within time window
✓ Update includes required information
✓ Timestamp is accurate (from date command)
✓ Progress is traceable through updates

## File-Specific Formats

### TRACKER.md Format
```markdown
# Task Tracker

## Todos
- [ ] Research task
- [x] Implementation task (completed HH:MM)
- [►] Active task (in progress)

## Progress Log
- **HH:MM** - Started work
- **HH:MM** - Completed research
- **HH:MM** - Implementation begun
```

### FINDINGS.md Format
```markdown
# Findings

### YYYY-MM-DD HH:MM - Finding Title
#### The Discovery
[Details]

#### Evidence
[Proof/data]

#### Impact
[What this means]
```

### DECISIONS.md Format
```markdown
# Decisions

### 1. Decision Title
**Decision**: [What]
**Rationale**: [Why]
**Date**: YYYY-MM-DD
```

## Cross-References
- [WORKFLOWS.md#create-work-tracking](../../templates/workflows/)
- [timestamps/before-adding.md](../timestamps/before-adding.md)
- [session/session-end.md](../session/session-end.md)
- [CONVENTIONS.md#work-tracking](../../templates/conventions/)

## Error Cases
- **No work folder**: Create immediately before continuing
- **Can't update**: Note issue and continue, fix later
- **File missing**: Recreate from template
- **Time elapsed**: Do checkpoint even if late

## Why This Gate Exists
- Creates comprehensive audit trail
- Enables work continuity
- Captures insights in real-time
- Prevents knowledge loss
- Supports handoffs and context switches
- Documents decision rationale

## Remember
**Real-time documentation is not optional - it's how we maintain work continuity and capture insights as they happen!**