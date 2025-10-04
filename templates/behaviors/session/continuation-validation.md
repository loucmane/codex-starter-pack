---
id: session-continuation-validation
type: behavior
category: session
title: Session Continuation Validation
version: 0.1.0
status: draft
dependencies:
  - templates/workflows/session/continuation.md
  - templates/workflows/session/state-management.md
  - scripts/codex-guard
related:
  - templates/handlers/orchestrators/work-continuation.md
  - templates/conventions/work-tracking/tracker-format.md
  - templates/conventions/timestamps/usage-patterns.md
---

> Ensure the workspace is safe to resume before executing continuation workflows.

# Session Continuation Validation Behavior

## Purpose
Provide a mandatory preflight check before resuming an in-progress task. The behavior verifies documentation, plan/tracker alignment, and guard evidence so that continuation workflows cannot proceed with stale context.

## Preconditions
- Active plan exists (`plans/current`).
- Tracker reflects the current task (`docs/ai/work-tracking/active/...`).
- Most recent guard run was captured after the latest plan/tracker edits.

## Steps
1. **Confirm Continuation Intent**
   - Read `sessions/current` and ensure the log contains a continuation directive.
   - Validate S:W:H:E markers reference the expected task/subtask IDs.
2. **Validate Plan & Tracker Sync**
   - Run `python3 scripts/codex-task plan sync` if hashes are stale.
   - Confirm tracker progress log has an entry for the current session.
3. **Check Evidence Artifacts**
   - Ensure the last guard log is stored under `reports/session-continuation/`.
   - If Serena memories are enabled, verify the most recent memory ID is recorded in `MEMORY-REFS.md`.
4. **Run Guard Enforcement**
   - Execute `python3 scripts/codex-guard validate --include-untracked`.
   - Block continuation if guard reports failures.
5. **Log Validation**
   - Append S:W:H:E entry to session + tracker summarising the validation.
   - Reference guard log filename for traceability.

## Evidence Requirements
- Session log entry documenting validation command output.
- Tracker entry confirming plan sync + guard timestamp.
- Guard log stored under `reports/session-continuation/`.
- Serena memory reference when applicable (optional, but recommended).

## Failure Modes & Recovery
- **Plan mismatch** → Re-run plan sync, update tracker, repeat guard.
- **Missing guard evidence** → Execute guard and store the new log.
- **Serena memory missing** → Create memory or annotate findings explaining absence.
- **Git diff outside plan scope** → Update plan scope or revert unexpected changes.

## Completion Criteria
- Guard passes without violations.
- Plan/tracker hashes recorded in `.plan_state/sync.log`.
- Evidence artefacts captured in session/tracker and reports directory.
- Continuation workflow may proceed.
