---
id: domain-development-workflow
type: workflow-component
category: domain
title: Development Domain Workflow
dependencies:
  - templates/behaviors/planning/plan-compliance.md
  - scripts/codex-guard
related:
  - templates/handlers/orchestrators/work-activity.md
  - templates/workflows/processes/plan-template.md
version: 1.0.0
status: draft
---

# Development Domain Workflow

## Purpose
Provide a structured workflow for feature implementation or refactoring, ensuring plan compliance, guard validation, and evidence collection.

## Preconditions
- Plan-step-scope completed with acceptance criteria
- Development environment ready (dependencies installed)
- Relevant design docs reviewed

## Steps
1. **Plan Alignment**
   - Sync plan/tracker (`python3 scripts/codex-task plan sync`)
   - Review scope and guard expectations
2. **Implementation**
   - Make code changes following plan
   - Update tracker progress entries periodically
3. **Validation**
   - Run domain tests (unit/integration) – record outputs in `reports/development/`
   - Execute `python3 scripts/codex-guard validate --include-untracked`
4. **Documentation**
   - Update session log, tracker, findings/decisions as needed
   - Prepare follow-up tasks or TODOs
5. **Handoff/Closure**
   - Summarize work in session tracker and handoff
   - Ensure evidence bundle is ready

## Evidence Requirements
- Guard log (`reports/development/guard-<timestamp>.txt`)
- Test outputs, code review notes
- Tracker/session entries referencing implementation details

## Failure Modes & Recovery
- **Guard failure** → follow hints (plan sync, evidence logging)
- **Scope creep** → update plan or create new tasks
- **Unmerged dependencies** → coordinate with parallel work before closing

## Completion Criteria
- Guard validation passes with no hints
- Evidence bundle captured
- Plan-step-implement flagged complete
