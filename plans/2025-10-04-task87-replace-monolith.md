---
session_id: 2025-10-04-005
work_context: task87-replace-monolith
handler_target: templates/workflows/domain/
task_ids: [87]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/
  - reports/domain-workflows/*
plan_version: v1
emergency_bypass: false
---

# Plan – Task 87 Replace Legacy Monolithic References

## Header
- **Session ID (S)**: 2025-10-04-005
- **Work Context (W)**: task87-replace-monolith
- **Handler Target (H)**: templates/workflows/domain/
- **Task IDs**: 87
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/, reports/domain-workflows/*
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                        | Evidence                                                   | Status  |
|---------------------|--------------------------------------------------------------------|------------------------------------------------------------|---------|
| plan-step-scope     | Enumerate legacy references and map replacements                   | Session log + tracker entries + docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md | completed |
| plan-step-implement | Replace references, update guard & metadata, capture regression    | Updated templates, guard logs, pytest output               | pending |
| plan-step-verify    | Evidence bundle captured, guard/tests passing, docs updated        | docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/guard-2025-10-04-1909.txt; docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/tests-2025-10-04-1910.txt, archived logs                  | pending |
| plan-step-emergency | _Optional_ – only if bypass required                                | Waiver + post-mortem plan                                  | n/a     |

## Scope
- `templates/WORKFLOWS.md`, `templates/PATTERNS.md`, `templates/BUILDING-BETTER.md`
- `templates/workflows/domain/*`
- `templates/registry/*`, `templates/metadata/*`
- `scripts/codex-guard`
- `reports/domain-workflows/*`

## Branch Policy
- Working branch: `feat/task87-replace-monolith`

## Amendments & Versioning
- _None yet_

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Review archived Task 85 & active Task 86 folders.
  2. Run `python3 scripts/codex-task plan sync` before guard operations.
  3. Use helper prompts from `templates/helpers/domain/` for domain-specific documentation.
- Outstanding risks/todos: ensure guard blocks legacy references; update documentation accordingly.

## Conflict & Scope Declaration
- Related plans: Task 86 domain workflows.
- Guard cross-check: ensure `git diff --name-only` matches listed scope.

## Evidence Checklist
- Guard logs under `reports/domain-workflows/`
- Pytest outputs for domain regression tests
- Tracker/session entries summarizing replacements

## Emergency Bypass Protocol
- No bypass authorized.

## Completion
- Upon completing plan steps and capturing evidence, archive plan and work-tracking folder.
