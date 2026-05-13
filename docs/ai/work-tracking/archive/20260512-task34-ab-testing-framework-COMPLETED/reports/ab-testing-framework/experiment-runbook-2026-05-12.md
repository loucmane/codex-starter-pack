# Foundation Experiment Runbook

- Label: task34-foundation-experiment
- Created at: 2026-05-12T22:32:01+02:00
- Mode: non-destructive-foundation-experiment-plan
- Executes mutations: False
- Current branch: feat/task-34-ab-testing-framework
- Current HEAD: e98d6f1f9cfb799d07659e97d868351374bc51e2
- Current dirty status entries: 11

## Variants

- current-foundation (control): 50.0%
- candidate-foundation (candidate): 50.0%

## Metrics

- Guard validation: `python3 scripts/codex-guard validate --include-untracked`
  - Success: Exit code 0 and no S:W:H:E or workflow-state issues.
- Focused regression tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <focused tests>`
  - Success: Exit code 0 for the experiment-specific regression surface.
- Performance policy: `python3 scripts/template-performance-harness --strict`
  - Success: Status pass; warn/fail deltas must be documented before promotion.
- Monitoring policy: `python3 scripts/template-monitoring --strict`
  - Success: Status pass against repo-local monitoring thresholds.
- Taskmaster health: `python3 scripts/codex-task taskmaster health`
  - Success: Zero invalid dependency references.

## Stop Conditions

- Candidate error or failure rate exceeds control by more than 5.00%.
- Any required guard, audit, health, or focused test command fails.
- Performance or monitoring reports fail strict policy.
- Evidence is missing for any control or candidate variant.

## Promotion Model

- Automatic promotion: False
- Reviewed evidence required: True
- Decision log required: True

## Rollback Policy

- Automatic rollback: False
- Stop and render a reviewed rollback/recovery plan if a stop condition fires.
- Do not execute destructive rollback commands from this experiment planner.

## Recommended Verification Commands

- `python3 scripts/codex-task rollout experiment-plan --report-file <plan.json> --runbook-file <runbook.md>`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `git diff --check`

## Non-Goals

- No LaunchDarkly or external feature flag service is configured.
- No runtime user segmentation is performed.
- No traffic is split or routed.
- No automatic rollback command is executed.
- No dashboard is generated.
- No notification is sent.

No feature flag service, traffic split, promotion, rollback, dashboard update, or notification was executed by this plan.
