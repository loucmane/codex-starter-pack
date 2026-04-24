# Task 98 Externalize Repo Structure Configuration Tracker

**Started**: 2026-04-24
**Status**: ACTIVE
**Last Updated**: 2026-04-24

## Goals
- [ ] Define the repo-structure configuration contract and hardcoded-path inventory
- [ ] Implement repo-local path loading across the workflow scripts
- [ ] Verify guard integration, documentation, and regression coverage

## Progress Log
- **2026-04-24 18:45** — [S:20260424|W:task98-externalize-repo-structure-config|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-04-24 18:45 CEST`
- **2026-04-24 18:45** — [S:20260424|W:task98-externalize-repo-structure-config|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/TRACKER.md] Scaffolded the Task 98 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-04-24 18:45** — [S:20260424|W:task98-externalize-repo-structure-config|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 98 in progress and regenerated the task files
- **2026-04-24 18:45** — [S:20260424|W:task98-externalize-repo-structure-config|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 98 kickoff
- **2026-04-24 18:45** — [S:20260424|W:task98-externalize-repo-structure-config|H:serena/memory|E:.serena/memories/2026-04-24_task98_repo_structure_config_kickoff.md] Stored Serena memory `2026-04-24_task98_repo_structure_config_kickoff` covering the kickoff state and baseline rewrite requirement
- **2026-04-24 18:45** — [S:20260424|W:task98-externalize-repo-structure-config|H:docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/designs/repo-structure-config-contract.md|E:docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/designs/repo-structure-config-contract.md] Replaced the generic wizard scope with the Task 98 repo-structure configuration contract and path inventory
- **2026-04-24 18:59** — [S:20260424|W:task98-externalize-repo-structure-config|H:templates/TOOLS.md|E:.codex/config.toml] Documented the new `[repo_structure]` contract in the shared tooling docs so repo-local path overrides are part of the foundation guidance
- **2026-04-24 18:59** — [S:20260424|W:task98-externalize-repo-structure-config|H:templates/engine/core/codex-readiness.md|E:.codex/config.toml] Updated the readiness checklist to require reviewing `[repo_structure]` before using the workflow scripts in alternate repo layouts
- **2026-04-24 19:02** — [S:20260424|W:task98-externalize-repo-structure-config|H:pytest|E:docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/reports/repo-structure-config/tests-2026-04-24-repo-structure.txt] Focused regression suite passed for the repo-structure loader, task helper, metrics dashboard, and guard rules
- **2026-04-24 19:02** — [S:20260424|W:task98-externalize-repo-structure-config|H:scripts/codex-guard|E:docs/ai/work-tracking/active/20260424-task98-externalize-repo-structure-config-ACTIVE/reports/repo-structure-config/guard-2026-04-24-pass.txt] Guard validation passed after normalizing the stale Task 96 plan conflict and syncing the Task 98 plan
- **2026-04-24 19:02** — [S:20260424|W:task98-externalize-repo-structure-config|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 98 done after storing the verification evidence

## Plan Compliance Checklist
- [x] plan-step-scope — Inventory hardcoded repo-layout assumptions and define the config contract
- [x] plan-step-implement — Add repo-structure loading across the workflow scripts
- [x] plan-step-verify — Evidence stored, regression suite captured, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
