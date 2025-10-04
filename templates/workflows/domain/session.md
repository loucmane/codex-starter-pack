---
id: domain-session-workflow
type: workflow-component
category: domain
title: Session Domain Workflow
dependencies:
  - templates/behaviors/session/continuation-validation.md
  - scripts/codex-guard
related:
  - templates/workflows/session/lifecycle.md
  - templates/handlers/orchestrators/work-continuation.md
version: 1.0.0
status: draft
---

# Session Domain Workflow

## Purpose
Provide a repeatable flow for session management tasks: starting sessions, documenting progress, handling compaction/continuation, and closing sessions with evidence.

## Preconditions
- Active plan linked via `plans/current`
- Continuation validation completed if resuming work (`python3 scripts/codex-guard validate --include-untracked`)
- Tracker file available under `docs/ai/work-tracking/active/<session>/`

## Steps
1. **Initialize Session**
   - Run `python3 scripts/codex-task plan sync`
   - Log kickoff in session + tracker (`codex-task sessions update`)
2. **Capture Context**
   - Review previous session, tracker, Serena memories
   - Verify guard compliance (`python3 scripts/codex-guard validate --include-untracked`)
3. **Execute Work**
   - Follow domain-specific subtasks (development, testing, etc.)
   - Update tracker and session for significant progress
4. **Prepare Continuation / Closure**
   - If nearing compaction: invoke continuation validation behavior
   - Store guard logs under `reports/session-continuation/`
5. **Close Session**
   - Summarize results in session and tracker handoff
   - Record final guard run

## Evidence Requirements
- Session and tracker entries with S:W:H:E markers
- Guard log stored under `reports/session-continuation/`
- Serena memory (if enabled) updated at end of session

## Failure Modes & Recovery
- **Missing tracker** → run `codex-task work-tracking update` to create entries
- **Guard failure** → follow hints (plan sync, log storage, session entry) and rerun guard
- **Continuation skipped** → re-run continuation validation before resuming work

## Completion Criteria
- Guard validation passes without hints
- Session/tracker reflect closing status and next steps
- Handoff ready for next session
