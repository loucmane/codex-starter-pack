# Task 44 Change Advisory Scope Reconciliation

## Purpose

Task 44 originally asked for a formal Change Advisory Board process: meeting cadence, change request template, change tracking, risk assessment, stakeholder approvals, communication delivery, metrics, and post-implementation reviews.

That wording predates the current portable foundation. The repository now has file-backed governance, emergency response, rollback, canary rollout, communication-template, CI, and final-validation primitives. Task 44 must therefore preserve the useful advisory intent without creating fake meetings, external approvals, dashboards, or notification systems.

## Evidence Reviewed

- `templates/engine/core/portable-foundation-spec.md` defines portable lifecycle, work-tracking, plan, enforcement, and repo-local policy contracts.
- `templates/metadata/template-governance-policy.json` defines review classes, required roles, approval guidance, notification audiences, and required evidence.
- `scripts/template_governance.py` already performs non-mutating governance assessment for version changes, lifecycle transitions, and emergency escalation.
- Task 36 completed the template governance board as a file-backed governance policy and assessor, not a live board or notification process.
- Task 35 completed emergency response as a non-destructive plan/runbook generator.
- Task 19 completed rollback as checkpoint manifests and reviewed recovery guidance.
- Task 40 completed canary rollout as deterministic staged rollout plans, not deployment automation.
- Task 49 completed repository-native communication templates, not distribution-list automation.
- Task 68 completed final validation as an executable evidence suite and sign-off runbook.
- Task 20 completed CI suite coverage and explicitly kept deployment gates and external repository settings out of repo-file scope.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 44 Decision |
| --- | --- | --- |
| CAB meeting structure and cadence | The foundation has no calendar, voting, or meeting backend. Task 36 already maps governance classes to roles and approval guidance. | Do not implement meetings. Render advisory packet sections that identify required roles and review guidance. |
| Change request template | Current tasks already use plan/tracker/session/work-tracking evidence, but no single change advisory packet composes the evidence into a review artifact. | Implement a deterministic JSON + Markdown advisory packet. |
| Change tracking system | Taskmaster, Git, sessions/current, plans/current, and work-tracking already track changes. | Snapshot existing tracking state; do not create a parallel tracker. |
| Risk assessment framework | Task 36 governance policy already defines review classes and evidence requirements. | Reuse governance assessment and add advisory-specific risk/evidence sections. |
| Stakeholder approval workflow | Governance policy already defines roles and approval wording; no external approver system exists. | Record approval expectations as evidence-only guidance. |
| Change communication plan | Task 49 provides communication templates; governance policy defines notification audiences with `notification_mode: evidence-only`. | Include communication guidance; do not send notifications. |
| Change metrics tracking | Dashboards and metrics exist for foundation reports, but CAB-specific live metrics would be duplicative. | Include report paths and current-state snapshot; do not create a metrics service. |
| Post-implementation reviews | Emergency response and final validation already include review/sign-off prompts. | Add post-implementation review prompts to the advisory runbook. |

## Confirmed Current Gap

The repository has the component controls, but no command that composes them into a single advisory packet for a proposed change. Today an agent must remember how to combine:

- governance review class and required roles,
- active Taskmaster/session/plan/work-tracking state,
- guard, audit, health, test, final-validation, rollback, canary, emergency, and communication evidence,
- approval and post-implementation review prompts.

That remembered composition is the gap. Task 44 should make it executable and evidence-backed.

## Selected Implementation Scope

Add a non-destructive change advisory planner to `scripts/codex-task`:

```bash
python3 scripts/codex-task change advisory \
  --summary "Proposed change summary" \
  --path templates/example.md \
  --previous-version 1.2.0 \
  --current-version 2.0.0 \
  --report-file docs/ai/work-tracking/active/<folder>/reports/change-advisory-board-process/change-advisory.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/change-advisory-board-process/change-advisory.md
```

The command should:

- write deterministic JSON and optional Markdown runbook outputs;
- call the existing template governance policy/assessment logic instead of duplicating it;
- support explicit `--review-class` override for non-template or manually classified changes;
- snapshot current Git, workflow, Taskmaster, and Serena state;
- list required roles, approval guidance, evidence requirements, communication audiences, and notification mode;
- recommend additional controls by review class, such as rollback checkpoint/final validation for breaking changes and emergency response planning for emergency changes;
- include post-implementation review prompts;
- clearly state that it executes no meetings, votes, approvals, notifications, dashboards, deployments, rollback, or external tracking updates.

## Non-Goals

- No live CAB meeting workflow.
- No external ticketing or change database.
- No stakeholder voting or approval automation.
- No notification delivery.
- No dashboard or metrics service.
- No deployment gates or branch-protection settings.
- No duplicate governance policy separate from `templates/metadata/template-governance-policy.json`.
- No destructive rollback, reset, cleanup, or deployment action.

## Planned Files

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `docs/ai/work-tracking/active/20260512-task44-change-advisory-board-process-ACTIVE/` task artifacts
- Taskmaster Task 44 artifacts

## Evidence Plan

- `python3 scripts/codex-task change advisory --summary "Task 44 evidence advisory" --review-class breaking --report-file <task-report>.json --runbook-file <task-runbook>.md`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Decision

Proceed with a change advisory packet/runbook generator. This satisfies Task 44 by making advisory review repeatable, evidence-backed, and portable while respecting the current foundation architecture and avoiding fake organizational infrastructure.

## Progress Log

- **2026-05-12 18:42** — [S:20260512|W:task44-change-advisory-board-process|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260512-task44-change-advisory-board-process-ACTIVE/designs/change-advisory-scope-reconciliation.md] Reconciled Task 44 against the current portable foundation and selected a non-destructive change advisory packet/runbook as the current implementation gap.
