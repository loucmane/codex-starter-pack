---
id: serena-memory-patterns
type: workflow-component
category: memory
title: Serena Memory Usage Patterns
dependencies:
  - ../session/lifecycle.md
related:
  - ./memory-lifecycle.md
  - ./memory-format.md
version: 1.0.0
status: stable
---

# Serena Memory Usage Patterns

## When to Create Memories

### Required Memory Points

1. **Session End**
   - Every session MUST create a memory
   - Format: `session_YYYY-MM-DD_descriptive_name`
   - Contains complete work summary

2. **Major Milestones**
   - Feature completion
   - System integration
   - Architecture decisions
   - Breaking changes

3. **Complex Discoveries**
   - Bug root causes
   - Performance insights
   - Integration patterns
   - Workflow improvements

## Memory Content Structure

### Session Memory Template

```markdown
# Session Memory: [Date] - [Topic]

## Session Overview
- **Date**: [YYYY-MM-DD]
- **Duration**: [Start time - End time]
- **Developer**: [Name from git config]
- **Task**: [TaskMaster ID and description]
- **Branch**: [git branch name]

## Work Completed
### Subtasks Finished
- ✅ 7.1: Semantic HTML Structure
  - Files: index.html, base-structure.css
  - Key decisions: Used semantic5 elements
  
- ✅ 7.2: Header Component  
  - Files: Header.tsx, header.module.css
  - Challenges: Mobile menu overlap on small screens
  - Solution: Adjusted positioning with media queries

### Code Changes
- `components/Header.tsx` - Created responsive header
- `styles/header.module.css` - Mobile-first styling
- `hooks/useMediaQuery.ts` - Responsive utilities

## Unfinished Work
### In Progress
- 🔄 7.3: Mobile Navigation (50% complete)
  - Gesture handling implemented
  - Focus trap pending
  - Accessibility review needed

### Blocked Items
- 🚫 Payment integration - Waiting for API keys

## Important Discoveries
1. **Mobile Menu Pattern**: Swipe gestures conflict with browser back
   - Decision: Use tap-only interactions
   - Rationale: Better browser compatibility

2. **Component Architecture**: Need consistent prop interfaces
   - Action: Create shared types file
   - Impact: Better TypeScript support

## Test Results
- Header Component: ✅ All tests passing
- Mobile Navigation: ⚠️ 2 tests pending
- Accessibility: ✅ WCAG AA compliant

## Decisions & Rationale
### Why We Chose [Approach]
- **Context**: [What problem we faced]
- **Options**: [What we considered]
- **Choice**: [What we decided]
- **Result**: [How it worked out]

## How to Initialize Next Session
```
Activate project MomsBlog, read memory session_YYYY-MM-DD_topic and sessions/
```

## Key Files to Review
- sessions/ - Latest progress
- tracker.md - Current sprint status
- handoff.md - Specific next steps
```

## Memory Naming Conventions

### Session Memories
- Pattern: `session_YYYY-MM-DD_descriptive_topic`
- Example: `session_2025-07-30_template_migration`

### Milestone Memories
- Pattern: `milestone_YYYY-MM-DD_achievement`
- Example: `milestone_2025-07-30_auth_system_complete`

### Discovery Memories
- Pattern: `discovery_YYYY-MM-DD_finding`
- Example: `discovery_2025-07-30_react_hydration_fix`

## Memory Search Patterns

### Finding Recent Work
```bash
# List all session memories
ls -la .serena/memories/session_* | tail -5

# Find memories about specific topic
grep -l "template" .serena/memories/*.md

# Get latest session memory
ls -t .serena/memories/session_* | head -1
```

### Cross-Referencing
- Always check sessions/current first
- Then read relevant Serena memories
- Compare for consistency
- Note any gaps or conflicts

## Memory Integration Points

1. **Session Start**
   - Read previous session memory
   - Verify against sessions/
   - Note continuation points

2. **During Work**
   - Reference relevant discoveries
   - Apply learned patterns
   - Avoid repeated mistakes

3. **Session End**
   - Summarize work completed
   - Document blockers
   - Provide clear handoff

## Best Practices

### DO:
- ✅ Create memory BEFORE ending session
- ✅ Include specific file names and paths
- ✅ Document both successes and failures
- ✅ Provide clear initialization instructions
- ✅ Cross-reference with sessions/

### DON'T:
- ❌ Create vague or generic memories
- ❌ Omit test results or verification
- ❌ Forget unfinished work status
- ❌ Skip decision rationale
- ❌ Duplicate sessions/ entirely

## Memory Verification

After creating a memory:
1. Confirm file exists in `.serena/memories/`
2. Verify it contains initialization instructions
3. Check cross-references are accurate
4. Ensure handoff is complete