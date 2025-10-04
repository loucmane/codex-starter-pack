---
id: session-state-management
type: workflow-component
category: session
title: Session State Management Workflow
dependencies:
  - templates/patterns/session/state-patterns.md
  - templates/conventions/work-tracking/*.md
  - templates/handlers/operators/session/save-context.md
related:
  - templates/workflows/session/lifecycle.md
  - templates/workflows/session/continuation.md
version: 1.0.0
status: stable
---
> **Codex Equivalent:** Use the plan file + Taskmaster tasks to mirror TodoWrite/TodoRead responsibilities; maintain plan/tracker sync via `python3 scripts/codex-task plan sync` before checkpoints.


# Session State Management Workflow

## Purpose
Provide a repeatable process for capturing, persisting, and restoring session/work state across development phases.

## Core State Artifacts
- `sessions/YYYY/MM/session-id.md`
- Work-tracking active folder (tracker, implementation, findings, decisions, changelog, handoff, reports)
- Taskmaster task list (Taskmaster CLI or plan)
- Serena memories (if enabled)
- Git branch + pending diff

## Workflow Steps
1. **State Capture (during work)**
   - Update Taskmaster status whenever changing subtasks (`task-master set-status ...`)
   - Log progress in session + tracker at meaningful milestones
   - Record findings/decisions immediately when discovered
   - Store evidence outputs under `reports/` or `code/`
2. **Checkpoint Creation**
   - Run `python3 scripts/codex-task sessions update --checkpoint`
   - Execute relevant scanners/tests and attach evidence
   - Record `python3 scripts/codex-task plan sync` so continuation guard recognizes checkpoint
   - Commit or stash diff if checkpoint requires clean state
3. **State Persistence**
   - Ensure session log, tracker, and handoff reflect the checkpoint
   - Write Serena memory describing work, state, next steps
   - Archive outdated notes into `archive/` if superseded
4. **State Restoration**
   - Use continuation workflow (with validation behavior) to load checkpoint
   - Verify Taskmaster statuses, tracker, Serena memory align
   - Re-run quick validation (tests/scans) if state diverged
   - Store guard log under `reports/session-continuation/`
5. **Audit & Reconciliation**
   - Compare Git diff to documented changes; resolve discrepancies
   - Update metadata (status fields, inventory, guard rules)
   - Log outcomes in Findings/Changelog

## Evidence Requirements
- Session entries showing state capture/restore
- Tracker entries with S:W:H:E anchors
- Serena memory IDs for checkpoints
- Git status clean or documented justification for WIP

## Tooling Integration
- `python3 scripts/codex-task` subcommands (`sessions update`, `work-tracking update`, `plan sync`, `scanner run`)
- `python3 scripts/codex-guard validate --include-untracked` to enforce documentation
- Serena MCP memory operations
- Taskmaster tasks linked by ID for automation

## Failure Modes & Mitigations
- **Incomplete documentation** → behavior `update-tracker` blocks continuation
- **State drift** → rerun checkpoints, reconcile diff, update logs
- **Missing Serena memory** → reconstruct from session/tracker, log as incident
- **Taskmaster desync** → audit tasks vs. tracker, realign statuses

## Completion Criteria
- All state artifacts synchronized post-work
- Next session can resume using continuation workflow without manual guesswork
- No guard violations when running `codex-guard validate`
