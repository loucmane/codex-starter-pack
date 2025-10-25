# Task 88 Alignment Scope Notes

## Objectives
- Ensure Taskmaster-related edits follow a documented alignment workflow before modifying task files.
- Capture guard requirements for timestamps, work-tracking scaffolding, and Taskmaster metadata edits.

## Deliverables
- New guard checks for session/tracker dates and work-tracking folder naming.
- CLI helpers for creating/archiving work-tracking scaffolding with correct timestamps.
- Updated documentation covering alignment prerequisites and usage instructions.

## Impacted Areas
- `scripts/codex-guard`
- `scripts/codex-task`
- `docs/ai/work-tracking/active/20251020-task88-taskmaster-alignment-ACTIVE/*`
- Taskmaster alignment plan and tracker.

## Out of Scope
- Downstream enforcement tasks (Tasks 89–97) consuming the alignment workflow.

## Incident 2025-10-22 – Premature Work-Tracking Archival
- **What happened**: While starting 2025-10-22 work I assumed each day required a fresh `*-ACTIVE` folder and archived `20251021-task88-taskmaster-alignment-ACTIVE` before confirming with the user.
- **Impact**: Briefly removed the active folder and risked data loss/confusion until the archive was restored to active.
- **Root cause**: Guard enforcement updated to flag stale prefixes but I didn’t differentiate between “existing tracked folder” and “new folder for today,” leading to a bad inference and no explicit confirmation.
- **Required follow-up**:
  1. ✅ Add automated guard/test coverage so deleting/archiving tracked active folders inside an open diff fails unless explicitly allowed.
  2. ✅ Update workflow documentation to state that active folders persist across days unless the task is finished.
  3. ✅ Implement guard CI hook and audit helper so confirmation & enforcement are automated.
