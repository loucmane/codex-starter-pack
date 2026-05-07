---
id: git-commit-format
type: convention
category: git
title: Git Commit Format
applies_to: code
enforcement: required
dependencies:
  - branch-naming
version: 1.1.0
status: stable
---

# Git Commit Format

## Convention

Use regular Git/GitHub commands as the Codex execution default:

```bash
git add -A
git commit -m "type(scope): concise summary" -m "Summary:
- Concrete change
- Evidence or verification

Work tracking: YYYYMMDD-folder-ACTIVE"
git push -u origin <branch>
```

The `gac` alias remains a user convenience only. Codex should not default to `gac`, should not hand back a `gac "..."` command after delegated Git work, and should not claim that the developer manually runs commits as the normal path. Use `gac` output only when the user explicitly asks for "the gac" or when an SSH/GPG auth failure requires manual fallback and the user chooses that path.

## Commit Message Format

### Structure

```text
type(scope): description

Summary:
- concrete change
- evidence or verification

Work tracking: YYYYMMDD-folder-ACTIVE
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting, missing semicolons, etc.
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding missing tests
- **chore**: Build process, workflow, generated files, or auxiliary tools

### Scope

- Component name: `feat(Button): add loading state`
- Module name: `fix(auth): correct token refresh`
- File type: `docs(README): update installation`
- Workflow area: `chore(workflow): archive task work tracking`

## Response Modes

Use these response modes consistently in commit-prep and commit execution flows:

- `direct-git-execution` — default when the user asks Codex to checkpoint, commit, push, create a PR, merge a PR, or otherwise delegates Git/GitHub work and auth is available.
- `full-gac-command` — only when the user explicitly asks for "the gac"; return only the complete `gac "..."` command.
- `message-payload-only` — when the user asks for a commit message or validation only; return only the payload text without `git commit`, `gac`, code fences, or wrappers.
- `auth-refresh-required` — when regular Git/GitHub execution fails because SSH/GPG auth expired; ask the user to refresh auth and retry the same regular Git command path.

## Direct Git Execution

When operating in `direct-git-execution` mode:

- Run final workflow gates before staging: plan sync, work-tracking audit, guard, diff-check, and relevant tests.
- Inspect `git status --short --branch` before staging.
- Stage intentionally with `git add -A` or narrower pathspecs when scope requires it.
- Commit with regular `git commit -m ... -m ...` using the canonical message format above.
- Push the current task branch when requested or when the user has delegated PR flow.
- Create, check, merge, and clean up PRs with normal GitHub commands when delegated and auth is available.
- Do not use `--no-verify`, disable signing, alter remotes, or bypass guard failures to compensate for expired auth.
- If SSH/GPG auth fails, ask the user to refresh the cache and retry the same regular Git/GitHub operation.

## Message Examples

### Simple Commit

```text
feat(auth): add OAuth2 callback validation
```

### Substantive Task Commit

```text
test(claude): smoke test runtime adapter in harness

Summary:
- Add real Claude harness evidence for cold-session blocking and READY-state behavior
- Verify protected Codex-owned path blocking through Edit and Bash diagnostics
- Record plan sync, audit, guard, diff-check, Taskmaster, Serena, and test evidence

Work tracking: 20260507-task106-claude-runtime-smoke-test-ACTIVE
```

### Explicit GAC Request Only

When the user explicitly asks "give me the gac", return only the raw `gac "..."` command. Keep the canonical `Summary:` block when the change is substantial.

```bash
gac "test(claude): smoke test runtime adapter in harness

  Summary:
  - Add real Claude harness evidence for cold-session blocking and READY-state behavior
  - Verify protected Codex-owned path blocking through Edit and Bash diagnostics
  - Record plan sync, audit, guard, diff-check, Taskmaster, Serena, and test evidence

  Work tracking: 20260507-task106-claude-runtime-smoke-test-ACTIVE"
```

## Wrong Patterns

```text
added stuff
Feature: new button
feat:no space after colon
FEAT: uppercase type
```

Wrong workflow defaults:

- Saying "all commits must use `gac`."
- Saying the developer manually executes the alias as the normal path.
- Handing the user a `gac "..."` command after they asked Codex to checkpoint, commit, push, or create a PR.
- Using `git add . && git commit -m ...` as an example that skips final workflow gates.

## Best Practices

### Subject Line

- **Length**: 50 characters or less when practical
- **Tense**: Present tense imperative ("add", not "added")
- **Case**: Lowercase after type
- **Period**: No period at end

### Body

- **When**: Use for substantive task commits or workflow changes
- **Length**: Keep bullets concise; wrap manually when needed
- **Content**: Explain what changed and what evidence proves it
- **Format**: Use `Summary:` followed by `- ` bullets and a `Work tracking:` line for tracked task commits

### Footer

- **Breaking changes**: `BREAKING CHANGE: description`
- **Issue references**: `Closes #123`, `Fixes #456`
- **Co-authors**: `Co-authored-by: Name <email>`

## Rationale

### Why Direct Git Execution

1. **Standard Tooling**: Regular Git/GitHub commands work in every shell and CI environment.
2. **Agent Accountability**: When Codex is delegated Git work, Codex performs the action instead of shifting execution back to the user.
3. **Clear Fallbacks**: Auth expiry becomes an `auth-refresh-required` state, not a reason to disable signing, skip hooks, or fall back to stale alias guidance.
4. **GitHub Alignment**: PR creation, checks, merge, and branch cleanup stay in the same normal GitHub workflow.

### Why Keep GAC As Explicit-Only

1. **User Convenience**: Some users still prefer the alias when they explicitly ask for it.
2. **Legacy Compatibility**: Existing docs and historical commits remain understandable.
3. **Reduced Ambiguity**: The alias is no longer a default execution path, so Codex should not emit it unless asked.

## Progress Log

- **2026-04-22 18:32** — [S:20260422|W:task92-expand-workflow-guard-coverage|H:templates/conventions/git/commit-format.md|E:docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/designs/guard-coverage-audit.md] Added explicit `full-gac-command` vs `message-payload-only` response modes and documented the canonical multi-line `Summary:` block for Task 92 commit-prep guard coverage
- **2026-05-07 13:55** — [S:20260507|W:task107-direct-git-execution-mode|H:templates/conventions/git/commit-format.md|E:docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/TRACKER.md] Reframed commit guidance around regular Git/GitHub execution by default and reserved `gac` output for explicit user requests or auth fallback
