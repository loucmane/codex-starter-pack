# Task {{task_id}} {{title}} Tracker

**Started**: {{date}}
**Status**: ACTIVE
**Last Updated**: {{date}}
**Authority**: `{{current_work_rel}}`
**Session**: `{{session_rel}}`
**Plan**: `{{plan_rel}}`
**Reports**: `{{reports_rel}}/`

## Goals
{{goals_checklist}}

## Progress Log
- **{{timestamp_tracker}}** - [S:{{session_value}}|W:{{work_context}}|H:aegis:kickoff|E:{{current_work_rel}}] Created Aegis-native current work state.
- **{{timestamp_tracker}}** - [S:{{session_value}}|W:{{work_context}}|H:sessions/current|E:{{session_rel}}] Created current session and repointed `sessions/current`.
- **{{timestamp_tracker}}** - [S:{{session_value}}|W:{{work_context}}|H:plans/current|E:{{plan_rel}}] Created current plan and repointed `plans/current`.
- **{{timestamp_tracker}}** - [S:{{session_value}}|W:{{work_context}}|H:work-tracking|E:{{tracker_rel}}] Created active work-tracking scaffold.

## Plan Compliance Checklist
- [ ] plan-step-scope - Confirm task scope, constraints, expected outputs, and affected files
- [ ] plan-step-implement - Make only task-scoped changes and record implementation notes
- [ ] plan-step-verify - Run verification, capture reports, and update handoff state
- [ ] plan-step-emergency (if applicable)

## Current State
Task {{task_id}} has been kicked off through Aegis. The project is ready for task-scoped work once readiness reports READY.

## Next Steps
1. Confirm scope and constraints in FINDINGS.md and DECISIONS.md.
2. Implement only task-scoped changes.
3. Store verification evidence under `{{reports_rel}}/`.
4. Update HANDOFF.md before ending the session.

## Dependencies & Notes
- Taskmaster: optional unless `{{current_work_rel}}` marks it required.
- Serena: optional continuity only; never required for READY.
- Direct workflow state writes should go through Aegis CLI or MCP tools.
