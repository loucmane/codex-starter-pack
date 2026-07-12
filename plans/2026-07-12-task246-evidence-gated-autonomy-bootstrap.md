---
session_id: 2026-07-12-003
work_context: task246-evidence-gated-autonomy-bootstrap
handler_target: scripts/_source_workflow_state.py
task_ids: [246]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/
  - scripts/_source_workflow_state.py
  - scripts/aegis-delivery-policy
  - aegis.delivery-policy.json
  - .github/workflows/aegis-autonomous-delivery.yml
  - .codex/deep-work.config.toml
  - .aegis/brief.json
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_246.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 246 Bootstrap Evidence-Gated Autonomous Delivery

## Header
- **Session ID (S)**: 2026-07-12-003
- **Work Context (W)**: task246-evidence-gated-autonomy-bootstrap
- **Handler Target (H)**: scripts/_source_workflow_state.py
- **Task IDs**: 246
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/, scripts/_source_workflow_state.py, scripts/aegis-delivery-policy, aegis.delivery-policy.json, .github/workflows/aegis-autonomous-delivery.yml, .codex/deep-work.config.toml, .aegis/brief.json, scripts/_aegis_installer.py, .taskmaster/tasks/task_246.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin main-branch derivation authorities, delivery-policy trust boundary, eligibility classes, persistence, and rollback | docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/designs/evidence-gated-autonomy-contract.md | completed |
| plan-step-implement | Implement fail-closed main derivation, policy engine/schema, mode-aware Aegis guidance, and trusted autonomous-delivery workflow | scripts/_source_workflow_state.py; scripts/aegis-delivery-policy; aegis.delivery-policy.json; .github/workflows/aegis-autonomous-delivery.yml; scripts/_aegis_installer.py; docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Replay PR #261 main-push failures, prove self-authorization resistance and attended categories, complete local gates, and preserve hosted PR/protected-main checks plus the bootstrap's final attended merge boundary as publication gates | docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/reports/evidence-gated-autonomy/task-verification.md; docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/HANDOFF.md | completed |
| plan-step-hardening | Add a non-overridable command guard for destructive Git, protected-branch pushes, remote replacement, and GitHub branch-protection mutation; preserve normal feature-branch delivery and prove advisory mode cannot downgrade the denial | .claude/scripts/gate_lib.py; aegis_foundation/assets/.claude/scripts/gate_lib.py; tests/claude_adapter/test_pretooluse_gates.py | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED/`
- `scripts/_source_workflow_state.py`
- `scripts/aegis-delivery-policy`
- `aegis_foundation/assets/scripts/aegis-delivery-policy`
- `aegis.delivery-policy.json`
- `schemas/aegis/delivery-policy.schema.json`
- `aegis_foundation/assets/schemas/aegis/delivery-policy.schema.json`
- `.github/workflows/aegis-autonomous-delivery.yml`
- `.codex/deep-work.config.toml`
- `.aegis/brief.json`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_246.md`
- `tests/`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `docs/aegis/`
- Taskmaster Task `246`

## Branch Policy
- Working branch: `feat/task-246-evidence-gated-autonomy-bootstrap`

## Amendments & Versioning
- 2026-07-12 - Task 246 kickoff created via the guided wizard flow.
- 2026-07-12 - Owner authorized a pre-merge hardening amendment: destructive Git and GitHub governance mutations must remain blocked even when ordinary Aegis enforcement is advisory.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 246 and its subtasks.
  3. Review the evidence-gated autonomy contract before changing source derivation or delivery authority.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: candidate PR bytes must never control privileged policy evaluation; taskless-main derivation must reject stale or contradictory current pointers; policy changes remain attended; missing policy remains backward-compatible attended mode.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Evidence-gated autonomy contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored PR #261 failure replay, policy-engine, workflow-contract, installer, full-suite, and hosted evidence

## Emergency Bypass Protocol
- No bypass authorized.
