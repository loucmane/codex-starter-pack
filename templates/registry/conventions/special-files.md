---
id: special-files
title: Special Files Conventions
type: registry-component
name: Special Files Conventions
description: File-specific rules and conventions for special system files
status: stable
cross_references:
  - ../index.md
  - ../matrices/decision-matrices.md
  - ../behavioral/hooks.md
---

# Special Files Conventions

Rules for specific files that require special handling.

## Append-Only Files

These files should only have content appended, never edited or deleted from existing sections.

### TRACKER.md
- **Location**: In each work folder
- **Append Section**: Progress Log
- **Format**: Timestamped entries
- **Example**:
  ```markdown
  ## Progress Log
  - **09:45** - Started investigating issue
  - **10:15** - Found root cause in auth module
  - **10:30** - Implemented fix with tests
  ```
- **Never**: Edit previous entries, delete entries, modify timestamps

### FINDINGS.md
- **Location**: In each work folder
- **Append Section**: Discoveries
- **Format**: Numbered findings with evidence
- **Example**:
  ```markdown
  ## Discoveries
  1. The auth module uses JWT tokens (auth.js:45)
  2. Token expiry is set to 24 hours (config.js:12)
  3. Refresh mechanism exists but unused (auth.js:78)
  ```
- **Never**: Modify existing findings, change numbering

### sessions/
- **Location**: Project root
- **Append Section**: After "Current Focus" section
- **Format**: Session progress updates
- **Special Rules**:
  - Archive to sessions/ when >1000 lines
  - Compact when requested
  - Preserve Current Focus section
- **Never**: Edit archived content, delete session history

### HANDOFF.md
- **Location**: In each work folder
- **Append Section**: Handoff Notes
- **Format**: Context for next session
- **Example**:
  ```markdown
  ## Handoff Notes
  - Left off at: Implementing user service tests
  - Next steps: Complete error handling
  - Blocker: Need API key for external service
  ```
- **Never**: Remove previous handoff notes

## Never-Edit Files

These files should never be directly edited.

### Generated Files
| File/Pattern | Reason | Alternative |
|--------------|--------|-------------|
| package-lock.json | NPM generated | Use npm install/update |
| yarn.lock | Yarn generated | Use yarn add/remove |
| .next/* | Next.js build | Modify source files |
| build/* | Build output | Modify source files |
| dist/* | Distribution files | Modify source files |
| coverage/* | Test coverage | Run tests to update |

### System Files
| File/Pattern | Reason | Alternative |
|--------------|--------|-------------|
| .git/* | Git internals | Use git commands |
| node_modules/* | Dependencies | Use package manager |
| .DS_Store | macOS system | Delete if needed |
| Thumbs.db | Windows system | Delete if needed |
| *.log | Log files | Read-only reference |

## Conditionally Editable Files

These files have specific conditions for editing.

### Configuration Files
| File | When to Edit | Restrictions |
|------|--------------|--------------|
| package.json | Adding dependencies | Maintain valid JSON |
| tsconfig.json | TypeScript config | Test after changes |
| .eslintrc | Linting rules | Team agreement needed |
| .prettierrc | Format rules | Team agreement needed |
| .gitignore | Ignore patterns | Never ignore critical files |
| .env | Environment vars | Never commit secrets |
| .env.local | Local overrides | Keep in .gitignore |

### Documentation Files
| File | Edit Rules | Format Requirements |
|------|------------|-------------------|
| README.md | Keep updated | Include all sections |
| CHANGELOG.md | Add new entries | Follow keepachangelog |
| CONTRIBUTING.md | Update process | Clear instructions |
| LICENSE | Never edit | Legal document |
| CODE_OF_CONDUCT.md | Team updates only | Follow template |

## Template System Files

Special rules for Claude template system files.

### Core Templates
| File | Location | Edit Rules |
|------|----------|------------|
| CLAUDE.md | Root | System updates only |
| REGISTRY.md | templates/ | Now replaced by modular registry |
| templates/workflows/ | templates/ | Preserve templates |
| TOOLS.md | templates/ | Tool matrix updates |
| templates/conventions/ | templates/ | Team agreement |
| templates/patterns/ | templates/ | Add new patterns |
| BEHAVIORS.md | templates/ | Hook additions |
| templates/matrices/ | templates/ | Matrix updates |

### Handler Files
| Pattern | Location | Requirements |
|---------|----------|--------------|
| *.md | handlers/*/* | Must have YAML frontmatter |
| triggers/* | handlers/triggers/ | Must have triggers field |
| orchestrators/* | handlers/orchestrators/ | Must coordinate |
| operators/* | handlers/operators/ | Must be atomic |

## File Operation Rules

### Before Creating
1. Check if file exists
2. Verify naming convention
3. Confirm correct location
4. Check special file rules
5. Apply appropriate template

### Before Editing
1. Read file completely
2. Check if append-only
3. Verify edit permissions
4. Backup if critical
5. Validate after edit

### Before Deleting
1. Check for references
2. Verify not system file
3. Confirm not needed
4. Consider archiving instead
5. Update any indexes

## Common Patterns

### The 7-File Work Structure
Every work folder must have:
```
YYYYMMDD-description-STATUS/
├── README.md         # Overview
├── PLAN.md          # Approach
├── TRACKER.md       # Progress (append-only)
├── FINDINGS.md      # Discoveries (append-only)
├── HANDOFF.md       # Context (append-only)
├── TODO.md          # Task list
└── sessions/        # Archived sessions
```

### Handler File Structure
Every handler must have:
```yaml
---
id: handler-name
name: Human Readable Name
role: trigger|orchestrator|operator
domain: development|git|search|debug|test|docs|workflow
stability: stable|beta|experimental
version: 1.0.0
---

# Handler content...
```

### Timestamp Format
Always use consistent format:
- Progress logs: `**HH:MM**` (24-hour)
- Dates: `YYYY-MM-DD` (ISO 8601)
- Full timestamp: `YYYY-MM-DD HH:MM:SS`
- Never estimate - always use actual time

## File Safety Checklist

Before any file operation, verify:

- [ ] Not a never-edit file
- [ ] Not a system/generated file
- [ ] Following naming conventions
- [ ] In correct location
- [ ] Has required structure
- [ ] Respects append-only rules
- [ ] Maintains file format
- [ ] Preserves critical content
- [ ] Updates related indexes
- [ ] Documents the change

## Progress Log

- **2026-04-22 15:53** — [S:20260422|W:task91-standardize-template-metadata|H:templates/registry/conventions/special-files.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 registry-family standardization slice
