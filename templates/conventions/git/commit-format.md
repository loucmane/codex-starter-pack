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
All commits must use the `gac` alias with double-quoted messages. Use single quotes only when you are quoting a literal string, command, or title inside the message; avoid them when they are not needed.

## The gac Alias

### Definition
```bash
gac='git add . && git commit -m'
```

### Quote Discipline
**⚠️ IMPORTANT: Enclose the entire commit message in double quotes. Only use single quotes inside the message when you must quote a literal string or command. Skip unnecessary quoting.**

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
Use a short subject line followed by a `Summary:` block (two leading spaces) and bullet points. Maintain two leading spaces for indentation so the body renders correctly. Only quote strings with single quotes when they represent literal code, commands, or titles.

```bash
gac "type(scope): concise summary of change

  Summary:
  - Major accomplishment or change
  - Supporting detail or impacted files
  - Additional context, measurements, or follow-up actions

  Work tracking: YYYYMMDD-folder-ACTIVE"
```

### Real Example
```bash
gac "chore: bootstrap codex ssot migration

  Summary:
  - Imported template system, scanner suite, and work-tracking scaffold
  - Ported Serena/agents configuration into `.codex/`
  - Captured baseline scanner outputs for references, duplicates, migration
  - Documented enforcement plan for codex-task + diff-aware guard

  Work tracking: 20250920-codex-migration-ssot-ACTIVE"
```

## When User Asks for Commit Message

## Response Modes

Use these response modes consistently in commit-prep flows:
- `full-gac-command` — when the user explicitly asks for "the gac", return only the complete `gac "..."` command.
- `message-payload-only` — when the user asks for a commit message or validation only, return only the payload text without `gac`, code fences, or wrappers.
- `execute-gac` — when the user explicitly authorizes Codex to commit/push and confirms SSH/GPG auth is cached, run the canonical `gac "..."` command directly after workflow gates pass.

### Direct Execution
When operating in `execute-gac` mode:
- Run the same canonical `gac "..."` format described above.
- Run final verification before committing.
- Push the current task branch when requested or when the user has delegated the PR flow.
- Do not use `--no-verify`, disable signing, alter remotes, or bypass guard failures to compensate for expired auth.
- If SSH/GPG auth fails, ask the user to refresh the cache and retry the same command.

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

### When User Asks for the gac
**📋 Response mode: `full-gac-command`**
- Give ONLY the raw `gac "..."` command
- NO code blocks or formatting
- Keep the canonical multi-line `Summary:` block when the change is substantial

### Example Response
```
User: "Give me the gac"
AI: gac "feat: implement OAuth2 authentication

  Summary:
  - Add Google and GitHub providers
  - Wire the callback flow and account linking
  - Capture guard and tracker evidence for the auth rollout

  Work tracking: 20260422-auth-oauth-ACTIVE"
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

### Why This Quote Discipline
1. **Shell Safety**: Double quotes around the message keep the `gac` alias simple.
2. **Minimal Noise**: Only using single quotes when required keeps bullets readable.
3. **Escape Control**: Literal code/commands stay accurate without heavy escaping.
4. **Error Prevention**: Avoids accidental double-quote shell breakage while permitting precise quoting when needed.

### Benefits
- **Searchable History**: Type prefixes enable filtering
- **Clear Intent**: Type immediately shows purpose
- **Changelog Generation**: Tools can parse format
- **Team Understanding**: Standard format for all
- **CI/CD Integration**: Automated version bumping

## Progress Log

- **2026-04-22 18:32** — [S:20260422|W:task92-expand-workflow-guard-coverage|H:templates/conventions/git/commit-format.md|E:docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/designs/guard-coverage-audit.md] Added explicit `full-gac-command` vs `message-payload-only` response modes and documented the canonical multi-line `Summary:` block for Task 92 commit-prep guard coverage
