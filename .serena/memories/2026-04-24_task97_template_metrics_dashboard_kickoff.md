# Task 97 Template Metrics Dashboard

- Branch: `feat/task-97-template-metrics-dashboard`
- Active folder: `docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/`
- Session: `sessions/2026/04/2026-04-24-004-task97-template-metrics-dashboard.md`
- Plan: `plans/2026-04-24-task97-template-metrics-dashboard.md`

## Scope
Implement a repo-local metrics generator that writes `reports/template-metrics/latest.md` and `latest.json` from existing workflow sources: Taskmaster JSON, template drift reports, plan sync log, work-tracking folders, session logs, and `codex-guard` metadata helpers.

## Important findings
- Starting Task 97 exposed a Task 96 wizard defect: the kickoff session used the wrong `S` token (`20260424004` instead of the day token) and did not mirror kickoff entries into the tracker. `scripts/codex-task` and its tests were fixed before Task 97 continued.
- `scripts/template-metrics-dashboard` now exists and is wired into both guard workflows.
- Repo-level outputs live under `reports/template-metrics/`; Task 97 evidence lives under `docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/reports/template-metrics-dashboard/`.

## Verification status
- `python3 scripts/template-metrics-dashboard` passes and writes the dashboard outputs.
- Focused pytest suite passes: `tests/meta_workflow_guard/test_template_metrics_dashboard.py`, `test_codex_task.py`, `test_guard_rules.py`.
- Guard still needs a rerun after updating the tracker with this Serena memory reference and marking `plan-step-scope` complete in the plan/tracker.

## Next steps
1. Update Task 97 session/tracker/plan with the Serena memory reference and current implementation results.
2. Rerun `python3 scripts/codex-task plan sync --plan plans/2026-04-24-task97-template-metrics-dashboard.md --tracker docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/TRACKER.md`.
3. Rerun `python3 scripts/codex-guard validate --include-untracked`.
4. Mark Taskmaster subtasks and Task 97 done, then capture final handoff.
