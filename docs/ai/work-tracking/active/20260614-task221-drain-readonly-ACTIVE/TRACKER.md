# Task 221 Drain must not accrete read-only events into required closeout evidence Tracker

**Started**: 2026-06-14
**Status**: ACTIVE
**Last Updated**: 2026-06-14

## Goals
- [ ] strict fail-keep _stored_event_is_read_only (Bash complement; MCP unconditional-read-only only, keep apply-gated)
- [ ] drain-gate in log_work: read-only pending event discards without accreting
- [ ] aegis repair --purge-read-only-pending batch purge (preview/--apply)
- [ ] tests incl. apply-gated MCP must be KEPT + fail-keep on broken gate_lib

## Progress Log
- **2026-06-14 15:02** — [S:20260614|W:task221-drain-readonly|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-06-14 15:02 CEST`
- **2026-06-14 15:02** — [S:20260614|W:task221-drain-readonly|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/TRACKER.md] Scaffolded the Task 221 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-06-14 15:02** — [S:20260614|W:task221-drain-readonly|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 221 in progress and updated only its generated task file
- **2026-06-14 15:02** — [S:20260614|W:task221-drain-readonly|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 221 kickoff
- **2026-06-14 15:17** — [S:20260614|W:task221-drain-readonly|H:scripts/_aegis_installer.py|E:docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/reports/pytest-drain-readonly.txt] Drain-layer fix: strict fail-keep _stored_event_is_read_only (Bash complement; MCP name-only, apply-gated KEPT), drain-gate discards read-only pending events without accreting, aegis repair --purge-read-only-pending batch purge. Adversarial diff-review SAFE; 20 tests pass.
- **2026-06-14 15:18** — [S:20260614|W:task221-drain-readonly|H:serena/memory|E:.serena/memories/task221-drain-readonly-fix.md] Captured Task 221 drain-readonly Serena memory; closes the HP-Coach closeout-report series.

## Plan Compliance Checklist
- [x] plan-step-scope — Define alignment prerequisites and scope
- [ ] plan-step-implement — Update workflow/guard/docs and capture tests
- [ ] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
