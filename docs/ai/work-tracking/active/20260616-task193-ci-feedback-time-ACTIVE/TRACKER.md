# Task 193 Reduce CI feedback time without reducing coverage Tracker

**Started**: 2026-06-16
**Status**: ACTIVE
**Last Updated**: 2026-06-16

## Goals
- [x] Profile current GitHub Actions jobs; identify slowest stages (only ci.yml runs pytest; pytest is the dominant cost)
- [x] Cut feedback time (pytest-xdist `-n auto --dist loadgroup`) WITHOUT reducing coverage
- [x] Prove coverage preserved (identical test set) + measure before/after (323s→~60s @32c, →103s @4w; 6/6 parallel runs green)

## Progress Log
- **2026-06-16 13:14** — [S:20260616|W:task193-ci-feedback-time|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-06-16 13:14 CEST`
- **2026-06-16 13:14** — [S:20260616|W:task193-ci-feedback-time|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/TRACKER.md] Scaffolded the Task 193 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-06-16 13:14** — [S:20260616|W:task193-ci-feedback-time|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 193 in progress and updated only its generated task file
- **2026-06-16 13:14** — [S:20260616|W:task193-ci-feedback-time|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 193 kickoff
- **2026-06-16** — [S:20260616|W:task193-ci-feedback-time|H:.github/workflows/ci.yml|E:docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/designs/wizard-flow.md] Scope/design: profiled CI (pytest dominates the only pytest job); chose pytest-xdist `-n auto --dist loadgroup`
- **2026-06-16** — [S:20260616|W:task193-ci-feedback-time|H:conftest.py|E:conftest.py] Implement: repo-root conftest isolates git config per worker (fixes latent cross-test gpgsign leak surfaced by xdist)
- **2026-06-16** — [S:20260616|W:task193-ci-feedback-time|H:tests/meta_workflow_guard/test_guard_rules.py|E:tests/meta_workflow_guard/test_guard_rules.py] Implement: pinned guard-rules module to one xdist group (real-repo fixed-path fixtures); added xdist dev dep + ci.yml `-n auto --dist loadgroup`
- **2026-06-16** — [S:20260616|W:task193-ci-feedback-time|H:pytest|E:docs/ai/work-tracking/active/20260616-task193-ci-feedback-time-ACTIVE/reports/task193-ci-feedback-time/tests-2026-06-16-final.txt] Verify: serial 1688 green; 6/6 `-n auto` runs green (323s→~60s @32c, →103s @4w); coverage unchanged
- **2026-06-16** — [S:20260616|W:task193-ci-feedback-time|H:serena/memory|E:.serena/memories/task193-ci-feedback-time.md] Captured Task 193 Serena memory.
- **2026-06-16** — [S:20260616|W:task193-ci-feedback-time|H:.aegis/brief.json|E:.aegis/brief.json] Accounted the new root `conftest.py` in witness `always_in_scope` (PR #238 aegis-witness diff_accounting flagged it); witness PASS locally.

## Plan Compliance Checklist
- [x] plan-step-scope — Profiled CI; pytest is the dominant cost; chose xdist `-n auto --dist loadgroup`
- [x] plan-step-implement — xdist dep + ci.yml flag + conftest git isolation + guard-rules xdist_group
- [x] plan-step-verify — Serial + 6× parallel green; speedup measured; coverage preserved; evidence stored
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
