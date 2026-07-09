---
session_id: 2026-07-09-002
work_context: task234-witness-delivery-projection
handler_target: aegis_foundation/cli.py
task_ids: [234]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260709-task234-witness-delivery-projection-ACTIVE/
  - aegis_foundation/cli.py
  - aegis_foundation/legacy_projection.py
  - .taskmaster/tasks/task_234.md
  - tests/claude_adapter/test_legacy_projection.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 234 Project witness and delivery boundaries into legacy S:W:H:E surfaces

## Header
- **Session ID (S)**: 2026-07-09-002
- **Work Context (W)**: task234-witness-delivery-projection
- **Handler Target (H)**: aegis_foundation/cli.py
- **Task IDs**: 234
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260709-task234-witness-delivery-projection-ACTIVE/, aegis_foundation/cli.py, aegis_foundation/legacy_projection.py, .taskmaster/tasks/task_234.md, tests/claude_adapter/test_legacy_projection.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define machine-grounded witness/delivery event identity, deduplication, projection, and failure semantics | docs/ai/work-tracking/active/20260709-task234-witness-delivery-projection-ACTIVE/designs/boundary-projection-design.md | completed |
| plan-step-implement | Record/project local witness outcomes and add GitHub-backed `aegis delivery sync` | aegis_foundation/cli.py; aegis_foundation/legacy_projection.py; scripts/_aegis_installer.py | completed |
| plan-step-verify | Prove idempotency, human-content preservation, CI non-persistence, GitHub truth handling, and blog dogfood | tests/claude_adapter/test_legacy_projection.py; docs/aegis/blog-legacy-shadow-sweh-dogfood-2026-07-09.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260709-task234-witness-delivery-projection-ACTIVE/`
- `aegis_foundation/cli.py`
- `aegis_foundation/legacy_projection.py`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `docs/aegis/legacy-shadow-sweh-projection-contract.md`
- `docs/aegis/pr-4-replacement-parity-matrix.md`
- `.taskmaster/tasks/task_234.md`
- `tests/`
- Taskmaster Task `234`

## Branch Policy
- Working branch: `feat/task-234-witness-delivery-projection`

## Amendments & Versioning
- 2026-07-09 - Task 234 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 234 and the TM-233 coexistence contract.
  3. Review the boundary-projection design before changing CLI or GitHub truth behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: never accept self-reported delivery truth; never let projection failure change a witness verdict; avoid duplicate boundary events when hooks and explicit commands both observe the same action.

## Conflict & Scope Declaration
- Related tasks: TM-233 legacy projection, TM-229 PR-4 parity matrix, TM-210 evidence-gated retirement.
- Guard cross-check: this slice adds boundary projections only; it does not demote or retire any legacy surface.

## Evidence Checklist
- Boundary design note under `designs/`
- Deterministic unit and CLI integration tests for witness/delivery event recording and projection
- Blog PR dogfood showing scope, witness, and GitHub delivery events projected into archived legacy surfaces
- Tracker/session entries plus parity-matrix evidence; PR-4 remains blocked

## Emergency Bypass Protocol
- No bypass authorized.
