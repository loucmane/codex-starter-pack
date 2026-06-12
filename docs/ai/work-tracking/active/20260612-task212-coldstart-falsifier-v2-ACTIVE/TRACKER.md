# Task 212 Cold-start falsifier v2: recon-to-decision metric + READY-envelope scenarios Tracker

**Started**: 2026-06-12
**Status**: ACTIVE
**Last Updated**: 2026-06-12

## Goals
- [ ] score_decision: recon-to-correct-decision incl. correctly doing nothing
- [ ] capture_scenario + build_envelope_worktree: forward-captured READY envelopes
- [ ] aggregate/decide v2 with accuracy gating; fresh-null kept
- [ ] aegis coldstart capture CLI + tests/fixtures

## Progress Log
- **2026-06-12 18:49** — [S:20260612|W:task212-coldstart-falsifier-v2|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-06-12 18:49 CEST`
- **2026-06-12 18:49** — [S:20260612|W:task212-coldstart-falsifier-v2|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/TRACKER.md] Scaffolded the Task 212 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-06-12 18:49** — [S:20260612|W:task212-coldstart-falsifier-v2|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 212 in progress and updated only its generated task file
- **2026-06-12 18:49** — [S:20260612|W:task212-coldstart-falsifier-v2|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 212 kickoff
- **2026-06-12 18:53** — [S:20260612|W:task212-coldstart-falsifier-v2|H:aegis_foundation/replay_coldstart.py|E:docs/ai/work-tracking/active/20260612-task212-coldstart-falsifier-v2-ACTIVE/reports/pytest-falsifier-v2.txt] Implemented falsifier v2: score_decision (recon-to-correct-decision incl. correct do-nothing), capture_scenario + READY-envelope worktrees with advisory seed, aggregate_v2/decide_v2 with accuracy gating, aegis coldstart capture CLI; 14 new tests pass; live dogfood capture succeeded.
- **2026-06-12 18:53** — [S:20260612|W:task212-coldstart-falsifier-v2|H:serena/memory|E:.serena/memories/task212-coldstart-falsifier-v2.md] Captured the Task 212 falsifier-v2 Serena memory checkpoint.

## Plan Compliance Checklist
- [x] plan-step-scope — Define alignment prerequisites and scope
- [ ] plan-step-implement — Update workflow/guard/docs and capture tests
- [ ] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
