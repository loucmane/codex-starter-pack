---
id: taskmaster-work-tracking-enforcement
type: workflow-component
category: taskmaster
title: Work-Tracking Enforcement Workflow
dependencies:
  - scripts/codex-task
  - scripts/codex-guard
  - templates/workflows/taskmaster/alignment.md
status: draft
---

# Work-Tracking Enforcement Workflow

## Purpose
Formalize the seven-file work-tracking process so every session captures tracker, findings, decisions, changelog, implementation, handoff, and reports updates while guard + helpers enforce compliance.

## Preconditions
- Taskmaster task set to `in-progress` (e.g. Task 89) with branch following policy (`feat/task89-work-tracking-enforcement`).
- Alignment workflow checklist satisfied (session + tracker logging already in place).
- Active folder scaffolded for the day (`python3 scripts/codex-task work-tracking scaffold --task <id> --slug <slug>`).

## Standard Workflow
1. **Scaffold (or reuse) seven-file structure**
   - Helper creates `TRACKER.md`, `FINDINGS.md`, `DECISIONS.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, `HANDOFF.md`, and `reports/<slug>/` with today’s placeholders.
   - If reusing, run `codex-task work-tracking update --preset tracker` to log a new session entry before editing.
2. **Log every operation via helpers**
   - Use presets: `codex-task work-tracking update --preset findings|decisions|changelog|implementation|handoff --handler auto` so guard has an S:W:H:E entry for each file.
   - Mirror the entry in the session log with `codex-task sessions update`.
3. **Enforce guard coverage**
   - `python3 scripts/codex-guard validate --include-untracked` before/after significant edits.
   - Guard now fails if tracker lacks today’s entry, findings/decisions/changelog are stale, or no Serena memory reference is present.
   - When dashboard/reporting automation changes, refresh repo-level metrics with `python3 scripts/template-metrics-dashboard` so CI and local evidence use the same output directory.
4. **Capture Serena memory each session**
   - `serena.write_memory` for the day → log via `codex-task sessions update --handler serena/memory` and tracker entry.
5. **Update documentation + implementation checklist**
   - Maintain `IMPLEMENTATION.md` to track guard/helper/documentation progress.
   - Record decisions and findings as enforcement behavior evolves.
   - Use `codex-task work-tracking update --preset handoff --handler auto` when preparing handoff notes.
6. **Regression proof**
   - Run guard unit tests (`python3 -m pytest tests/meta_workflow_guard/test_guard_rules.py`) and capture output under `reports/work-tracking-enforcement/`.
   - Include evidence paths in plan/table and tracker.
7. **Archive on completion**
   - Once guard + helper changes merge, run `codex-task work-tracking archive` to move the folder into `archive/`, set tracker status to `COMPLETED`, and append an archive entry to `HANDOFF.md`.
   - Guard ignores tracked-folder deletions only when the completed archive folder (with `TRACKER.md` set to `COMPLETED`) exists.
   - Ensure Taskmaster task transitions to `done` with guard/test evidence referenced.

## Guard Expectations
- `TRACKER.md` must include today’s entry and Serena memory reference.
- `FINDINGS.md`, `DECISIONS.md`, `CHANGELOG.md` require same-day log lines when edited.
- Multi-day Active folders must log a fresh tracker entry for each new day.
- Manual deletions of tracked ACTIVE folders fail unless archived via helper.

## Helper Shortcuts
- `codex-task bootstrap init --target-dir <repo>` → seed portable-foundation starter assets in a new or existing repo without overwriting existing config/policy files unless `--force` is explicit.
- `codex-task wizard kickoff --task <id>` → guided kickoff for a new task; creates the session, plan, active folder, current symlinks/state, and initial plan sync.
- `codex-task work-tracking scaffold --task <id> --slug <slug>` → creates full structure.
- `codex-task work-tracking update --preset findings --handler auto --evidence <path> --note "..."` → appends standardized entries.
- `codex-task work-tracking audit` → highlights stale active folders or missing `sessions/current` link.
- `python3 scripts/template-metrics-dashboard` → refreshes the repo-level metrics snapshot under `reports/template-metrics/`.

Bootstrap note:
- Bootstrap is the entrypoint for portable adoption; kickoff remains task-scoped. Use bootstrap first when a repository does not yet have `.codex/config.toml`, metadata policy, or workflow roots.
- Bootstrap is intentionally migration-safe: existing starter files are skipped by default, while kickoff/archive/update flows continue to enforce same-day evidence once a repo is active.

## Evidence Checklist
- Session log covering scaffold, guard runs, plan syncs, helper usage, tests.
- Tracker entries mirroring the same actions.
- Guard + pytest logs in `docs/.../reports/work-tracking-enforcement/`.
- Serena memory entry ID recorded in tracker/session.
- Taskmaster status updates referencing the enforcement work.

## Failure Modes & Recovery
- **Guard fails for stale doc entry** → add same-day entry via preset and rerun guard.
- **Serena memory missing** → capture memory immediately, log in tracker and session.
- **Multiple ACTIVE folders** → archive old folder, rerun guard.
- **Plan out of sync** → run `python3 scripts/codex-task plan sync` after every tracker edit.

## References
- `scripts/codex-task work-tracking scaffold`
- `scripts/codex-task work-tracking update --preset ...`
- `scripts/codex-guard`
- `templates/workflows/taskmaster/alignment.md`

## S:W:H:E Examples
- [S:20251027|W:task89-work-tracking|H:scripts/codex-task|E:cmd`python3 scripts/codex-task work-tracking scaffold --task 89 --slug work-tracking-enforcement`] Seven-file scaffold created
- [S:20251027|W:task89-work-tracking|H:scripts/codex-guard|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/reports/work-tracking-enforcement/guard-2025-10-27-pass.txt] Guard validation clean after documentation update
