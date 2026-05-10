# Task 35 Create Emergency Response System – Implementation Notes

## Planned Workstreams
- Reconcile legacy external incident-response wording against the portable foundation before coding.
- Add a repo-local emergency response policy with P0-P3 severity, SLA, halt guidance, response checklist, escalation guidance, post-incident prompts, and non-goals.
- Add `python3 scripts/codex-task emergency plan` to generate non-destructive JSON and Markdown response artifacts from the policy and current workflow state.
- Keep bootstrap/sync portability intact by adding the emergency policy and report root to repo-structure helpers.
- Add focused regression coverage for parser support, policy loading, plan generation, runbook rendering, bootstrap portability, and cross-project roots.

## Implemented Surface

- `templates/metadata/emergency-response-policy.json`
- `scripts/_repo_structure.py`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `tests/meta_workflow_guard/test_repo_structure_config.py`
- Live Task 35 emergency artifacts:
  - `reports/emergency-response-system/emergency-plan-2026-05-10.json`
  - `reports/emergency-response-system/emergency-runbook-2026-05-10.md`

## Non-Destructive Guarantees

- The planner writes only the requested report/runbook artifacts.
- It snapshots Git, workflow, Taskmaster, and Serena state.
- It recommends halt for configured severities but does not create a halt marker.
- It does not run notification, dashboard, rollback, reset, clean, restore, branch deletion, force-push, or external incident actions.
