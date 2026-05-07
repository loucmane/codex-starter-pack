# Task 107 Direct Git Execution Scope

## Problem

Task 106 exposed a workflow regression: after the user had enabled SSH/GPG cache support and delegated Git work to Codex, Codex still returned a `gac "..."` command instead of using regular Git/GitHub commands directly. The template system contained conflicting guidance:

- `templates/conventions/git/commit-format.md` still said all commits must use `gac`.
- `templates/handlers/operators/git/create-commit-message.md` said `gac` is manually executed by the developer.
- `templates/TOOLS.md` and session lifecycle docs already allowed direct execution when SSH/GPG auth is cached.

The conflict made both behaviors look valid. Task 107 removes the ambiguity and adds guard coverage so stale GAC-default language fails validation.

## Policy

Commit-prep flows use four response modes:

- `direct-git-execution` — default when the user delegates checkpoint/commit/push/PR/merge work and auth is available.
- `full-gac-command` — only when the user explicitly asks for "the gac".
- `message-payload-only` — only when the user asks for a commit message or validation.
- `auth-refresh-required` — when regular Git/GitHub execution fails because SSH/GPG auth expired.

## Scope

Update:

- `templates/conventions/git/commit-format.md`
- `templates/behaviors/git/before-commit.md`
- `templates/handlers/operators/git/create-commit-message.md`
- `templates/TOOLS.md`
- `templates/tools/git/commands.md`
- `scripts/codex-guard`
- `tests/meta_workflow_guard/test_guard_rules.py`

Out of scope:

- Changing Git aliases in the user's shell.
- Removing historical references from archived work-tracking.
- Changing commit signing, remotes, or PR merge strategy.

## Initial Evidence

Targeted guard tests pass:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_guard_rules.py -k gac
9 passed, 54 deselected
```
