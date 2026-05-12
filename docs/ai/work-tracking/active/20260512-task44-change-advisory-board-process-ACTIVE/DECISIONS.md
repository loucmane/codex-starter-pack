# Decisions

- 2026-05-12 — Implement Task 44 as a non-destructive change advisory packet/runbook helper in `scripts/codex-task`, backed by focused tests and task evidence. Do not implement live CAB meetings, stakeholder voting, notification delivery, dashboards, deployment gates, or a parallel tracking system.
- 2026-05-12 — Reuse `templates/metadata/template-governance-policy.json` and `scripts/template_governance.py` for review class, role, approval, communication-audience, and required-evidence semantics instead of creating a second CAB policy.
- 2026-05-12 — Do not reopen completed Taskmaster Task 44 solely to rewrite historical parent details. The completed subtasks and work-tracking scope reconciliation already document the current implementation, and reopening a done task after verification would create unnecessary Taskmaster churn.
