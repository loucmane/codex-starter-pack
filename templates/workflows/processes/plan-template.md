---
id: plan-template
type: workflow-template
category: processes
title: Standard Plan Compliance Template
version: 1.0.0
status: draft
dependencies:
  - templates/behaviors/planning/plan-compliance.md
  - templates/engine/enforcement/behavioral-hooks.md
related:
  - templates/workflows/processes/meta-workflow-authoring.md
  - templates/workflows/session/lifecycle.md
---

# Standard Plan Compliance Template

Use this template for every non-trivial work effort. The plan file lives under `plans/` (e.g., `plans/2025-09-24-action-1-plan.md`) with the `plans/current` symlink pointing to the active plan.

## Header
- **Session ID (S)**: `YYYY-MM-DD-###`
- **Work Context (W)**: Matches work-tracking folder/task ID
- **Handler Target (H)**: Primary template/handler being executed
- **Task IDs**: Primary Taskmaster IDs covered by this plan (comma-separated)
- **Branch Policy**: `main-only` (work lands directly on main) or `feature-required` (enforce feature branch)
- **Evidence Summary (E)**: Commands/files that will prove completion
- **Plan Version**: Increment when amendments occur (v1, v2, ...)
- **Emergency Bypass**: `false` (set `true` only with approved waiver)

## Plan Table
| Step ID              | Description                                   | Evidence                             | Status    |
|----------------------|-----------------------------------------------|--------------------------------------|-----------|
| plan-step-scope      | Confirm scope with loucmane                   | Session log entry (timestamp + note) | pending   |
| plan-step-implement  | List concrete deliverables (files/tests/etc.) | File paths, commands, guard outputs  | pending   |
| plan-step-verify     | Tests/guard/doc updates + handoff             | Test results, guard log, docs updated| pending   |
| plan-step-emergency* | Emergency bypass rationale & follow-up        | Waiver note + post-mortem plan       | (optional)|

> `plan-step-emergency` only appears when an emergency bypass is invoked. Post-mortem documentation must be created within 24 hours.

## Scope
- (List affected files/components here)

## Branch Policy
- `feature-required` (default): work must happen on a feature branch that encodes one of the plan’s Task IDs, e.g. `feat/81-plan-guard`, `feat/task81-plan-guard`, or `feat/task-81-plan-guard`.
- `main-only`: allowed only when work needs to land directly on `main`; rationale must be noted in Continuation/Handoff and guard will enforce tracker documentation.
- Additional policies (e.g. `release/<id>`) can be defined explicitly; the guard treats any non `main-only` policy as requiring task-aligned feature branches.

## Amendments & Versioning


## Amendments & Versioning
- On scope change, archive current plan to `plans/archive/<name>-vN.md` and increment plan version.
- Record amendment details (what changed, why, approved by, timestamp) in an **Amendments** section below the table.

## Continuation & Handoff
- Populate **Continuation** block when work spans sessions:
  - Next owner
  - Required context reload steps
  - Outstanding risks/todos
- Reference this plan in Serena handoff memory and tracker entries.

## Conflict & Scope Declaration
- List files/components affected in a **Scope** section. Guard cross-checks git diff against this list.
- Document related plans to detect potential conflicts.

## Evidence Checklist
- Command outputs saved under `reports/` or attached to session log.
- Tests executed with logs linked in **Evidence** column.
- Guard validation results attached before marking `plan-step-verify` complete.
- Branch compliance verified (`git branch --show-current` matches Branch Policy and Task IDs).

## Emergency Bypass Protocol
- Set `plan-step-emergency` status to `in_progress` when bypass triggered.
- Log reason + approval in session & tracker.
- Create follow-up plan for remediation and post-mortem review.

## Completion
- When all steps verified, update tracker checklist and archive plan if no longer active.
- Remove `plans/current` symlink or point to the next active plan.
