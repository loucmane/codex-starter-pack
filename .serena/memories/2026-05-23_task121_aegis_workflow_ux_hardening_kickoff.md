# Task 121 Aegis Workflow UX and Logging Defaults Kickoff

Date: 2026-05-23
Branch: feat/task-121-aegis-workflow-ux-hardening
Taskmaster: Task 121, in-progress
Session: sessions/2026/05/2026-05-23-001-task121-aegis-workflow-ux-hardening.md
Plan: plans/2026-05-23-task121-aegis-workflow-ux-hardening.md
Work tracking: docs/ai/work-tracking/active/20260523-task121-aegis-workflow-ux-hardening-ACTIVE/

## Scope
Task 121 hardens Aegis installed workflow ergonomics before TestPyPI/PyPI. It keeps the architecture proven by Task 120: Aegis MCP/CLI is the workflow control plane, installed hooks enforce behavior, and native agent tools remain the normal implementation path.

## Task 120 Findings Driving This Task
- Fresh Claude local-wheel install passed end to end.
- Claude used MCP for install/kickoff/log/verify/closeout and native tools for source edits and app checks.
- Closeout still required extra relogging because default log surfaces missed canonical evidence surfaces.
- Strict verify created pending tracking that required exact handler/evidence copying.
- Closeout missing-evidence output identified missing surfaces but did not provide actionable repair commands.

## Initial Plan
- Create a Task 121 scope design artifact from the Task 120 live-test result.
- Add event-aware default surfaces for aegis log while preserving explicit surface overrides.
- Add pending-event consumption by id/sentinel for CLI and MCP.
- Improve hook pending-event guidance and closeout repair guidance.
- Add regression tests that prove the installed web workflow closes out without extra relogging.

## Boundaries
- Do not publish to TestPyPI or PyPI in this task.
- Do not make MCP the editor path; MCP remains control plane only.
- Keep source and packaged Aegis assets in sync.