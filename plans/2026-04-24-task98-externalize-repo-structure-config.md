---
session_id: 2026-04-24-005
work_context: task98-externalize-repo-structure-config
handler_target: scripts/codex-guard
task_ids: [98]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/
  - scripts/codex-guard
  - .taskmaster/tasks/task_098.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 98 Externalize Repo Structure Configuration

## Header
- **Session ID (S)**: 2026-04-24-005
- **Work Context (W)**: task98-externalize-repo-structure-config
- **Handler Target (H)**: scripts/codex-guard
- **Task IDs**: 98
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/, scripts/codex-guard, .taskmaster/tasks/task_098.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Inventory hardcoded repo-layout assumptions and define the repo-local configuration contract | docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/designs/repo-structure-config-contract.md | completed |
| plan-step-implement | Add repo-structure config loading and update workflow scripts to derive operational roots from it | .codex/config.toml; scripts/_repo_structure.py; scripts/codex-guard; scripts/codex-task; scripts/template-metrics-dashboard | completed |
| plan-step-verify | Store regression evidence, refresh handoff docs, and confirm Taskmaster status for Task 98 | docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/reports/repo-structure-config/; docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/`
- `.codex/config.toml`
- `scripts/_repo_structure.py`
- `scripts/codex-guard`
- `scripts/codex-task`
- `scripts/template-metrics-dashboard`
- `.taskmaster/tasks/task_098.txt`
- `tests/`
- Taskmaster Task `98`

## Branch Policy
- Working branch: `feat/task-98-externalize-repo-structure-config`

## Amendments & Versioning
- 2026-04-24 - Task 98 kickoff created via the guided wizard flow.
- 2026-04-24 - Replaced the generic wizard scope with the repo-structure configuration contract and initial implementation inventory.
- 2026-04-24 - Completed the scope and implementation phases after landing the shared loader, config contract, and supporting docs.
- 2026-04-24 - Completed verification after passing the regression suite and guard, then marking Taskmaster Task 98 done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 98 and its implementation details.
  3. Review the repo-structure config contract before broad path refactors.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the config contract small and root-based so later portability tasks can build on it without another migration.

## Conflict & Scope Declaration
- Related plans: Task 97 metrics dashboard, plus the portability chain in Tasks 99-102.
- Guard cross-check: repo-structure configuration must preserve the current default layout while allowing alternate roots through repo-local config.

## Evidence Checklist
- Repo-structure config contract under `designs/`
- Tracker/session entries for scope inventory and config refactor progress
- Stored tests and guard evidence under `reports/repo-structure-config/`

## Emergency Bypass Protocol
- No bypass authorized.
