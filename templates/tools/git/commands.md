---
id: git-commands
type: tool-guide
category: git
title: Git Commands and Operations Guide
version: 1.0.0
description: Version control operations and git workflow
status: stable
tools: [Bash]
---

# Git Commands and Operations Guide

## Overview

Git operations are executed through the Bash tool. This guide covers common git workflows, best practices, and the project's git conventions.

## Basic Git Operations

### Status and Information

```bash
# Check current status
Bash --command "git status"

# View recent commits
Bash --command "git log --oneline -10"

# Check current branch
Bash --command "git branch --show-current"

# See all branches
Bash --command "git branch -a"
```

### Staging and Committing

```bash
# Stage specific files
Bash --command "git add src/component.tsx"

# Stage all changes
Bash --command "git add -A"

# Commit with message
Bash --command "git commit -m 'feat: add user authentication'"

# Using gac alias (git add -A && commit)
Bash --command "gac 'fix: resolve login bug'"
```

## Commit Message Format

Follow conventional commits:

```yaml
Format: <type>: <description>

Types:
  feat: New feature
  fix: Bug fix
  docs: Documentation changes
  style: Code style changes
  refactor: Code refactoring
  test: Test additions/changes
  chore: Maintenance tasks
  perf: Performance improvements

Examples:
  "feat: add user authentication"
  "fix: resolve memory leak in parser"
  "docs: update API documentation"
  "refactor: simplify auth flow"
```

## Branch Management

### Creating Branches

```bash
# Create and checkout new branch
Bash --command "git checkout -b feat/new-feature"

# Create from specific branch
Bash --command "git checkout -b fix/bug-fix origin/main"

# Branch naming conventions
feat/feature-name    # New features
fix/bug-description  # Bug fixes
test/test-name       # Test branches
refactor/area        # Refactoring
```

### Switching Branches

```bash
# Switch to existing branch
Bash --command "git checkout main"

# Switch and update
Bash --command "git checkout main && git pull"

# Stash before switching
Bash --command "git stash && git checkout other-branch"
```

## Working with Remotes

### Authentication and Signing Cache

Before GitHub operations that depend on SSH or signed commits, treat auth state as workflow context instead of a side issue.

```bash
# Check SSH agent state when fetch/push auth looks stale
Bash --command "ssh-add -l"

# Check that a GPG agent is reachable before signed commits
Bash --command "gpg-connect-agent /bye"
```

- In this environment, SSH/GPG auth may be cached for 24 hours after the user refreshes it.
- If fetch, push, branch deletion, PR creation, or signed commit operations fail after the cache expires, ask the user to refresh the cache and rerun the exact failed operation.
- Do not disable commit signing, change remotes, use `--no-verify`, or bypass normal GitHub checks just to work around an expired auth cache.
- Log auth-cache refreshes or failures in the active session/work-tracking record when they affect delivery.

### Pushing Changes

```bash
# Push to current branch
Bash --command "git push"

# Push new branch
Bash --command "git push -u origin feat/new-feature"

# Force push (use carefully)
Bash --command "git push --force-with-lease"
```

### Pulling Updates

```bash
# Pull latest changes
Bash --command "git pull"

# Pull with rebase
Bash --command "git pull --rebase"

# Fetch without merging
Bash --command "git fetch"
```

## Advanced Operations

### Stashing

```bash
# Stash current changes
Bash --command "git stash"

# Stash with message
Bash --command "git stash push -m 'work in progress'"

# Apply latest stash
Bash --command "git stash pop"

# List stashes
Bash --command "git stash list"
```

### Merging and Rebasing

```bash
# Merge branch
Bash --command "git merge feat/feature-branch"

# Rebase on main
Bash --command "git rebase main"

# Interactive rebase
Bash --command "git rebase -i HEAD~3"

# Abort rebase
Bash --command "git rebase --abort"
```

### Viewing Differences

```bash
# Show unstaged changes
Bash --command "git diff"

# Show staged changes
Bash --command "git diff --staged"

# Compare branches
Bash --command "git diff main..feature-branch"

# Show file history
Bash --command "git log -p src/file.js"
```

## Git Workflows

### Feature Development

```bash
# 1. Create feature branch
Bash --command "git checkout -b feat/new-feature"

# 2. Make changes and commit
Bash --command "gac 'feat: implement feature foundation'"

# 3. Push branch
Bash --command "git push -u origin feat/new-feature"

# 4. Create pull request (via GitHub/GitLab)
```

### Bug Fixing

```bash
# 1. Create fix branch from main
Bash --command "git checkout main && git pull"
Bash --command "git checkout -b fix/critical-bug"

# 2. Fix and test
# ... make changes ...

# 3. Commit with clear message
Bash --command "gac 'fix: prevent null pointer in auth handler'"

# 4. Push for review
Bash --command "git push -u origin fix/critical-bug"
```

### Hotfix Process

```bash
# 1. Create from production
Bash --command "git checkout production && git pull"
Bash --command "git checkout -b hotfix/urgent-fix"

# 2. Apply fix
# ... fix issue ...

# 3. Commit and push
Bash --command "gac 'hotfix: patch security vulnerability'"
Bash --command "git push -u origin hotfix/urgent-fix"
```

## Project-Specific Aliases

```bash
# gac - Git add all and commit
Bash --command "gac 'message'"  # Equals: git add -A && git commit -m

# Other useful aliases (if configured)
Bash --command "git st"          # status
Bash --command "git co"          # checkout
Bash --command "git br"          # branch
Bash --command "git last"        # log -1 HEAD
```

## Handling Conflicts

### Merge Conflicts

```bash
# 1. Identify conflicts
Bash --command "git status"  # Shows conflicted files

# 2. Open and resolve conflicts
# Edit files to resolve <<<< ==== >>>> markers

# 3. Mark as resolved
Bash --command "git add resolved-file.js"

# 4. Continue merge
Bash --command "git commit"
```

### Rebase Conflicts

```bash
# During rebase, if conflicts occur:
# 1. Fix conflicts in files
# 2. Stage resolved files
Bash --command "git add ."

# 3. Continue rebase
Bash --command "git rebase --continue"

# Or abort if needed
Bash --command "git rebase --abort"
```

## Best Practices

### DO:
✓ Commit frequently with clear messages
✓ Pull before pushing
✓ Use branches for features
✓ Keep commits atomic and focused
✓ Test before committing

### DON'T:
❌ Commit sensitive data (keys, passwords)
❌ Force push to shared branches
❌ Commit broken code to main
❌ Mix unrelated changes in commits
❌ Ignore conflicts

## Safety Commands

```bash
# Undo last commit (keep changes)
Bash --command "git reset --soft HEAD~1"

# Discard local changes
Bash --command "git checkout -- file.js"

# Clean untracked files (careful!)
Bash --command "git clean -fd"

# Restore deleted file
Bash --command "git checkout HEAD -- deleted-file.js"
```

## Integration with Tools

### With Serena

```bash
# Before committing, analyze changes
mcp__serena__get_symbols_overview
# Then commit with informed message
Bash --command "gac 'refactor: improve auth service structure'"
```

### With sessions/

```bash
# Update session before commit
Edit sessions/  # Add progress note
Bash --command "gac 'feat: complete user auth [updates SESSION]'"
```

## Progress Log

- **2026-05-06 13:40** — [S:20260506|W:task9-git-hooks-infrastructure|H:templates/tools/git/commands.md|E:docs/ai/work-tracking/active/20260506-task9-git-hooks-infrastructure-ACTIVE/designs/task9-scope-reconciliation.md] Added SSH/GPG auth-cache checks and safety rules for GitHub fetch, push, branch cleanup, PR, and signed commit operations.

## Quick Reference

| Task | Command |
|------|---------||
| Quick commit | `gac "message"` |
| Check status | `git status` |
| View history | `git log --oneline -10` |
| Create branch | `git checkout -b name` |
| Switch branch | `git checkout name` |
| Pull updates | `git pull` |
| Push changes | `git push` |
| Stash work | `git stash` |
| Apply stash | `git stash pop` |
| View diff | `git diff` |
