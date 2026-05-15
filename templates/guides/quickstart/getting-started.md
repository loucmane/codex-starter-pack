---
id: getting-started
type: user-guide
status: stable
audience: new-users
skill-level: beginner
title: Getting Started With The Codex Foundation
description: Beginner guide for using the portable Codex foundation workflow with Taskmaster, sessions, plans, work tracking, guard evidence, and direct Git execution.
---

# Getting Started With The Codex Foundation

This repository uses a structured workflow so work can survive long sessions, compaction, multiple days, and multiple agents. The goal is simple: every real task should leave enough state and evidence for the next session to continue without guessing.

## The Five Things To Check

Before implementation starts, these should line up:

1. Taskmaster has the selected task.
2. The Git branch contains the task ID.
3. `sessions/current` points at today's session.
4. `plans/current` points at the active plan.
5. One ACTIVE work-tracking folder exists for the task.

If those are not true, the agent should start or repair the workflow before editing implementation files.

## Start From A Clean Repository

Useful inspection commands:

```bash
date '+%Y-%m-%d %H:%M:%S %Z %z'
git status --short --branch
task-master next
python3 scripts/codex-task work-tracking audit
```

Between sessions, it is normal for the audit to report no ACTIVE folder and no `sessions/current` symlink.

## Start A New Task

1. Inspect the task:

   ```bash
   task-master show <id>
   ```

2. Create the task branch:

   ```bash
   git switch -c feat/task-<id>-short-slug
   ```

3. Run kickoff:

   ```bash
   python3 scripts/codex-task wizard kickoff --task <id> --slug <short-slug> --title "<Task title>"
   ```

4. Confirm the active state:

   ```bash
   python3 scripts/codex-task work-tracking audit
   ```

## Continue A Task On A Later Day

If a task already has an ACTIVE folder, do not archive it just because the day changed. Continue it:

```bash
python3 scripts/codex-task sessions continue --task <id> --slug <short-slug>
```

That creates a fresh daily session while preserving the task's active work-tracking folder.

## During Work

Keep changes scoped:

- record discoveries in `FINDINGS.md`
- record choices in `DECISIONS.md`
- record implementation notes in `IMPLEMENTATION.md`
- keep progress and evidence in `TRACKER.md`
- keep the next-session summary in `HANDOFF.md`
- store command output under `reports/`

Use plan sync whenever plan/tracker status changes:

```bash
python3 scripts/codex-task plan sync
```

## Before Commit Or PR

Run the task's focused checks, then the workflow checks:

```bash
python3 scripts/codex-task plan sync
python3 scripts/codex-task work-tracking audit
python3 scripts/codex-guard validate --include-untracked
git diff --check
```

When full Python tests are in scope and local Git signing interferes with temp repos, use:

```bash
GIT_CONFIG_GLOBAL=/dev/null PYTHONDONTWRITEBYTECODE=1 python3 -m pytest
```

## Git Defaults

The agent should run regular Git commands directly after checks pass when SSH/GPG auth is cached and the user delegates Git work. A `gac` command is only for explicit user requests or manual auth fallback.

## What To Ask For

| If you want | Say |
| --- | --- |
| Start the next task | "What's next? Let's start it." |
| Continue current work | "Continue where we left off." |
| See current status | "Where are we in the task?" |
| End the day | "End today's session and prepare handoff." |
| Prepare for compaction | "Prepare compaction using the protocol." |
| Commit/push directly | "Run the commit and push after checks pass." |
| Get a manual commit command | "Give me the GAC." |

## More References

- Guide hub
- Full user guide
- Tool router: [../../TOOLS.md](../../TOOLS.md)
- Portable foundation spec: [../../engine/core/portable-foundation-spec.md](../../engine/core/portable-foundation-spec.md)
- Taskmaster alignment: [../../workflows/taskmaster/alignment.md](../../workflows/taskmaster/alignment.md)
- Work-tracking enforcement: [../../workflows/taskmaster/work-tracking-enforcement.md](../../workflows/taskmaster/work-tracking-enforcement.md)
- Claude runtime contract: [../../../.claude/engine/runtime-contract.md](../../../.claude/engine/runtime-contract.md)

## Progress Log

- **2026-04-21 17:59** — [S:20260421|W:task91-standardize-template-metadata|H:templates/guides/quickstart/getting-started.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `status` metadata during the Task 91 guide-standardization slice
- **2026-05-11 16:02** — [S:20260511|W:task32-documentation-suite|H:templates/guides/quickstart/getting-started.md|E:docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/designs/documentation-suite-scope-reconciliation.md] Replaced the older Claude-only quickstart with current Codex foundation startup, continuation, evidence, and direct Git guidance.
