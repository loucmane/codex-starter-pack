---
session_id: 2026-04-24-007
work_context: task100-foundation-bootstrap-layer
handler_target: templates/engine/core/portable-foundation-spec.md
task_ids: [100]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/
  - templates/engine/core/portable-foundation-spec.md
  - .taskmaster/tasks/task_100.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 100 Build Foundation Bootstrap Layer

## Header
- **Session ID (S)**: 2026-04-24-007
- **Work Context (W)**: task100-foundation-bootstrap-layer
- **Handler Target (H)**: templates/engine/core/portable-foundation-spec.md
- **Task IDs**: 100
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/, templates/engine/core/portable-foundation-spec.md, .taskmaster/tasks/task_100.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the bootstrap-layer contract, starter asset set, and migration-safe rollout boundary for portable foundation adoption | docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/designs/foundation-bootstrap-layer-outline.md | completed |
| plan-step-implement | Implement bootstrap commands, starter assets, and adoption documentation that rely on the portable spec and repo-structure config | scripts/codex-task; docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task100-foundation-bootstrap-layer-ACTIVE/`
- `templates/engine/core/portable-foundation-spec.md`
- `docs/ai/work-tracking/archive/20260424-task98-externalize-repo-structure-config-COMPLETED/designs/repo-structure-config-contract.md`
- `.codex/config.toml`
- `templates/metadata/template-metadata-policy.json`
- `.taskmaster/tasks/task_100.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `100`

## Branch Policy
- Working branch: `feat/task-100-foundation-bootstrap-layer`

## Amendments & Versioning
- 2026-04-24 - Task 100 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 100 status evidence and handoff.
  3. Review `templates/engine/core/portable-foundation-spec.md` and the Task 98 repo-structure contract before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep bootstrap logic data-driven and migration-safe; do not hardcode this repo's layout back into the adoption path.

## Conflict & Scope Declaration
- Related plans: Task 99 portable foundation spec, Task 98 repo-structure externalization, Task 101 cross-project fixtures.
- Guard cross-check: bootstrap scaffolding must preserve plan/tracker/session compliance without assuming this repo is the target layout.

## Evidence Checklist
- Bootstrap outline under `designs/`
- Tracker/session entries for kickoff, design decisions, and implementation progress
- Stored helper, guard, and repo-setup evidence once bootstrap commands land

## Emergency Bypass Protocol
- No bypass authorized.
