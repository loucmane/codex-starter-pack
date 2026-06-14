# Task 218 Robust + recoverable closeout evidence (stable-key matching) Tracker

**Started**: 2026-06-13
**Status**: COMPLETED
**Last Updated**: 2026-06-13

## Goals
- [ ] stable-key matching: closeout.evidence.* recognizes commit SHA + canonical repo-relative paths, not just verbatim command strings
- [ ] demote free-text/compound-command tokens to advisory (non-required) deliberately
- [ ] recovery acceptance: lost-pending-event committed task reaches green closeout in one command
- [ ] adversarial guard: partial/sibling path + coincidental SHA substring must NOT satisfy the gate

## Progress Log
- **2026-06-13 18:07** — [S:20260613|W:task218-recoverable-evidence|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-06-13 18:07 CEST`
- **2026-06-13 18:07** — [S:20260613|W:task218-recoverable-evidence|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/TRACKER.md] Scaffolded the Task 218 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-06-13 18:07** — [S:20260613|W:task218-recoverable-evidence|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 218 in progress and updated only its generated task file
- **2026-06-13 18:07** — [S:20260613|W:task218-recoverable-evidence|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 218 kickoff
- **2026-06-13 18:32** — [S:20260613|W:task218-recoverable-evidence|H:scripts/_aegis_installer.py|E:docs/ai/work-tracking/active/20260613-task218-recoverable-evidence-ACTIVE/reports/pytest-evidence-demotion.txt] Demotion fix: command/free-text evidence tokens advisory (cmd/note prefix + metachar fallback); paths/SHAs stay required. Recovers HP-Coach canonical case; invariant intact (strict_verify+pending_tracking independent). Stable-key matching dropped (redundant/inert); populate deferred TM 220; assets-installer drift filed TM 219. 8 focused tests + 1 updated semantics test pass.
- **2026-06-13 18:32** — [S:20260613|W:task218-recoverable-evidence|H:serena/memory|E:.serena/memories/task218-recoverable-closeout-evidence.md] Captured the Task 218 recoverable-evidence Serena memory checkpoint.

## Plan Compliance Checklist
- [x] plan-step-scope — Define alignment prerequisites and scope
- [ ] plan-step-implement — Update workflow/guard/docs and capture tests
- [ ] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
