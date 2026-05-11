---
id: codex-foundation-user-guide
type: user-guide
status: stable
audience: all-users
skill-level: beginner
title: Codex Foundation User Guide
description: User-facing guide for working with the portable Codex foundation, Taskmaster workflow, sessions, work tracking, guard evidence, and Claude runtime adapter.
---

# Codex Foundation User Guide

This guide explains how to work in this repository now. The system is not just a prompt collection. It is a portable workflow foundation made of Taskmaster tasks, dated sessions, plans, work-tracking folders, guard checks, evidence files, and agent runtime contracts.

Use this guide when you want to start work, continue work, verify what changed, or understand what the agent should do next.

## Start Here

- Guide hub: [guides/index.md](guides/index.md)
- Quickstart: [guides/quickstart/getting-started.md](guides/quickstart/getting-started.md)
- Tool router: [TOOLS.md](TOOLS.md)
- Handler registry: [REGISTRY.md](REGISTRY.md)
- Conventions: [CONVENTIONS.md](CONVENTIONS.md)
- Portable foundation spec: [engine/core/portable-foundation-spec.md](engine/core/portable-foundation-spec.md)
- Foundation adoption guide: [engine/validation/foundation-adoption-guide.md](engine/validation/foundation-adoption-guide.md)
- Taskmaster alignment: [workflows/taskmaster/alignment.md](workflows/taskmaster/alignment.md)
- Work-tracking enforcement: [workflows/taskmaster/work-tracking-enforcement.md](workflows/taskmaster/work-tracking-enforcement.md)
- Claude runtime contract: [../.claude/engine/runtime-contract.md](../.claude/engine/runtime-contract.md)

## Mental Model

Every real development task should have matching state in five places:

| Layer | What it answers | Typical file or command |
| --- | --- | --- |
| Taskmaster | What task are we doing? | `task-master show <id>` |
| Git branch | Where should the changes live? | `feat/task-<id>-...` |
| Session log | What happened today? | `sessions/current` |
| Plan | What step are we on? | `plans/current` |
| Work tracking | What evidence and decisions exist? | `docs/ai/work-tracking/active/*-ACTIVE/` |

If any of these layers are missing during implementation work, the workflow is not ready. The right fix is to start or continue the session through the documented helper, not to manually create random files.

## Normal Daily Flow

### 1. Between Sessions

After a task is closed, the repository should usually have:

- no ACTIVE work-tracking folder
- no `sessions/current` symlink
- no `plans/current` symlink
- `sessions/state.json` with `"current": null`
- clean `main`

`python3 scripts/codex-task work-tracking audit` may report warnings in this state. Warnings about no ACTIVE folder and no `sessions/current` are expected between sessions.

### 2. Pick the Next Task

Use Taskmaster as the source of truth:

```bash
task-master next
task-master show <id>
```

Confirm dependencies are satisfied before starting. If filtered Taskmaster output shows dependency warnings, use the full graph health helper:

```bash
python3 scripts/codex-task taskmaster health
```

### 3. Start a Task

Create a task branch and run the kickoff helper:

```bash
git switch -c feat/task-<id>-short-slug
python3 scripts/codex-task wizard kickoff --task <id> --slug <short-slug> --title "<Task title>"
```

The wizard creates or updates:

- `sessions/current`
- `plans/current`
- `sessions/state.json`
- `plans/YYYY-MM-DD-task...md`
- `sessions/YYYY/MM/YYYY-MM-DD-...md`
- `docs/ai/work-tracking/active/YYYYMMDD-task...-ACTIVE/`
- the targeted Taskmaster generated task file

### 4. Continue an Active Task On A Later Day

Do not archive and recreate task work tracking just because a new day starts. Continue the existing active task:

```bash
python3 scripts/codex-task sessions continue --task <id> --slug <short-slug>
```

This creates a fresh daily session while preserving the task-scoped ACTIVE folder and plan.

### 5. Work In Small Evidence-Backed Slices

For each slice:

1. Read the current task, plan, and tracker.
2. Inspect the relevant code or docs.
3. Record findings and decisions in the ACTIVE folder.
4. Make the smallest scoped change.
5. Capture evidence under `reports/`.
6. Sync the plan and run guard checks.

Use the active work-tracking folder for decisions, findings, implementation notes, handoff notes, and evidence files.

## Git And GitHub

Direct Git execution is the default when the user has refreshed SSH/GPG auth and asks the agent to commit, push, create PRs, merge, or clean branches.

Use `gac` output only when the user explicitly asks for it or when auth is unavailable and the user needs to run the command manually.

Substantive task commits use a normal Git commit with a multi-line body:

```text
<type>(<scope>): <summary>

Summary:
- <what changed>
- <why it matters>
- <evidence captured>

Work tracking: <YYYYMMDD-task-slug-ACTIVE-or-COMPLETED>
```

Do not use `--no-verify` as a default workaround. If a bypass is explicitly authorized, document the reason in the active work-tracking decisions.

## Evidence And Verification

Common verification commands:

```bash
python3 scripts/codex-task plan sync
python3 scripts/codex-task work-tracking audit
python3 scripts/codex-guard validate --include-untracked
git diff --check
python3 -m pytest
```

When tests or Git commands need isolated unsigned Git behavior, use the established project pattern:

```bash
GIT_CONFIG_GLOBAL=/dev/null PYTHONDONTWRITEBYTECODE=1 python3 -m pytest
```

Capture meaningful outputs under the active work-tracking `reports/` directory when they are part of task acceptance.

## Claude Runtime Adapter

Claude can participate through its runtime adapter when `.claude/` is present. The important behavior is mechanical gating, not memory or promises.

The Claude runtime should:

- run readiness checks before mutation
- block hookable persistent mutations when workflow state is not READY
- block Codex-owned paths from Claude-side tasks
- allow read-only inspection in cold sessions
- rely on tests and evidence, not private memory, for claims

See [../.claude/engine/runtime-contract.md](../.claude/engine/runtime-contract.md) for the detailed contract.

## Common Requests

| User says | Expected workflow |
| --- | --- |
| "What's next?" | Inspect Taskmaster and summarize the next task. |
| "Let's start" | Confirm clean state, create branch, run kickoff. |
| "Continue" | Read current session/plan/tracker and resume the active task. |
| "It's a new day" | Close previous session if needed, then create a new daily session or continue the active task correctly. |
| "End the session" | Update session, tracker, handoff, memory, evidence, and clear current pointers only when appropriate. |
| "Give me the GAC" | Provide the requested command string only because it was explicitly requested. |
| "Push it" | Run Git directly after guard and diff checks pass, assuming auth cache is active. |
| "Prepare compaction" | Use `scripts/codex-task compaction checkpoint` and provide a complete resume message. |

## Troubleshooting

### The audit says there is no ACTIVE folder

If the repository is between sessions, this is expected. If you are in the middle of a task, run or repair the kickoff/continue workflow.

### The guard fails on session or tracker evidence

Update the active session and tracker with concrete S:W:H:E evidence. Avoid placeholder evidence such as `pending`.

### A task seems stale or too broad

Do a scope reconciliation first. Treat old Taskmaster wording as historical context until current repository evidence confirms the remaining gap.

### Git signing or SSH auth fails

Refresh the local SSH/GPG cache, then retry the same Git operation. Do not disable signing or bypass hooks unless explicitly authorized and documented.

### Claude tries to write memory instead of following workflow

That is not acceptable evidence. Workflow claims must be backed by files, hooks, tests, and reports in the repository. Private memory is continuity only.

## Progress Log

- **2026-05-11 16:02** — [S:20260511|W:task32-documentation-suite|H:templates/USER-GUIDE.md|E:docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/designs/documentation-suite-scope-reconciliation.md] Replaced the legacy Claude-only user guide with current Codex foundation workflow guidance.
