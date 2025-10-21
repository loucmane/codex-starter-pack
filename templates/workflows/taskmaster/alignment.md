---
id: taskmaster-alignment-workflow
type: workflow-component
category: taskmaster
title: Taskmaster Alignment Workflow
dependencies:
  - scripts/codex-task
  - scripts/codex-guard
  - templates/handlers/orchestrators/session-start.md
status: draft
---

# Taskmaster Alignment Workflow

## Purpose
Establish a repeatable process for starting, maintaining, and closing Taskmaster-driven work-tracking sessions with enforced timestamps, guard coverage, and documented evidence.

## Preconditions
- Active Taskmaster task (e.g. Task 88) identified in the session plan.
- Branch created following Taskmaster branch policy (`feat/<task>-<slug>` unless otherwise noted).
- Plan (`plans/YYYY-MM-DD-*.md`) scoped and synced via `python3 scripts/codex-task plan sync`.
- Guard baseline passing or remediation notes logged before new work begins.

## Standard Workflow
1. **Run the scaffolding helper**
   - `python3 scripts/codex-task work-tracking scaffold --task <id> --slug <slug>`
   - Command derives today’s `YYYYMMDD` prefix, creates `TRACKER.md` and `CHANGELOG.md`, and refuses to scaffold when another `-ACTIVE` folder already exists (unless `--force`).
   - First tracker entry should be logged via `scripts/codex-task work-tracking update` (WORK = `task<int>-...`).
2. **Start the session properly**
   - Follow `session-start` template: run `date "+%Y-%m-%d %H:%M %Z"` and capture the output in the session log.
   - Ensure the session file lives under `sessions/YYYY/MM/` and the `sessions/current` symlink points at it.
3. **Record all guard / plan operations**
   - Each guard invocation (`python3 scripts/codex-guard validate --include-untracked`) and plan sync must be logged both in the session file and tracker via `scripts/codex-task`.
   - Run guard before significant edits and after major milestones (scaffold, docs, tests, pre-handoff).
4. **Document active work every day**
   - Append new entries to `TRACKER.md` with the current timestamp (`scripts/codex-task work-tracking update --note '...'`).
   - If the same folder stays active across days, add a fresh log entry for the new day before running guard; the guard checks the latest `**Last Updated**` stamp.
5. **Close or archive when finished**
   - `python3 scripts/codex-task work-tracking archive --folder <active-folder>` moves the folder to `docs/ai/work-tracking/archive/` and marks the tracker `COMPLETED`.
   - Guard should fail if another `-ACTIVE` folder remains for the same task after archival.
6. **Keep Taskmaster in sync**
   - Update Taskmaster status (`task-master set-status --id=<task> --status=in-progress|done`) after each milestone.
   - Mirror key notes inside Taskmaster via `task-master update-subtask` as evidence of progress.
7. **Run regression tests + guard before handoff**
   - Execute pytest suites touching guard/date logic.
   - Capture outputs under `reports/taskmaster-alignment/` and reference them in both session and tracker logs.
8. **Finalize documentation**
   - Summarise accomplishments, outstanding work, and next steps in the session “Session End Status” block.
   - Ensure plan `plan-step-implement` and `plan-step-verify` are updated, with evidence paths noted.

## Guard Expectations
- Active sessions **must** have `session_id` and `date` aligned, and today’s date recorded.
- Trackers must include `**Last Updated**: <today>` whenever they are modified.
- Editing any `docs/ai/work-tracking/active/` folder whose name isn’t stamped with today’s `YYYYMMDD` fails the guard unless the folder has been archived first.
- Editing a session file dated before today only passes if it is the latest prior session and already marked `SESSION COMPLETE`; older or in-progress sessions must remain untouched.
- Historical trackers/sessions remain valid provided they are archived or untouched; guard still expects their evidence to remain immutable.

## Multi-Day Active Work
- Reuse the same `YYYYMMDD-taskX-...-ACTIVE` folder across consecutive days, but add a fresh tracker entry with the new date before running guard.
- Archive only when the task completes or you need to free the namespace for another folder.

## Evidence Checklist
- Session log entries for: scaffold run, plan syncs, guard runs, pytest output, archival.
- Tracker log mirroring the same events.
- Reports under `reports/taskmaster-alignment/` for guard + pytest runs.
- Taskmaster status updates referencing the same session ID and evidence.

## Failure Modes & Recovery
- **Guard fails due to stale dates** → Run `plan sync`, confirm session date, add missing tracker entry, rerun guard.
- **Multiple `-ACTIVE` folders** → Archive the old folder using the helper, rerun guard.
- **Missing evidence** → Use `scripts/codex-task` helpers to append retroactive log entries (with clear notes) before re-running guard.

## References
- `scripts/codex-task work-tracking scaffold`
- `scripts/codex-task work-tracking archive`
- `scripts/codex-guard`
- Taskmaster CLI (`task-master ...`)

## S:W:H:E Examples
- [S:20251021|W:task88-taskmaster-alignment|H:scripts/codex-task|E:docs/ai/work-tracking/active/20251021-task88-taskmaster-alignment-ACTIVE/TRACKER.md] Scaffold new active folder before edits
- [S:20251021|W:task88-taskmaster-alignment|H:scripts/codex-guard|E:reports/taskmaster-alignment/guard-2025-10-21-pass.txt] Guard run after workflow updates
