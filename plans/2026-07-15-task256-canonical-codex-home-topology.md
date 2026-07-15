---
session_id: 2026-07-15-003
work_context: task256-canonical-codex-home-topology
handler_target: aegis_foundation/codex_topology.py
task_ids: [256]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/
  - aegis_foundation/codex_topology.py
  - docs/aegis/canonical-codex-home-architecture.md
  - docs/aegis/task257-canonical-codex-home-cutover-plan.md
  - docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/reports/canonical-codex-home-topology/task-verification.md
  - .taskmaster/tasks/task_256.md
plan_version: v3
emergency_bypass: false
---

# Plan - Task 256 Canonical Codex Home Topology Diagnostics and Migration Plan

## Header
- **Session ID (S)**: 2026-07-15-003
- **Work Context (W)**: task256-canonical-codex-home-topology
- **Handler Target (H)**: aegis_foundation/codex_topology.py
- **Task IDs**: 256
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/, aegis_foundation/codex_topology.py, docs/aegis/canonical-codex-home-architecture.md, docs/aegis/task257-canonical-codex-home-cutover-plan.md, docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/reports/canonical-codex-home-topology/task-verification.md, .taskmaster/tasks/task_256.md
- **Plan Version**: v3
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Record the binding canonical-home ADR, official Codex facts, Aegis inferences, and Task 256 non-goals | docs/aegis/canonical-codex-home-architecture.md; docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/designs/canonical-home-topology-contract.md | completed |
| plan-step-contract | Freeze the secret-safe status schema, split-brain and stale-thread rules, CLI surface, and deterministic planner contract | docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/designs/canonical-home-topology-contract.md | completed |
| plan-step-implement | Implement read-only topology collection and no-mutation planning without changing either live Codex home or any server | aegis_foundation/codex_topology.py; aegis_foundation/cli.py | completed |
| plan-step-test | Prove healthy, split-brain, stale/fresh thread, unknown-state, redaction, determinism, no-write, CLI, and package-parity behavior | tests/meta_workflow_guard/test_codex_topology.py | completed |
| plan-step-cutover | Publish the exact drain-first Task 257 host cutover, rollback boundaries, preservation requirements, and attended checkpoints | docs/aegis/task257-canonical-codex-home-cutover-plan.md | completed |
| plan-step-verify | Run focused and regression verification, synchronize workflow evidence, close out Task 256, and prepare attended exact-head PR delivery | docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/HANDOFF.md; docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/`
- `aegis_foundation/codex_topology.py`
- `aegis_foundation/cli.py`
- `docs/aegis/canonical-codex-home-architecture.md`
- `docs/aegis/task257-canonical-codex-home-cutover-plan.md`
- packaged documentation mirrors under `aegis_foundation/assets/docs/aegis/`
- `schemas/aegis/codex-topology-*.schema.json`
- packaged schema mirrors under `aegis_foundation/assets/schemas/aegis/`
- `.taskmaster/tasks/task_256.md`
- `tests/meta_workflow_guard/test_codex_topology.py`
- `tests/meta_workflow_guard/test_aegis_schemas.py`
- Taskmaster Task `256`

Explicitly out of scope are live Codex-home writes, server lifecycle operations, process
signals, shell or wrapper edits, Blog changes, session/auth/trust/hash copying, hook-trust
bypass, host cutover, wrapper retirement, and Taskmaster-to-Gas-Town migration.

## Branch Policy
- Working branch: `feat/task-256-canonical-codex-home-topology`

## Amendments & Versioning
- 2026-07-15 - Task 256 kickoff created via the guided wizard flow.
- 2026-07-15 - v2 replaced generic wizard boilerplate with the owner-approved canonical-home diagnostic and migration-planning contract.
- 2026-07-15 - Implementation completed as a bounded read-only collector, strict JSON schemas, deterministic ten-phase Task 257 planner, and source/package documentation mirrors; verification and attended delivery remain.
- 2026-07-15 - v3 completed source verification and closeout preparation; attended exact-head PR review remains the delivery boundary outside Task 256's implementation-complete status.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 256 and its subtasks.
  3. Review the canonical-home ADR and topology contract before changing diagnostic behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: never turn a diagnostic observation into inferred hook trust, active-work safety, or permission to mutate host state.

## Conflict & Scope Declaration
- Related work: Tasks 253-255 establish tracked hook guidance, strict portability, and the transitional dual-home trust bridge.
- Guard cross-check: Task 256 may describe Task 257 mutations but must remain read-only with respect to host topology.

## Evidence Checklist
- Canonical-home ADR and topology design contract
- Deterministic Task 257 drain-first cutover plan
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
