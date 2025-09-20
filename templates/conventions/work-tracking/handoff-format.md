---
id: handoff-format
type: convention
category: work-tracking
title: HANDOFF.md Format Standards
applies_to: documentation
enforcement: required
dependencies:
  - tracker-format
  - work-folder-structure
version: 1.0.0
status: stable
---

# HANDOFF.md Format Standards

## Convention
HANDOFF.md files must provide complete context for seamless work transitions between sessions or developers.

## Required Structure

### File Template
```markdown
# Handoff Document

**Last Session**: 2025-07-30 16:45 CEST
**Last Worked By**: John Doe
**Current Branch**: feat/template-migration
**Session Memory**: session_2025-07-30_template_migration.md
**Current State**: Migration 50% complete, awaiting validation

## What Was Done
- ✅ Completed template scanner implementation
- ✅ Migrated 127 handlers to new structure
- ✅ Updated migration state tracking
- 🔄 Partial: Reference updates (30% done)
- ❌ Failed: Automated validation (needs fix)

## Current Issues/Blockers
### Critical
- Validation script fails on handlers with complex metadata
- Migration state file lock issue on concurrent runs

### Non-Critical
- Performance degradation on files > 1000 lines
- Some handlers missing domain classification

## Test Results
- Unit tests: 95% passing (2 failures in validator)
- Integration tests: Not yet run
- Manual testing: Basic flows verified

## Next Steps
1. **Fix validation script** - See error in `logs/validation-error.log`
2. **Complete remaining 130 handlers** - Use `npm run migrate:continue`
3. **Update all template references** - List in `migration-mapping.md`
4. **Run full test suite** - `pnpm test:all`
5. **Generate final report** - `npm run report:generate`

## Important Context
### Decisions Made
- Chose to preserve handler IDs for backwards compatibility
- Decided to skip deprecated handlers (marked with @deprecated)
- Using staging directory for safety before final move

### Gotchas Discovered
- Handler names with special characters need escaping
- Some handlers have circular dependencies (list in FINDINGS.md)
- YAML frontmatter parser is strict about indentation

## File States
### Modified Files
- `templates/REGISTRY.md` - Updated with new paths
- `templates/workflows/` - Partially updated
- `migration-state.json` - Current migration progress

### Files to Review
- `.claude/staging/handlers/` - All migrated handlers
- `.claude/agent-outputs/template-migrator/errors.log`
- `migration-mapping.md` - Source to destination mapping

## Environment Setup
### Required Tools
- Node.js >= 18.0.0
- pnpm 8.x
- Template scanner agent active

### Environment Variables
```bash
export MIGRATION_MODE=staging
export VALIDATE_STRICT=false
export DEBUG_MIGRATION=true
```

## How to Continue

### Quick Resume
```bash
# 1. Navigate to project
cd /home/user/project

# 2. Check current state
cat migration-state.json | jq '.summary'

# 3. Continue migration
npm run migrate:continue

# 4. If validation fails
npm run validate:fix
```

### Full Context Load
```bash
# Read session memory
cat .serena/memories/session_2025-07-30_template_migration.md

# Check tracker status
cat docs/ai/work-tracking/active/20250730-template-migration-ACTIVE/TRACKER.md

# Review errors
tail -n 50 .claude/agent-outputs/template-migrator/errors.log
```

## Session End Checklist
- [x] Updated TRACKER.md with final progress
- [x] Created session memory with key decisions
- [x] Committed current changes
- [x] Updated this HANDOFF.md
- [x] Noted any breaking changes
```

## Section Details

### Header Metadata
- **Last Session**: Exact timestamp from `date "+%Y-%m-%d %H:%M %Z"`
- **Last Worked By**: From `git config user.name`
- **Current Branch**: From `git branch --show-current`
- **Session Memory**: Link to relevant memory file
- **Current State**: One-line summary

### What Was Done
- Use checkmarks for status:
  - ✅ Completed
  - 🔄 Partial
  - ❌ Failed
  - 🧪 Testing
- Include file references
- Be specific about scope

### Current Issues
- Separate critical from non-critical
- Include error messages or logs
- Link to relevant files
- Describe attempted solutions

### Next Steps
- Numbered priority order
- Include specific commands
- Reference relevant files
- Note dependencies

### Important Context
- Decisions with rationale
- Discovered gotchas
- Assumptions made
- External dependencies

## Examples

### ✅ Good HANDOFF.md
```markdown
# Handoff Document

**Last Session**: 2025-07-30 17:00 CEST
**Last Worked By**: Alice Smith
**Current Branch**: feat/auth-system
**Session Memory**: session_2025-07-30_auth_implementation.md
**Current State**: OAuth implemented, testing in progress

## What Was Done
- ✅ Implemented Google OAuth flow
- ✅ Added session management with Redis
- 🔄 Partial: GitHub OAuth (80% complete)
- 🧪 Testing: Integration tests written, not run

## Current Issues/Blockers
### Critical
- GitHub OAuth callback URL mismatch in production config
  - Error: "Redirect URI mismatch"
  - Config location: `.env.production`
  
### Non-Critical  
- Session timeout not configurable (hardcoded to 24h)
- No user profile picture handling

## Next Steps
1. **Fix GitHub OAuth** - Update callback URL in `.env.production`
2. **Run integration tests** - `pnpm test:integration`
3. **Add profile picture handling** - See TODO in `UserProfile.tsx:45`

## How to Continue
```bash
# Load context
cat sessions/

# Check test status
pnpm test:integration --reporter=verbose

# Start dev server
pnpm dev
```
```

### ❌ Poor HANDOFF.md
```markdown
# Handoff

Did some work on auth. 

Some issues with OAuth.

Next: Fix the bugs and continue.
```

## Integration Points

### With TRACKER.md
- HANDOFF captures session-end state
- TRACKER maintains ongoing progress
- Both reference same work items

### With sessions/
- SESSION has detailed progress
- HANDOFF has transition summary
- Memory file bridges sessions

### With Memory Files
- HANDOFF references relevant memory
- Memory has detailed context
- Together enable full continuity

## Update Timing

### When to Update
- End of every work session
- Before switching tasks
- When blocked or paused
- Before requesting help
- At natural pause points

### Update Commands
```bash
# Get current time
date "+%Y-%m-%d %H:%M %Z"

# Get current user
git config user.name

# Get current branch
git branch --show-current

# Check file states
git status --short
```

## Rationale

### Why These Conventions

1. **Seamless Handoffs**: Complete context for transitions
2. **Quick Resume**: Clear steps to continue work
3. **Issue Tracking**: Problems documented with solutions
4. **Decision History**: Rationale preserved
5. **Time Efficiency**: No context reconstruction needed

### Benefits
- **Continuity**: Work continues smoothly
- **Collaboration**: Multiple developers can contribute
- **Debugging**: Issues documented with context
- **Knowledge Transfer**: Decisions and learnings captured
- **Productivity**: Fast session startup