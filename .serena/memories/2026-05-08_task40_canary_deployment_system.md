# Task 40 Canary Deployment System

## Context
- Date: 2026-05-08
- Branch: `feat/task-40-canary-deployment-system`
- Taskmaster task: 40, `Create Canary Deployment System`
- Active plan: `plans/2026-05-08-task40-canary-deployment-system.md`
- Active work tracking: `docs/ai/work-tracking/active/20260508-task40-canary-deployment-system-ACTIVE/`

## Scope Decision
Task 40's historical wording referenced production canary deployment concepts such as traffic splitting, notifications, dashboards, automatic promotion, rollback triggers, and staged Codex/Claude/other-agent windows. The current repository is a portable workflow/template foundation, not a deployable service, so the task was narrowed to a non-destructive foundation canary rollout planner.

## Implementation
- Added `python3 scripts/codex-task rollout canary-plan` in `scripts/codex-task`.
- The planner emits JSON and optional Markdown runbook output.
- It snapshots current Git, workflow, Taskmaster, and Serena state.
- It encodes staged rollout guidance for Codex (24h), Claude (48h), and other agents/profiles (72h).
- It requires reviewed evidence for promotion and a checkpoint for rollback.
- It explicitly does not execute deployment, traffic splitting, automatic promotion, rollback commands, dashboards, notifications, or external feature flag configuration.

## Tests And Evidence
- Added focused tests in `tests/meta_workflow_guard/test_codex_task.py` for parser wiring, plan payload, runbook rendering, and output file writing.
- Focused evidence: `docs/ai/work-tracking/active/20260508-task40-canary-deployment-system-ACTIVE/reports/canary-deployment-system/tests-2026-05-08-codex-task.txt`.
- Live planner evidence: `canary-plan-2026-05-08.json` and `canary-runbook-2026-05-08.md` in the same report folder.

## Resume Notes
After this memory was written, rerun guard because the previous guard failure was only the missing Serena memory tracker reference. Then finish verification, mark Taskmaster subtask 40.2 and parent 40 done, commit/push/PR/merge, and archive the Task 40 work-tracking folder.