# Migration Rehearsal Runbook

- Label: task23-rehearsal
- Created at: 2026-05-08T12:12:25+02:00
- Mode: non-destructive-local-rehearsal
- Executes mutations: False

## Inputs

- Migration roadmap: docs/ai/work-tracking/active/20260508-task23-migration-rehearsal-environment-ACTIVE/reports/migration-rehearsal-environment/migration-roadmap-2026-05-08.json
- Rollback checkpoint: docs/ai/work-tracking/active/20260508-task23-migration-rehearsal-environment-ACTIVE/reports/migration-rehearsal-environment/checkpoint-2026-05-08.json

## Current State

- Current branch: feat/task-23-migration-rehearsal-environment
- Current HEAD: 3b73b3494ecf9edb656d609278c20edb25e18674
- Current dirty status entries: 10
- Checkpoint branch: feat/task-23-migration-rehearsal-environment
- Checkpoint HEAD: 3b73b3494ecf9edb656d609278c20edb25e18674

## Roadmap Summary

- Roadmap generated at: 2026-05-08T12:12:14.032335
- Roadmap version: 1.0.0
- Total roadmap items: 83
- Taskmaster draft items: 83

### Priority Counts

- critical: 63
- high: 16
- medium: 3
- low: 1

### Phase Plan

| Phase | Priorities | Start Day | Duration |
| --- | --- | --- | --- |
| Critical integrity | critical | 0 | 2 days |
| Foundation correctness | high | 2 | 3 days |
| Maintenance risk | medium | 5 | 2 days |
| Optimization backlog | low | 7 | 2 days |

### First Rehearsal Items

| Priority | Category | Effort | Risk | Findings | Title |
| --- | --- | --- | --- | --- | --- |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/MATRICES.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/file-operations/before-create.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/file-operations/before-edit.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/planning/plan-compliance.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/session/session-end.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/task-management/todo-write.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/behaviors/work-tracking/update-tracker.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/conventions/docs/documentation-standards.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/coordination/session-swhe-integration.md |
| critical | references | S | high | 1 | Repair 1 broken reference in templates/engine/navigation/common-flows.md |

## Rehearsal Steps

1. Review the rollback checkpoint and current dirty Git status.
2. Select the smallest roadmap item or coherent group of items to rehearse.
3. If additional isolation is required, create a git worktree manually after reviewing the command; this runbook does not create it.
4. Run the selected scanner or fix command in dry-run mode first.
5. Capture guard, audit, Taskmaster health, plan sync, and diff-check evidence before marking the rehearsal slice complete.
6. If any abort criterion triggers, stop and use the rollback checkpoint recovery plan for reviewed, non-destructive guidance.

## Recommended Verification Commands

- `git status --short --branch`
- `python3 scripts/codex-task rollback checkpoint --label <label> --report-file <path>`
- `python3 scripts/template-ssot-scanner/migration_roadmap.py --data-dir scripts/template-ssot-scanner/output/data --json-out <path> --markdown-out <path>`
- `python3 scripts/codex-task rehearsal plan --roadmap <roadmap.json> --checkpoint <checkpoint.json> --report-file <plan.json> --runbook-file <runbook.md>`
- `python3 scripts/codex-task taskmaster health --report-file <path>`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Abort Criteria

- Stop if guard, plan sync, Taskmaster health, or required pytest suites fail.
- Stop if the rollback checkpoint is missing, unreadable, or points at an unexpected branch/head.
- Stop if rehearsal requires Docker, external API keys, agent simulators, load testing, or destructive Git commands; those are out of scope for this foundation task.
- Treat 63 critical roadmap item(s) as pre-migration blockers unless explicitly waived in work tracking.
- Review the current dirty working tree (10 status entries) before applying roadmap changes.

## Non-Goals

- No Docker containers are created.
- No test API keys are read or written.
- No Claude/Codex agent simulators are launched.
- No k6/locust load test harness is invoked.
- No Taskmaster tasks are imported from roadmap data.
- No rollback, reset, clean, restore, or worktree command is executed.

No rehearsal commands were executed by this plan.
