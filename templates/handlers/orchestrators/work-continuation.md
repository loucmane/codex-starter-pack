---
id: work-continuation
name: Work Continuation Orchestrator
title: Work Continuation Orchestrator
role: orchestrator
type: orchestrator
domain: workflow
stability: beta
status: beta
triggers:
  - continue
  - resume
  - "back to"
  - "keep working"
  - "where were we"
dependencies:
  - templates/behaviors/session/continuation-validation.md
  - templates/workflows/session/continuation.md
  - templates/workflows/session/state-management.md
version: 2.0.0
---
> **Codex Equivalent:** Continuation requires the active plan + tracker to be synced and documented before work resumes; TodoWrite tooling is replaced by Taskmaster tasks and the `codex-task` helper.

#### Pattern: work-continuation {#work-continuation}
- **Triggers**: continue, resume, "back to", "keep working", "where were we"
- **Preconditions**:
  - Active plan (`plans/current`) exists and plan-step-scope completed
  - Continuation validation behavior passes (plan/tracker sync + guard evidence)
  - Session + tracker have current S:W:H:E entries
- **Process**:
  1. Invoke [Session Continuation Validation](../../behaviors/session/continuation-validation.md)
  2. Load [Session Continuation Workflow](../../workflows/session/continuation.md)
  3. Restore state via [Session State Management Workflow](../../workflows/session/state-management.md)
  4. Confirm Taskmaster status (`task-master show <id>`) and set active subtask `in-progress`
  5. Resume implementation with guard monitoring enabled
- **Success**: Work resumes from the correct continuation point with documented evidence and passing guard
- **Failure**: Ask for missing context, create required documentation, or rerun guard until validation passes

**Examples**
- "Continue working on the timestamp guard" → Runs validation, syncs plan/tracker, and resumes Task 84/Task 85 work
- "Where were we yesterday?" → Loads continuation workflow, surfaces guard log, and prepares next subtask

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/work-continuation.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
