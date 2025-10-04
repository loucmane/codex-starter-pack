---
session_id: 2025-10-04-004
work_context: task86-domain-workflows
handler_target: templates/workflows/domain/
task_ids: [86]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20251004-task86-domain-workflows-ACTIVE/
  - reports/domain-workflows/*
plan_version: v1
emergency_bypass: false
---

# Plan – Task 86 Domain Workflow Modules

## Header
- **Session ID (S)**: 2025-10-04-004
- **Work Context (W)**: task86-domain-workflows
- **Handler Target (H)**: templates/workflows/domain/
- **Task IDs**: 86
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20251004-task86-domain-workflows-ACTIVE/, reports/domain-workflows/*
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                        | Evidence                                                   | Status  |
|---------------------|--------------------------------------------------------------------|------------------------------------------------------------|---------|
| plan-step-scope     | Inventory domains, existing workflows, and gaps                    | Session log + tracker entries + designs/domain-inventory.md | in_progress |
| plan-step-implement | Author domain workflows, update registry, guards, helpers          | Updated templates, guard logs, helper docs, pytest output  | pending |
| plan-step-verify    | Evidence bundle captured, guard/tests passing, handoff documented  | reports/domain-workflows/*, updated docs, Serena memory    | pending |
| plan-step-emergency | _Optional_ – only if bypass required                                | Waiver + post-mortem plan                                  | n/a     |

## Scope
- `templates/workflows/domain/*`
- `templates/handlers/orchestrators/domain/*`
- `templates/metadata/domain-summary.*`
- `templates/registry/domain/*.md`
- `scripts/codex-guard` (domain enforcement rules)
- `docs/ai/work-tracking/active/20251004-task86-domain-workflows-ACTIVE/*`
- `tests/domain_workflows/*`
- `reports/domain-workflows/*`

## Branch Policy
- Current branch: `feat/task86-domain-workflows`
- Work must stay on this feature branch until completion.

## Amendments & Versioning
- _None yet_

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Activate Serena project `codex` and read newest task memories.
  2. Review work-tracking folder `20251004-task86-domain-workflows-ACTIVE/` (Tracker, Implementation, Designs).
  3. Run `python3 scripts/codex-guard validate --include-untracked` before committing.
- Outstanding risks/todos: domain inventory completeness, guard coverage, regression design.

## Conflict & Scope Declaration
- Related plans: 2025-10-01-task85-session-continuation (completed).
- Guard cross-check: ensure `git diff --name-only` remains within listed scope.

## Evidence Checklist
- Store guard logs under `reports/domain-workflows/guard-<timestamp>.txt`.
- Store pytest outputs under `reports/domain-workflows/tests-<timestamp>.txt`.
- Update tracker + session logs with S:W:H:E entries per guard policy.

## Emergency Bypass Protocol
- No bypass authorized; keep `plan-step-emergency` as `n/a` unless waiver granted.

## Completion
- When plan steps complete and evidence captured, mark tracker checklist items and archive plan if no longer active.
