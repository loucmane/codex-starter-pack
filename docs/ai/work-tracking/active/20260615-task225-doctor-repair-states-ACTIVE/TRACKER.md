# Task 225 Surface doctor safe-repair vs manual-review states in aegis next Tracker

**Started**: 2026-06-15
**Status**: ACTIVE
**Last Updated**: 2026-06-15

## Goals
- [x] next_action emits safe_repair_available + manual_review_repair states
- [x] CONTINUATION_BRIEF_BY_STATE entries for both (manual-review confirmation-gated)
- [x] tests: states + briefs; safe-repair apply-gated, manual-review never auto-applies
- [x] assets installer re-mirrored byte-identical

## Progress Log
- **2026-06-15 20:11** — [S:20260615|W:task225-doctor-repair-states|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-06-15 20:11 CEST`
- **2026-06-15 20:11** — [S:20260615|W:task225-doctor-repair-states|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/TRACKER.md] Scaffolded the Task 225 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-06-15 20:11** — [S:20260615|W:task225-doctor-repair-states|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 225 in progress and updated only its generated task file
- **2026-06-15 20:11** — [S:20260615|W:task225-doctor-repair-states|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 225 kickoff
- **2026-06-15 20:30** — [S:20260615|W:task225-doctor-repair-states|H:workflow:design|E:docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/designs/wizard-flow.md] Scope/design: ran a design workflow on doctor/repair + next_action; chose severity-gated detection, injection after scaffold, normalize_plan_table exclusion
- **2026-06-15 20:35** — [S:20260615|W:task225-doctor-repair-states|H:scripts/_aegis_installer.py|E:scripts/_aegis_installer.py] Implement: _repair_plan_split + severity-gated repair branch in next_action (safe_repair_available / manual_review_repair) + brief entries; re-mirrored assets
- **2026-06-15 20:45** — [S:20260615|W:task225-doctor-repair-states|H:workflow:adversarial-review|E:scripts/_aegis_installer.py] Adversarial review found Finding #2 (cosmetic-action resurrection swallowing a real failure); fixed via substantive-only gate + regression test
- **2026-06-15 20:50** — [S:20260615|W:task225-doctor-repair-states|H:pytest|E:docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/reports/task225-doctor-repair-states/tests-2026-06-15-final.txt] Verify: focused 20 passed; installer/MCP/replay/parity 175 passed; full suite green
- **2026-06-15 20:52** — [S:20260615|W:task225-doctor-repair-states|H:serena/memory|E:.serena/memories/task225-doctor-repair-states.md] Captured Task 225 Serena memory.

## Plan Compliance Checklist
- [x] plan-step-scope — Design via workflow; severity-gated detection, injection after scaffold, normalize exclusion
- [x] plan-step-implement — _repair_plan_split + repair branch + brief entries + assets mirror + tests
- [x] plan-step-verify — Design + adversarial review run; Finding #2 fixed; suites green; evidence stored
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
