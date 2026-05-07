# Task 19 Rollback Scope Reconciliation

## Context
Task 19 was created from an older migration-safety backlog item. Its original scope mentions git checkpoint tags, state restoration, Taskmaster snapshots, Serena backups, compatibility-map versioning, a rollback decision matrix, an emergency legacy-mode toggle, and rollback tests.

The current foundation has since gained several targeted safety systems:

- Task 10 shipped `scripts/template-ssot-scanner/apply_reference_fixes.py`, including dry-run-by-default behavior, explicit `--apply`, backups, JSON logging, symlink protection, and git-backed rollback for reference-fix mutations.
- Task 84 shipped timestamp guard behavior and regression coverage for session/work-tracking date integrity.
- Task 97 shipped template metrics visibility.
- Later workflow tasks added direct Git execution, pre-commit guard enforcement, targeted Taskmaster generation, guided kickoff, active/archive work-tracking, and Taskmaster full-graph health helpers.

## Current-State Gap
The remaining useful gap is not another reference-fix rollback path. That already exists in Task 10.

The current gap is a portable checkpoint manifest for risky workflow operations:

- capture current branch and HEAD
- capture dirty Git status
- capture current session, current plan, active work-tracking folder, and session state
- capture Taskmaster graph hash and health summary
- capture Serena memory inventory
- optionally create an explicit git tag at HEAD
- render a non-destructive recovery plan from the manifest

## Out Of Scope
- Running destructive rollback commands automatically.
- Using `git reset --hard`.
- Deleting untracked files automatically.
- Reintroducing a project-specific legacy mode toggle.
- Copying or rewriting Serena memories as a backup mechanism.
- Replacing Task 10's reference-fix rollback.

## Selected Implementation
Add `python3 scripts/codex-task rollback` with two subcommands:

- `rollback checkpoint` writes a JSON checkpoint manifest and can optionally create an annotated git tag.
- `rollback plan` reads a checkpoint manifest and writes or prints safe recovery guidance without executing rollback commands.

This keeps rollback portable, auditable, and compatible with the existing helper surface. The implementation belongs in `scripts/codex-task` because the checkpoint spans Taskmaster, sessions, plans, work-tracking, Serena, and Git.

## Acceptance
- Parser exposes `rollback checkpoint` and `rollback plan`.
- Checkpoint manifest includes Git, workflow, Taskmaster, and Serena state.
- Recovery plan is explicitly non-destructive and does not execute restore/reset/clean commands.
- Tests cover parser wiring, manifest generation, and plan rendering.
- Evidence is stored under `reports/rollback-mechanism/`.
