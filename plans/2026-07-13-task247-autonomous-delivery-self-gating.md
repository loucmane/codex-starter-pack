---
session_id: 2026-07-13-003
work_context: task247-autonomous-delivery-self-gating
handler_target: scripts/aegis-delivery-policy
task_ids: [247]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260713-task247-autonomous-delivery-self-gating-ACTIVE/
  - scripts/aegis-delivery-policy
  - .github/workflows/aegis-autonomous-delivery.yml
  - tests/fixtures/aegis/pr264-autonomous-delivery-self-gating.json
  - tests/meta_workflow_guard/test_aegis_delivery_policy.py
  - tests/meta_workflow_guard/test_aegis_autonomous_delivery_workflow.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 247 Fix Autonomous Delivery Self-Gating Race

## Header
- **Session ID (S)**: 2026-07-13-003
- **Work Context (W)**: task247-autonomous-delivery-self-gating
- **Handler Target (H)**: scripts/aegis-delivery-policy
- **Task IDs**: 247
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: Task 247 design/tracking, source and packaged policy, trusted delivery workflow, PR #264 replay fixture, and policy/workflow contract tests
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reproduce PR #264 and bind a fail-closed evaluator/executor contract | docs/ai/work-tracking/active/20260713-task247-autonomous-delivery-self-gating-ACTIVE/designs/self-gating-delivery-contract.md | completed |
| plan-step-implement | Add the non-authorizing provisional policy result, split trusted workflow, replay fixture, docs, and regression contracts | scripts/aegis-delivery-policy; aegis_foundation/assets/scripts/aegis-delivery-policy; .github/workflows/aegis-autonomous-delivery.yml; tests/fixtures/aegis/pr264-autonomous-delivery-self-gating.json | completed |
| plan-step-verify | Run focused and full suites, repository guards, hosted CI, exact-head delivery, live ordinary canary, and post-merge dispatch verification | docs/ai/work-tracking/active/20260713-task247-autonomous-delivery-self-gating-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260713-task247-autonomous-delivery-self-gating-ACTIVE/TRACKER.md | in-progress |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260713-task247-autonomous-delivery-self-gating-ACTIVE/`
- `.github/workflows/aegis-autonomous-delivery.yml`
- `scripts/aegis-delivery-policy`
- `aegis_foundation/assets/scripts/aegis-delivery-policy`
- `docs/aegis/evidence-gated-autonomous-delivery.md`
- `tests/fixtures/aegis/pr264-autonomous-delivery-self-gating.json`
- `tests/meta_workflow_guard/test_aegis_delivery_policy.py`
- `tests/meta_workflow_guard/test_aegis_autonomous_delivery_workflow.py`
- `.taskmaster/tasks/task_247.md`
- Taskmaster Task `247`

## Branch Policy
- Working branch: `feat/task-247-autonomous-delivery-self-gating`

## Amendments & Versioning
- 2026-07-13 - Task 247 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 247 and its subtasks.
  3. Review the self-gating delivery contract before changing policy or workflow behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: hosted CI and an ordinary post-merge canary must prove that the required evaluator can complete provisionally and that only a fresh clean `allow` reaches the merge endpoint.

## Conflict & Scope Declaration
- Related plans: Task 246 evidence-gated autonomy bootstrap and Task 239 PR #264 dogfood evidence.
- Guard cross-check: the required evaluator must remain read-only; attended paths and labels remain non-autonomous.

## Evidence Checklist
- Secret-free PR #264 replay fixture and self-gating contract under `designs/`
- Source/packaged policy byte parity and workflow trust-boundary contract tests
- Focused, meta-workflow, repository-wide, guard, hosted-CI, and live-canary evidence

## Emergency Bypass Protocol
- No bypass authorized.
