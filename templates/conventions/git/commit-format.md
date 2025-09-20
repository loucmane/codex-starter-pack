---
id: git-commit-format
type: convention
category: git
title: Git Commit Format (gac)
applies_to: code
enforcement: required
dependencies:
  - branch-naming
version: 1.0.0
status: stable
---

# Git Commit Format (gac)

## Convention
All commits must use the `gac` alias with proper format and SINGLE QUOTES inside messages when quoting.

## The gac Alias

### Definition
```bash
gac='git add . && git commit -m'
```

### Critical Quote Rule
**⚠️ IMPORTANT: Use SINGLE QUOTES (') inside commit messages, NEVER double quotes (")**

## Commit Message Format

### Structure
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting, missing semicolons, etc
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding missing tests
- **chore**: Changes to build process or auxiliary tools

### Scope (Optional)
- Component name: `feat(Button): add loading state`
- Module name: `fix(auth): correct token refresh`
- File type: `docs(README): update installation`

## Examples

### ✅ Correct Examples
```bash
# Simple commits
gac "feat: add user authentication"
gac "fix: resolve memory leak in sidebar"
gac "docs: update API documentation"

# With quotes inside (using single quotes)
gac "feat: add 'Modern Blog' feature"
gac "fix: update 'orchestrate-and-test' command"
gac "docs: improve 'sessions/' structure"
gac "refactor: extract 'useAuth' hook"

# With scope
gac "feat(auth): add OAuth2 support"
gac "fix(Button): correct disabled state"
gac "test(utils): add formatDate tests"

# Multi-line with details
gac "feat: implement user dashboard

- Added dashboard layout
- Created widget components
- Integrated with API

Closes #123"
```

### ❌ Wrong Examples
```bash
# Double quotes inside - WILL BREAK!
gac "feat: add "Modern Blog" feature"      # Shell error!
gac "fix: update "orchestrate" command"    # Shell error!

# Wrong quote style for gac
gac 'feat: add feature'                     # Wrong outer quotes

# Manual git commands instead of gac
git add . && git commit -m "feat: add feature"  # Use gac!

# Poor message format
gac "added stuff"                           # No type prefix
gac "Feature: new button"                   # Wrong type format
gac "feat:no space after colon"            # Missing space
gac "FEAT: uppercase type"                 # Types are lowercase
```

## Commit Message Best Practices

### Subject Line
- **Length**: 50 characters or less
- **Tense**: Present tense imperative ("add" not "added")
- **Case**: Lowercase after type
- **Period**: No period at end

### Body (Optional)
- **When**: For complex changes needing explanation
- **Length**: Wrap at 72 characters
- **Content**: Explain what and why, not how
- **Format**: Bullet points with `-` or `*`

### Footer (Optional)
- **Breaking changes**: `BREAKING CHANGE: description`
- **Issue references**: `Closes #123`, `Fixes #456`
- **Co-authors**: `Co-authored-by: Name <email>`

## Multi-line Commit Format (Codex Default)

### For Complex Changes
Use a short subject line followed by a bulleted body. Two leading spaces keep the bullet indentation intact inside the commit message. Remember to convert inner double quotes to single quotes.

```bash
gac "type(scope): concise summary of change

  - Major accomplishment or change
  - Supporting detail or impacted files
  - Additional context, measurements, or follow-up actions

  Work tracking: YYYYMMDD-folder-ACTIVE"
```

### Real Example
```bash
gac "chore: bootstrap codex ssot migration

  - Imported template system, scanner suite, and work-tracking scaffold
  - Ported Serena/agents configuration into `.codex/`
  - Captured baseline scanner outputs for references, duplicates, migration
  - Documented enforcement plan for codex-task + diff-aware guard

  Work tracking: 20250920-codex-migration-ssot-ACTIVE"
```

## When User Asks for Commit Message

### Response Format
**📋 When user asks for gac commit message:**
- Give ONLY the raw commit message text
- NO code blocks or formatting
- NO "Here's your message:" prefix
- Just the plain text they can use with gac

### Example Response
```
User: "Give me a commit message for the auth changes"
AI: feat: implement OAuth2 authentication with Google and GitHub providers
```

## Common Patterns

### Feature Development
```bash
gac "feat: initial component structure"
gac "feat: add component props and types"
gac "feat: implement component logic"
gac "test: add component tests"
gac "docs: add component documentation"
```

### Bug Fixing
```bash
gac "fix: identify issue in error handling"
gac "fix: implement corrected logic"
gac "test: add regression test"
gac "docs: update changelog"
```

### Refactoring
```bash
gac "refactor: extract helper functions"
gac "refactor: simplify component structure"
gac "refactor: improve type definitions"
gac "test: update tests for refactored code"
```

## Rationale

### Why gac
1. **Consistency**: Same command for all commits
2. **Efficiency**: Combines add and commit
3. **Safety**: Adds all changes (intentional)
4. **Simplicity**: Shorter than manual commands

### Why Single Quotes Inside
1. **Shell Parsing**: Double quotes break shell parsing
2. **Escape Complexity**: Avoids complex escaping
3. **Consistency**: One rule for all quoted content
4. **Error Prevention**: Eliminates common shell errors

### Benefits
- **Searchable History**: Type prefixes enable filtering
- **Clear Intent**: Type immediately shows purpose
- **Changelog Generation**: Tools can parse format
- **Team Understanding**: Standard format for all
- **CI/CD Integration**: Automated version bumping
