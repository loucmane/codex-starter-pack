---
id: work-tracking-patterns
type: pattern
category: work-tracking
title: Work Tracking Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - templates/workflows/
  - templates/conventions/
related:
  - patterns/work-tracking/progress-patterns.md
  - patterns/work-tracking/documentation-patterns.md
version: 1.0.0
status: stable
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Work Tracking Patterns

## Pattern Description
Patterns and approaches for tracking work, organizing tasks, and maintaining work context throughout development sessions. These patterns ensure work is properly tracked and can be resumed efficiently.

## Pattern Structure
1. Identify work type
2. Create/locate work folder
3. Initialize tracking files
4. Update progress regularly
5. Maintain work context
6. Document outcomes

## When to Use
- Starting new development work
- Continuing existing work
- Tracking progress on tasks
- Organizing multi-session work
- Documenting work outcomes

## When NOT to Use
- Simple one-off queries
- Quick fixes without context
- Exploration without deliverables
- Casual conversations

## Work Organization Structure

### Work Folder Pattern
```
docs/ai/work-tracking/active/[DATE]-[WORK-NAME]-ACTIVE/
├── TRACKER.md          # Progress tracking
├── FINDINGS.md         # Discoveries and insights
├── IMPLEMENTATION.md   # Implementation details
├── CHANGELOG.md       # Change log
├── DECISIONS.md       # Design decisions
├── MEMORY-REFS.md     # Memory references
├── HANDOFF.md         # Handoff documentation
├── analysis/          # Analysis results
├── archive/           # Archived iterations
├── code/              # Code snippets and scripts
├── designs/           # Design documents
├── plans/             # Planning documents
└── reports/           # Generated reports
```

### File Purposes
**Required Files (7):**
- **TRACKER.md**: Append-only progress log
- **FINDINGS.md**: Key discoveries and insights
- **IMPLEMENTATION.md**: Detailed implementation plan
- **CHANGELOG.md**: Changes made during work
- **DECISIONS.md**: Design decisions and rationale
- **MEMORY-REFS.md**: References to related work
- **HANDOFF.md**: Handoff notes for continuation

**Subdirectories:**
- **analysis/**: Investigation results and data analysis
- **archive/**: Archived iterations and old work
- **code/**: Code snippets, scripts, and examples
- **designs/**: Architecture and design documents
- **plans/**: Planning documents and strategies
- **reports/**: Generated reports and summaries

## Work Activity Pattern

### Pattern Structure
**Triggers**: test, implement, analyze, fix, document, "new feature", "work on", build, develop
**Pre-conditions**: Work type identifiable

### Process
1. Check for active work folder
   ```bash
   ls docs/ai/work-tracking/active/
   ```
2. If exists → Continue existing work
3. If not → Create new work folder
4. Initialize tracking files
5. Begin work with context

### Work Initialization
```markdown
# New Work Setup
1. Create folder: docs/ai/work-tracking/active/YYYYMMDD-work-name-ACTIVE/
2. Create TRACKER.md with header
3. Create FINDINGS.md structure
4. Log initial entry
5. Set work context
```

### Success Criteria
- Work folder created/located
- Tracking initialized
- Context established
- Progress logged

## Work Continuation Pattern

### Pattern Structure
**Triggers**: continue, resume, "back to", "keep working", "where were we"
**Pre-conditions**: Previous work exists

### Process
1. Identify work to continue
   - Check TodoWrite for active tasks
   - Review recent work folders
   - Check sessions/ for context
2. Load work context
   - Read tracker.md for status
   - Review findings.md for decisions
   - Check current iteration
3. Resume from last point
   - Update timestamp
   - Log continuation
   - Continue tasks

### Context Recovery
```markdown
# Context Recovery Steps
1. Read last tracker.md entry
2. Check TodoWrite state
3. Review git status
4. Load relevant files
5. Summarize current state
```

## Progress Tracking Patterns

### Append-Only Tracking
**For**: tracker.md files
**Rule**: Only append, never edit existing entries

```markdown
## Progress Log

[2025-01-15 10:30 CEST]
- Started implementation of auth module
- Created base structure

[2025-01-15 11:15 CEST]
- Added JWT token generation
- Implemented refresh logic
```

### Structured Updates
**For**: findings.md files
**Rule**: Update appropriate sections

```markdown
## Discoveries
- JWT refresh pattern works well
- Need to handle token expiry edge case

## Decisions
- Using 15min access token lifetime
- Refresh tokens last 7 days

## Action Items
- [ ] Add token expiry handling
- [ ] Test refresh flow
```

### Iteration Management
**Pattern**: One file per major iteration
```
iteration-1.md: Initial implementation
iteration-2.md: Refactoring and optimization
iteration-3.md: Testing and documentation
```

## Work State Patterns

### Active Work States
1. **ACTIVE**: Currently being worked on
2. **PAUSED**: Temporarily on hold
3. **BLOCKED**: Waiting for external input
4. **REVIEW**: Under review
5. **TESTING**: In testing phase

### State Transitions
```
NEW → ACTIVE → TESTING → REVIEW → COMPLETED
         ↓         ↓         ↓
      PAUSED   BLOCKED   REVISING
         ↓         ↓         ↓
      ACTIVE    ACTIVE    ACTIVE
```

### State Documentation
Always document state changes in tracker.md:
```markdown
[2025-01-15 14:00 CEST]
- Status: ACTIVE → BLOCKED
- Reason: Waiting for API credentials
- Next: Resume when credentials available
```

## Work Context Patterns

### Context Capture
When starting or resuming work:
1. Current objective
2. Previous progress
3. Next steps
4. Blocking issues
5. Dependencies

### Context Format
```markdown
## Current Context
**Objective**: Implement user authentication
**Progress**: JWT generation complete
**Next**: Add refresh token logic
**Blocked**: None
**Dependencies**: auth-service, database
```

### Context Handoff
For session transitions:
```markdown
## Handoff Notes
**Completed**: Steps 1-3 of auth implementation
**In Progress**: Refresh token endpoint
**Todo**: Testing and error handling
**Notes**: Check edge case for expired tokens
```

## Common Work Patterns

### Feature Development
```
1. Create work folder with feature name
2. Document requirements in README
3. Track implementation in iterations
4. Log discoveries in findings
5. Update tracker with progress
```

### Bug Investigation
```
1. Create work folder with bug ID
2. Document symptoms in README
3. Track investigation in analysis/
4. Log findings as discovered
5. Document fix in iteration file
```

### System Migration
```
1. Create work folder for migration
2. Plan phases in designs/
3. Track each phase in iterations
4. Log issues in findings
5. Document progress in tracker
```

## Work Artifacts

### Required Artifacts
Every work folder must have:
- tracker.md (progress log)
- README.md (work overview)
- At least one iteration file

### Optional Artifacts
Based on work type:
- findings.md (discoveries)
- designs/ (architecture)
- analysis/ (investigation)
- tests/ (test files)
- docs/ (documentation)

## Anti-Patterns to Avoid

1. **Working without tracking**: Always create work folder
2. **Editing tracker.md history**: Only append new entries
3. **Vague progress updates**: Be specific about what was done
4. **Missing context**: Always capture current state
5. **No handoff notes**: Document for next session

## Examples

### Good Work Tracking
```markdown
[2025-01-15 10:30 CEST]
- Implemented UserController.create method
- Added input validation for email and password
- Created unit tests (3 passing)
- Next: Add error handling for duplicate emails
```

### Poor Work Tracking
```markdown
[2025-01-15]
- Worked on stuff
- Made progress
- Will continue later
```

## Related Patterns
- [Progress Patterns](progress-patterns.md) - Progress measurement
- [Documentation Patterns](documentation-patterns.md) - Documentation approaches
- [Session Patterns](../session/session-patterns.md) - Session management

## Handler References
[Handler: work-activity migrated to handlers/orchestrators/work-activity.md]
[Handler: work-continuation migrated to handlers/orchestrators/work-continuation.md]