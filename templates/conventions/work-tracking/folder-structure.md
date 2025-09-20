---
id: work-folder-structure
type: convention
category: work-tracking
title: Work Folder Format (YYYYMMDD-name-STATUS)
applies_to: files
enforcement: required
dependencies:
  - tracker-format
  - handoff-format
version: 1.0.0
status: stable
---

# Work Folder Structure Convention

## Start here

- Path: `docs/ai/work-tracking/active/YYYYMMDD-<slug>-ACTIVE/`
- Create these 7 files (ALL CAPS) in the new folder:
  - `IMPLEMENTATION.md`
  - `TRACKER.md`
  - `CHANGELOG.md`
  - `FINDINGS.md`
  - `DECISIONS.md`
  - `MEMORY-REFS.md`
  - `HANDOFF.md`
- Quick scaffold (copy/paste):
```bash
folder="docs/ai/work-tracking/active/$(date +%Y%m%d)-<slug>-ACTIVE" \
&& mkdir -p "$folder" && cd "$folder" \
&& for f in IMPLEMENTATION.md TRACKER.md CHANGELOG.md FINDINGS.md DECISIONS.md MEMORY-REFS.md HANDOFF.md; do echo "# $f" > "$f"; done
```
- Recommended (once available): `scripts/work-tracking/new.sh --title "<slug>"`

Anchors you may need next: `#path-and-naming`, `#required-files`, `#file-roles`.

## Path and naming

Use the exact path under `docs/ai/work-tracking/active/` and the date from `date +%Y%m%d` to avoid mistakes. See details below in Folder Location and Folder Naming Format.

## Convention
Work tracking folders must follow a consistent naming pattern and contain standardized documentation files to track progress and enable seamless handoffs.

## Folder Naming Format

### Pattern
```
YYYYMMDD-description-STATUS
```

### Components
- **YYYYMMDD**: Date created (from `date +%Y%m%d`)
- **description**: Kebab-case description of work
- **STATUS**: Current status in CAPS

### Status Values
- **ACTIVE**: Currently being worked on
- **COMPLETE**: Successfully finished
- **PAUSED**: On hold, may resume
- **BLOCKED**: Waiting on external dependency
- **ABANDONED**: Stopped, won't continue
- **SUPERSEDED**: Replaced by newer approach

### Examples
```
20250730-template-migration-ACTIVE
20250729-auth-implementation-COMPLETE
20250728-ui-redesign-PAUSED
20250727-payment-integration-BLOCKED
20250726-old-approach-ABANDONED
20250725-legacy-system-SUPERSEDED
```

## Folder Location

### Directory Structure
```
docs/ai/work-tracking/
├── active/              # Current work
├── completed/           # Finished work
├── paused/              # On hold
├── blocked/             # Waiting
├── abandoned/           # Stopped
└── superseded/          # Replaced
```

### Archive Rules
- Move folders when status changes
- Preserve folder name including STATUS
- Never delete work folders
- Update STATUS suffix when moving

## Required Files

### Core Files (7 Required)
1. **IMPLEMENTATION.md** - The implementation PLAN
2. **TRACKER.md** - Checkbox task tracking
3. **CHANGELOG.md** - Actual changes made
4. **FINDINGS.md** - Discoveries and insights
5. **DECISIONS.md** - Key decisions with rationale
6. **MEMORY-REFS.md** - Related session memories
7. **HANDOFF.md** - Session transition info

### File Purposes

#### IMPLEMENTATION.md
```markdown
# Implementation Plan

## Overview
What we intend to build/change

## Approach
Technical approach and architecture

## Steps
1. Detailed implementation steps
2. In order of execution
3. With technical details

## Success Criteria
- Clear success metrics
- Definition of done
```

#### TRACKER.md
```markdown
# [Feature] Tracker

**Started**: [Date]
**Status**: ACTIVE
**Last Updated**: [Date]

## Goals
- [ ] Primary goal
- [x] Completed goal
- [ ] Secondary goal

## Progress Log
- **YYYY-MM-DD HH:MM**: Entry

## Current State
[Current status - REPLACE when updating]

## Next Steps
[Upcoming actions - REPLACE when updating]
```

#### CHANGELOG.md
```markdown
# Changelog

## [Date]

### Added
- New feature or file

### Changed
- Modified behavior

### Fixed
- Bug fixes

### Removed
- Deleted code or files
```

#### FINDINGS.md
```markdown
# Findings

## Discoveries
- Important discovery with context
- Unexpected behavior found

## Test Results
- Test outcome and implications

## Performance Observations
- Metrics and measurements

## Issues Encountered
- Problems and their solutions
```

#### DECISIONS.md
```markdown
# Decisions

## [Date] - Decision Title

### Context
Why decision was needed

### Options Considered
1. Option A - Pros/Cons
2. Option B - Pros/Cons

### Decision
What was chosen and why

### Consequences
Implications of this decision
```

#### MEMORY-REFS.md
```markdown
# Memory References

## Related Sessions
- session_2025-07-30_description.md
- session_2025-07-29_other_work.md

## Key Context
- Important background info
- Previous attempts
- Lessons learned
```

#### HANDOFF.md
```markdown
# Handoff Document

**Last Session**: [Date Time]
**Last Worked By**: [Developer]
**Current State**: [Brief status]

## What Was Done
- Completed work items

## Current Issues/Blockers
- Any problems
- Unresolved questions

## Next Steps
1. Priority action
2. Secondary action

## How to Continue
Exact commands or steps to resume
```

## Optional Subdirectories

### Extended Structure
```
work-folder/
├── IMPLEMENTATION.md    # Required
├── TRACKER.md          # Required
├── CHANGELOG.md        # Required
├── FINDINGS.md         # Required
├── DECISIONS.md        # Required
├── MEMORY-REFS.md      # Required
├── HANDOFF.md          # Required
├── plans/              # Detailed plans
├── designs/            # Architecture docs
├── code/               # Code attempts
├── archive/            # Old versions
└── reports/            # Analysis reports
```

## When to Create Work Folders

### Create NEW Folder When
- Starting new feature/initiative
- Different project phase
- Unrelated to existing work
- Major pivot in approach

### Continue EXISTING Folder When
- Same overall initiative
- Related subtasks
- Natural progression
- Minor adjustments

## Work Preservation

### Never Delete
- Keep all work folders
- Archive completed work
- Preserve failed attempts
- Document abandoned reasons

### Version Control
```
code/
  v1-failed.md     # What didn't work
  v2-working.md    # Current approach
  v3-optimized.md  # Improvements
```

## Examples

### ✅ Good Folder Structure
```
20250730-template-migration-ACTIVE/
  IMPLEMENTATION.md    # Clear plan
  TRACKER.md          # Tasks tracked
  CHANGELOG.md        # Changes documented
  FINDINGS.md         # Discoveries noted
  DECISIONS.md        # Choices explained
  MEMORY-REFS.md      # Context linked
  HANDOFF.md          # Ready for handoff
```

### ❌ Poor Folder Structure
```
template-work/           # No date
  notes.md              # Non-standard file
  todo.txt              # Wrong format
```

## Critical Date Rule

### Always Use Command
```bash
# Get folder date
date +%Y%m%d
# Output: 20250730

# Create folder
mkdir "$(date +%Y%m%d)-feature-name-ACTIVE"
```

### Never Type Manually
- ❌ 20250730 (typed from memory)
- ✅ `date +%Y%m%d` (command output)

## Rationale

### Why These Conventions

1. **Chronological Order**: Date prefix enables sorting
2. **Status Visibility**: STATUS suffix shows at a glance
3. **Complete Documentation**: All aspects tracked
4. **Easy Handoffs**: Standardized structure
5. **Knowledge Preservation**: Nothing lost

### Benefits
- **Organization**: Clear folder structure
- **Traceability**: Complete audit trail
- **Continuity**: Anyone can pick up work
- **Learning**: Failed attempts documented
- **Efficiency**: No duplicate efforts