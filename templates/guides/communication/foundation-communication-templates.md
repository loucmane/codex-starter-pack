---
id: foundation-communication-templates
type: user-guide
status: stable
audience: maintainers
skill-level: intermediate
title: Foundation Communication Templates
description: Repository-native communication templates for Taskmaster, PR, release, incident, and feedback updates in the portable foundation workflow
dependencies:
  - templates/engine/core/portable-foundation-spec.md
  - templates/workflows/taskmaster/alignment.md
  - templates/workflows/session/lifecycle.md
  - templates/conventions/git/commit-format.md
  - .claude/engine/runtime-contract.md
---

# Foundation Communication Templates

Use these templates when communicating task status, PR readiness, breaking changes, incidents, milestones, or follow-up feedback for the portable foundation. These are repository-native payloads: they should point to Taskmaster, session, plan, work-tracking, guard, test, Git, and GitHub evidence. They are not email distribution-list automation.

## Communication Rules

- Ground every update in the active Taskmaster task and work-tracking folder.
- Reference the relevant session, plan, tracker, and report paths instead of relying on memory.
- Include `S:W:H:E` evidence when summarizing workflow or implementation progress.
- Use `direct-git-execution` as the default Git/GitHub mode when auth is available.
- Mention `gac` only when the user explicitly asks for "the gac" or chooses an auth-fallback path.
- Do not claim tests, guard, PR checks, merge state, or archive state unless the evidence exists.

## Pull Request Description

Use this for PR bodies or PR-ready handoff notes.

```markdown
## Summary
- Taskmaster Task: <id> - <title>
- Branch: <branch>
- Work tracking: <YYYYMMDD-task-slug-ACTIVE>
- Session: <sessions/YYYY/MM/YYYY-MM-DD-NNN-task.md>

## What Changed
- <Concrete change 1 with file path>
- <Concrete change 2 with file path>
- <Concrete change 3 with file path>

## Scope Decision
- <Brief current-state scope decision>
- Evidence: <design/scope-reconciliation path>

## Verification
- [ ] `python3 -m pytest <focused test paths>`
- [ ] `python3 scripts/codex-task plan sync`
- [ ] `python3 scripts/codex-task work-tracking audit`
- [ ] `python3 scripts/codex-guard validate --include-untracked`
- [ ] `git diff --check`

## Risks And Follow-Ups
- <Known risk or "None identified">
- <Follow-up Taskmaster task or "None">
```

## Task Completion Update

Use this when a task or subtask is complete and evidence has been captured.

```markdown
Taskmaster Task <id> is complete.

Completed:
- <Implementation outcome>
- <Documentation or workflow update>
- <Taskmaster status update>

Evidence:
- Session: <session path>
- Plan: <plan path>
- Work tracking: <active or completed folder>
- Tests: <reports/.../tests-*.txt>
- Guard: <reports/.../guard-*.txt>
- Taskmaster health: <reports/.../taskmaster-health-*.txt>

GitHub:
- PR: <number or URL>
- Checks: <green/pending/failing with evidence>
- Merge state: <not merged / merged on YYYY-MM-DD HH:MM TZ>
```

## Breaking Change Notice

Use this when a template, script, runtime gate, or workflow behavior changes what future sessions must do.

```markdown
## Breaking Change: <short title>

Affected Surface:
- <path or workflow>

What Changed:
- <old behavior>
- <new behavior>

Required Action:
- <what maintainers or agents must do now>

Compatibility:
- <migration path, fallback, or explicit no-fallback note>

Evidence:
- Taskmaster Task: <id>
- Decision: <DECISIONS.md entry/path>
- Tests: <reports/.../tests-*.txt>
- Guard: <reports/.../guard-*.txt>
```

## Incident Or Regression Notice

Use this when the system behaved incorrectly, a gate failed unexpectedly, or a workflow invariant was violated.

```markdown
## Incident: <short title>

Detected:
- Time: <YYYY-MM-DD HH:MM TZ from date command>
- Reporter: <person/agent>
- Surface: <file, command, hook, CI check, PR, or workflow>

Impact:
- <what became unsafe, unclear, blocked, or misleading>

Root Cause:
- <known cause or "under investigation">

Immediate Containment:
- <what was stopped, reverted, blocked, or documented>

Remediation:
- <fix or follow-up Taskmaster task>

Evidence:
- S:W:H:E: [S:<session>|W:<work>|H:<handler>|E:<evidence>]
- Session: <session path>
- Findings: <FINDINGS.md path>
- Decisions: <DECISIONS.md path>
- Verification: <reports path>
```

## Milestone Announcement

Use this when a foundation capability becomes available after merge and archive closeout.

```markdown
## Milestone: <capability name>

Delivered In:
- Taskmaster Task: <id>
- PR: <URL or number>
- Archive: <docs/ai/work-tracking/archive/...-COMPLETED>

Capability:
- <what is now possible>

How To Use:
- <command, guide path, or workflow entry point>

Evidence:
- Tests: <reports/.../tests-*.txt>
- Guard: <reports/.../guard-*.txt>
- Work-tracking audit: <reports/.../work-tracking-audit-*.txt>
- Taskmaster health: <reports/.../taskmaster-health-*.txt>
```

## Feedback And Follow-Up Capture

Use this for user feedback, review findings, or deferred improvements discovered during a task.

```markdown
## Feedback / Follow-Up

Source:
- <user, review thread, CI failure, smoke test, or session observation>

Observation:
- <specific behavior or gap>

Decision:
- <fix now / defer / no action>

Follow-Up:
- Taskmaster Task: <existing id or "create new task">
- Owner: <person/agent>
- Evidence: <FINDINGS.md, DECISIONS.md, HANDOFF.md, or report path>
```

## Evidence Checklist

Before sending a final task update, PR description, or milestone announcement, verify the payload has the relevant evidence:

- [ ] Taskmaster Task ID and status are accurate.
- [ ] Session and plan paths are current.
- [ ] Work-tracking folder is ACTIVE before merge and COMPLETED only after archive closeout.
- [ ] `python3 scripts/codex-task plan sync` has been run after plan/tracker edits.
- [ ] `python3 scripts/codex-task work-tracking audit` has been captured when relevant.
- [ ] `python3 scripts/codex-task taskmaster health` has been captured for Taskmaster state claims.
- [ ] `python3 scripts/codex-guard validate --include-untracked` has passed before claiming guard health.
- [ ] `git diff --check` has passed before claiming diff cleanliness.
- [ ] PR/check/merge state is confirmed from GitHub when mentioned.
- [ ] Any `gac` wording is present only because the user explicitly requested it.

## Progress Log

- **2026-05-08 17:25** — [S:20260508|W:task49-communication-templates|H:templates/guides/communication/foundation-communication-templates.md|E:docs/ai/work-tracking/active/20260508-task49-communication-templates-ACTIVE/designs/communication-templates-scope-reconciliation.md] Added repo-native communication templates for PRs, task completion, breaking changes, incidents, milestones, and feedback capture
