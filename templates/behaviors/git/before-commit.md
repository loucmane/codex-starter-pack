---
trigger: User mentions Git commit, asks for commit message, asks for gac, or delegates commit/push/PR work
title: Before Commit
action: Validate commit format and choose the correct Git execution mode
blocks: Cannot provide or execute a commit flow with wrong format, stale mode, or failed gates
category: git
type: behavior
enforcement: mandatory
status: stable
version: 1.1.0
---

# Before Commit

## Trigger Condition

This behavior fires whenever:
- User says "gac" or "give me gac"
- User asks for a commit message
- About to commit changes
- Creating commit message for user
- User mentions git commit
- User asks Codex to checkpoint, commit, push, create a PR, merge a PR, or clean up a branch
- User confirms SSH/GPG auth is cached and asks the agent to handle Git/GitHub operations directly

## Required Action

```text
CRITICAL CHECKLIST - MUST VERIFY ALL:
□ Has type prefix (feat/fix/docs/chore/style/refactor/test)
□ Subject line fits "type(scope): summary" format
□ Multi-line body (when present) uses the canonical `Summary:` block
□ Output mode matches the request (`direct-git-execution`, `full-gac-command`, `message-payload-only`, or `auth-refresh-required`)
□ Workflow gates pass before direct Git/GitHub execution
```

## Step-by-Step Process

1. **Verify Conventional Format**
   - Must start with type prefix.
   - Use colon and space after type.
   - Use lowercase description.

2. **Choose Output Mode**
   - `direct-git-execution`: if the user asks Codex to checkpoint, commit, push, create a PR, merge a PR, or otherwise delegates Git/GitHub execution, run regular Git/GitHub commands after workflow gates pass.
   - `full-gac-command`: if the user explicitly asks for "the gac", return only the raw `gac "..."` command.
   - `message-payload-only`: if the user asks for a commit message or validation only, return only the payload text.
   - `auth-refresh-required`: if regular Git/GitHub execution fails because SSH/GPG auth expired, ask the user to refresh auth and retry the same command path.

3. **Direct Git Execution**
   - If the user delegates Git/GitHub work, verify workflow gates first.
   - Run regular `git add`, `git commit`, `git push`, and related GitHub branch/PR commands directly.
   - Do not include `--no-verify`, disable signing, or alter remotes to work around auth failures.
   - If SSH/GPG cache has expired, stop and ask the user to refresh it, then retry the exact failed command.

## Blocking Gate

**CANNOT PROCEED** with commit flow until:
- Conventional commit format is verified.
- Correct output mode is confirmed (`direct-git-execution`, `full-gac-command`, `message-payload-only`, or `auth-refresh-required`).
- Direct execution has current plan/tracker/guard/test evidence where the task requires it.
- No bypass flags, signing-disable workarounds, remote changes, or hook skips are introduced to avoid expired auth.

## Satisfaction Criteria

- Has valid type prefix.
- Follows `type(scope): description` format.
- Output matches the requested mode.
- Direct Git/GitHub execution is the default for delegated commit/push/PR work.
- `gac` output appears only when explicitly requested by the user or selected as a manual fallback after auth failure.

## Example Workflows

### Wrong Approaches

```text
User: "checkpoint it"
AI: gac "chore: checkpoint work"
Problem: User delegated Git execution; Codex should run regular Git commands after gates pass.

User: "commit message"
AI: git commit -m "feat: add feature"
Problem: User asked for message payload only, not execution.

User: "give me gac"
AI: feat: add feature
Problem: User explicitly asked for the GAC command, not only the payload.
```

### Correct Approaches

```text
User: "checkpoint it"
AI: runs plan sync, audit, guard, diff-check, tests, then regular git add/commit/push when delegated.

User: "commit message"
AI: docs: update README with installation steps

User: "give me gac"
AI: gac "docs: update README with installation steps"
```

## Multi-line Commit Format

For substantive task commits, use:

```text
type(scope): concise summary of change

Summary:
- Primary outcome or change
- Supporting detail, evidence, or verification
- Follow-up action or context

Work tracking: YYYYMMDD-work-folder-ACTIVE
```

## Cross-References

- [Git Commit Format](../../conventions/git/commit-format.md)
- [TOOLS.md GitHub auth/signing support](../../TOOLS.md)
- [session/session-end.md](../session/session-end.md) - Session end commits

## Error Cases

- **Auth expired**: ask the user to refresh SSH/GPG cache and retry the same regular command path.
- **Complex message**: use the multi-line `Summary:` format.
- **Non-conventional type**: suggest the closest supported type.
- **Too long**: shorten the subject and move detail into the body.

## Why This Gate Exists

- Prevents stale GAC-default handoffs.
- Keeps Codex accountable for delegated Git/GitHub work.
- Ensures consistent commit history.
- Maintains conventional format.
- Enables automated changelog generation and commit parsing.

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/git/before-commit.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
- **2026-05-07 13:55** — [S:20260507|W:task107-direct-git-execution-mode|H:templates/behaviors/git/before-commit.md|E:docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/TRACKER.md] Reframed before-commit behavior around regular Git/GitHub execution by default and GAC output only on explicit request
