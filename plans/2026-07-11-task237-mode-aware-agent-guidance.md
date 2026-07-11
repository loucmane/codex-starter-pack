---
session_id: 2026-07-11-002
work_context: task237-mode-aware-agent-guidance
handler_target: scripts/_aegis_installer.py
task_ids: [237]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/
  - docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/designs/mode-aware-guidance-contract.md
  - scripts/_aegis_installer.py
  - aegis_foundation/assets/scripts/_aegis_installer.py
  - tests/meta_workflow_guard/test_aegis_installer.py
  - tests/meta_workflow_guard/test_continuation_contract.py
  - .taskmaster/tasks/task_237.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 237 Make Managed Agent Guidance Truthful And Mode-Aware

## Header
- **Session ID (S)**: 2026-07-11-002
- **Work Context (W)**: task237-mode-aware-agent-guidance
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 237
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: Task 237 design, canonical and packaged installer renderers, focused installer/continuation tests, Blog dogfood, and Taskmaster evidence
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define compact mode-aware guidance, ownership, preservation, and non-goal contracts | docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/designs/mode-aware-guidance-contract.md; docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Update canonical/packaged renderers, source Codex managed block, and install/update preservation tests | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; CODEX.md; tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_continuation_contract.py; docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Run focused, authoritative, parity, guard, and Blog dogfood validation | docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/reports/mode-aware-agent-guidance/task-verification.md; docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260711-task237-mode-aware-agent-guidance-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `CODEX.md` managed block only
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_continuation_contract.py`
- `.taskmaster/tasks/task_237.md`
- Taskmaster Task `237`

## Branch Policy
- Working branch: `feat/task-237-mode-aware-guidance`

## Amendments & Versioning
- 2026-07-11 - Task 237 kickoff created via the guided wizard flow.
- 2026-07-11 - Replaced the generic wizard plan with the Task 237 mode-aware managed-guidance contract; no enforcement behavior change is authorized.
- 2026-07-11 - Added checksum-backed migration for exact manifest-owned markerless Claude
  runtimes after isolated Blog dogfood exposed obsolete ceremony preservation.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 237 and its subtasks.
  3. Review `designs/mode-aware-guidance-contract.md` before changing a renderer or merge path.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve project-owned bytes on repeat CODEX updates; keep advisory wording descriptive rather than creating a second enforcement policy.

## Conflict & Scope Declaration
- Related tasks: 199 advisory mode, 235 managed-update divergence, 236 convergence roadmap, 238 output budgets, and 210 PR-4 retirement.
- Guard cross-check: strict behavior and `.aegis/contract.md` remain unchanged; all entrypoint updates preserve project-owned content.

## Evidence Checklist
- Mode-aware guidance contract under `designs/`
- Fresh/update/divergence fixtures for Claude, Codex, and multi-agent installs
- Source/package parity and managed-block nonblank-line budgets
- Blog dry-run/apply dogfood with project instructions preserved
- Focused, authoritative, guard, and diff evidence

## Emergency Bypass Protocol
- No bypass authorized.
