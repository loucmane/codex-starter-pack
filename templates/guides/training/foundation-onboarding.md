---
id: foundation-onboarding-training
type: user-guide
status: stable
audience: maintainers
skill-level: beginner
title: Portable Foundation Onboarding Training
description: Hands-on training path for using the portable Codex foundation and Claude runtime adapter safely
dependencies:
  - templates/engine/core/portable-foundation-spec.md
  - templates/engine/validation/foundation-adoption-guide.md
  - templates/workflows/taskmaster/alignment.md
  - templates/workflows/taskmaster/work-tracking-enforcement.md
  - .claude/engine/runtime-contract.md
---

# Portable Foundation Onboarding Training

This guide trains a new maintainer or agent operator to use the current workflow as a system. The goal is not to memorize commands. The goal is to understand which state must exist before work starts, which evidence proves work happened correctly, and which guards prevent silent drift.

## Learning Path

1. Read the [portable foundation specification](../../engine/core/portable-foundation-spec.md) to understand the core contract.
2. Read the [foundation adoption guide](../../engine/validation/foundation-adoption-guide.md) to understand how the foundation applies across repositories.
3. Read [Taskmaster alignment](../../workflows/taskmaster/alignment.md) to understand task, branch, session, plan, and tracker alignment.
4. Read [work-tracking enforcement](../../workflows/taskmaster/work-tracking-enforcement.md) to understand ACTIVE and COMPLETED folder behavior.
5. Read the [Claude runtime contract](../../../.claude/engine/runtime-contract.md) if Claude will participate in the task.
6. Complete the exercises below inside a real Taskmaster task or a disposable training task.

## Evidence And Gates

Every training exercise should reinforce these invariants:

- A task starts from a clean `main` branch and a known current date.
- Work happens on a feature branch named for the Taskmaster task.
- `sessions/current`, `plans/current`, and `sessions/state.json` point to the active task session.
- Exactly one work-tracking folder is ACTIVE for the task.
- Plan and tracker checkboxes agree through `python3 scripts/codex-task plan sync`.
- Guard evidence is captured with `python3 scripts/codex-guard validate --include-untracked`.
- Work-tracking is archived only after the PR is merged.

## Hands-On Exercises

### Exercise 1: Readiness inspection

Practice the start-of-work inspection without mutating files:

```bash
date '+%Y-%m-%d %H:%M:%S %Z %z'
git status --short --branch
python3 scripts/codex-task taskmaster health
task-master next
```

Expected result:

- The date is current.
- The repository is clean or any dirty state is explained before work begins.
- Taskmaster health reports no invalid dependency references.
- The next task is known before branch or scaffold creation.

### Exercise 2: Guided kickoff

Start a real task through the guided workflow:

```bash
git switch -c feat/task-<id>-<slug>
python3 scripts/codex-task wizard kickoff --task <id> --slug <slug> --title "<task title>"
```

Expected result:

- A session file is created under `sessions/YYYY/MM/`.
- `sessions/current` points to the new session.
- `plans/current` points to the new plan.
- `sessions/state.json` names the current session.
- A work-tracking folder exists under `docs/ai/work-tracking/active/`.
- The Taskmaster task is `in-progress`.

### Exercise 3: Scope reconciliation

Before implementation, compare the Taskmaster wording to repository evidence:

```bash
task-master show <id>
rg -n "<task keywords>" templates docs scripts tests .claude .codex
```

Write the scope result under the active work-tracking folder, usually in `designs/`. Record findings and decisions when the historical task wording does not match the current repository.

Expected result:

- The plan describes the current implementation surface, not stale backlog wording.
- The tracker and session log include S:W:H:E entries for the scope decision.
- The implementation does not begin until the scope gate is clear.

### Exercise 4: Evidence capture

Run the normal evidence stack for a small change:

```bash
python3 scripts/codex-task plan sync
python3 scripts/codex-task work-tracking audit
python3 scripts/codex-guard validate --include-untracked
git diff --check
```

Expected result:

- Plan sync records the active plan/tracker state.
- Work-tracking audit has no unexpected active-folder issues.
- Guard passes.
- Diff check is empty.
- Evidence files are stored under the active task's `reports/` directory.

### Exercise 5: Merge and archive closeout

After the implementation PR is merged, archive the task:

```bash
python3 scripts/codex-task work-tracking archive --folder <YYYYMMDD-task-slug-ACTIVE>
python3 scripts/codex-task work-tracking audit
python3 scripts/codex-guard validate --include-untracked
git diff --check
```

Expected result:

- The work-tracking folder moves from `active/` to `archive/` with a `-COMPLETED` suffix.
- `sessions/current`, `plans/current`, and `sessions/state.json` return to between-session state.
- Post-archive audit warnings are limited to expected between-session warnings.
- The archive closeout is committed separately from the implementation PR.

## Completion Checklist

Training is complete when the trainee can do all of the following without bypassing the system:

- [ ] Explain why date confirmation happens before timestamped files are created.
- [ ] Explain why work-tracking folders are archived after merge, not recreated every day.
- [ ] Start a task with `python3 scripts/codex-task wizard kickoff`.
- [ ] Identify the active session, active plan, and ACTIVE work-tracking folder.
- [ ] Write a scope reconciliation note when task wording is stale.
- [ ] Capture plan sync, work-tracking audit, guard, and diff-check evidence.
- [ ] Mark only the relevant Taskmaster task/subtask done and refresh only its generated task file.
- [ ] Merge a PR only after checks are green.
- [ ] Archive the completed work-tracking folder after merge.
- [ ] Leave the repository in clean between-session state after closeout.

## Feedback Notes

Store feedback as repository evidence only when it belongs to an active task. Do not use private memory as training evidence. If a training gap is found, record it in the task's `FINDINGS.md` and either fix it inside the task scope or create a follow-up Taskmaster task.

## Progress Log

- **2026-05-08 16:49** — [S:20260508|W:task33-training-materials|H:templates/guides/training/foundation-onboarding.md|E:docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/designs/training-materials-scope-reconciliation.md] Added current portable foundation onboarding training with exercises and a completion checklist
