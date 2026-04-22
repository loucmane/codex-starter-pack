---
trigger: User mentions "gac" or asks for commit message
title: Before Commit (gac Format)
action: Validate commit format and ensure no double quotes
blocks: Cannot provide message with wrong format or quotes
category: git
type: behavior
enforcement: mandatory
status: stable
version: 1.0.0
---

# Before Commit (gac Format)

## Trigger Condition
This behavior fires whenever:
- User says "gac" or "give me gac"
- User asks for a commit message
- About to commit changes
- Creating commit message for user
- User mentions git commit

## Required Action
```
CRITICAL CHECKLIST - MUST VERIFY ALL:
□ NO double quotes inside message (would break gac)
□ Has type prefix (feat/fix/docs/chore/style/refactor/test)
□ Subject line fits "type(scope): summary" format
□ Multi-line body (when present) uses two-space bullet list
□ Any internal quotes use single quotes (')
□ Message provided raw (no code blocks / wrappers)
```

### Step-by-Step Process
1. **Check Quote Safety**
   - Scan entire message for double quotes
   - Replace with single quotes if needed
   - NEVER include double quotes inside

2. **Verify Conventional Format**
   - Must start with type prefix
   - Colon and space after type
   - Lowercase description

3. **Output Format**
   - Raw text only
   - No code blocks
   - No markdown formatting
   - No "Here's your message:" prefix

## Blocking Gate
**CANNOT PROCEED** with commit message until:
- All double quotes removed/replaced
- Conventional commit format verified
- Raw output format confirmed
- No formatting or wrappers

## Satisfaction Criteria
✓ Zero double quotes inside message
✓ Has valid type prefix
✓ Follows type: description format
✓ Output is raw text only
✓ Any quotes are single quotes

## Example Workflows

### ❌ Wrong Approaches
```
User: "gac"
AI: ```
feat: add "new" feature
```
Problem: Code block wrapper and double quotes

User: "give me gac"  
AI: Here's your commit message:
feat: implement user "authentication"
Problem: Extra text and double quotes

User: "gac"
AI: feat: add "special" handling
Problem: Double quotes will break gac command
```

### ✅ Correct Approach
```
User: "gac"
AI: feat: add new feature with 'special' handling

User: "give me gac"
AI: fix: resolve navigation bug in mobile view

User: "commit message"
AI: docs: update README with installation steps
```

## Conventional Commit Types

| Type | When to Use | Example |
|------|------------|---------|
| feat | New feature | feat: add user authentication |
| fix | Bug fix | fix: resolve memory leak in parser |
| docs | Documentation | docs: update API documentation |
| style | Formatting only | style: fix indentation in components |
| refactor | Code restructure | refactor: extract helper functions |
| test | Test changes | test: add unit tests for auth |
| chore | Maintenance | chore: update dependencies |
| perf | Performance | perf: optimize database queries |
| ci | CI/CD changes | ci: add GitHub Actions workflow |

## Multi-line Commit Format
When user needs detailed commit:
```
type(scope): concise summary of change

  - Primary outcome or change
  - Supporting detail (files, counts, measurements)
  - Follow-up actions or context (tests, docs, plans)

  Work tracking: YYYYMMDD-work-folder-ACTIVE
```

## Special gac Considerations

### Why No Double Quotes?
The gac alias wraps the message in double quotes:
```bash
gac "your message here"
```
If message contains double quotes, it breaks the command.

### Work Tracking in Commits
For work tracking commits, append folder reference:
```
feat: implement user profile component

Work tracking: 20250127-user-profile-ACTIVE
```

### Breaking Changes
For major changes, use BREAKING CHANGE:
```
feat: redesign authentication flow

BREAKING CHANGE: removes legacy auth endpoints
```

## Cross-References
- [CONVENTIONS.md#git-conventions](../../templates/conventions/)
- [TOOLS.md#git-operations](../../templates/TOOLS.md)
- [session/session-end.md](../session/session-end.md) - Session end commits

## Error Cases
- **User wants quotes**: Use single quotes and explain
- **Complex message**: Break into multi-line format
- **Non-conventional type**: Suggest closest match
- **Too long**: Shorten to under 72 characters

## Quick Validation Script
Mental check before outputting:
```
Is it raw text? ✓
No double quotes? ✓  
Has type prefix? ✓
No code blocks? ✓
→ Safe to output
```

## Why This Gate Exists
- Prevents broken git commands
- Ensures consistent commit history
- Maintains conventional format
- Enables automated changelog generation
- Supports commit parsing tools

## Remember
**When user says "gac" they want ONLY the commit message - nothing else!**

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/git/before-commit.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
