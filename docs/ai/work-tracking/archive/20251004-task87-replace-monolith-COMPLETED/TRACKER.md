# Task 87 Replace Legacy Monolithic References Tracker

**Started**: 2025-10-04
**Status**: COMPLETED
**Last Updated**: 2025-10-20

## Goals
- [x] Enumerate lingering references to WORKFLOWS.md / PATTERNS.md / BUILDING-BETTER.md
- [x] Map each reference to new modular files (domain workflows, guards, helpers)
- [x] Implement replacements and ensure guard enforcement blocks legacy paths
- [x] Document migration and regression coverage

## Progress Log
- **2025-10-04 21:16 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/HANDOFF.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/HANDOFF.md`] Captured end-of-day handoff with remediation next steps.

- **2025-10-04 19:10 CEST** — [S:20251004|W:task87-replace-monolith|H:reports/domain-workflows/guard-2025-10-04-1909.txt|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/guard-2025-10-04-1909.txt`] Stored guard validation log for legacy replacement sweep.

- **2025-10-04 19:10 CEST** — [S:20251004|W:task87-replace-monolith|H:reports/domain-workflows/tests-2025-10-04-1910.txt|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/tests-2025-10-04-1910.txt`] Captured pytest output (Project baseline).

- **2025-10-04 13:40** — [S:20251004|W:task87-replace-monolith|H:sessions/2025/10/2025-10-04-005-task87-replace-monolith.md|E:files`sessions/2025/10/2025-10-04-005-task87-replace-monolith.md`] Session started for Task 87 legacy replacement.
- **2025-10-04 13:41** — [S:20251004|W:task87-replace-monolith|H:plans/2025-10-04-task87-replace-monolith.md|E:files`plans/2025-10-04-task87-replace-monolith.md`] Task 87 plan created and linked via plans/current.
- **2025-10-04 13:44** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Recorded initial plan/tracker sync for Task 87.
- **2025-10-04 16:51 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/HANDOFF.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/HANDOFF.md`] Work-tracking folder fully scaffolded with standard files.

- **2025-10-04 17:05 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md`] Catalogued primary legacy reference mappings and pending replacements.

- **2025-10-04 17:17 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md`] Expanded inventory to cover registry, matrices, and user guide references.

- **2025-10-04 17:43 CEST** — [S:20251004|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/designs/legacy-inventory.md`] Inventory coverage complete; plan-step-scope marked complete with evidence logged.

- **2025-10-04 17:43 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Synced plan after completing scope inventory.

- **2025-10-04 17:47 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/handlers/operators/git/create-commit-message.md|E:files`templates/handlers/operators/git/create-commit-message.md`] Authored modular commit-message handler and updated metadata inventory entries.


- **2025-10-04 17:49 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Synced plan after authoring commit-message handler.


- **2025-10-04 17:57 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/workflows/examples/common-workflows.md|E:files`templates/workflows/examples/common-workflows.md`] Updated legacy example workflow to align with Codex plan/tracker protocol.


- **2025-10-04 17:57 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Synced plan after refreshing common workflow guidance.


- **2025-10-04 18:23 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/workflows/handlers/intent-handlers.md|E:files`templates/workflows/handlers/intent-handlers.md`] Modernized intent handlers to reference plan/tracker + Taskmaster instead of TodoWrite.


- **2025-10-04 18:23 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after intent handler refresh.


- **2025-10-04 18:24 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/workflows/patterns/task-management.md|E:files`templates/workflows/patterns/task-management.md`] Converted task-management pattern to plan/tracker + Taskmaster guidance.


- **2025-10-04 18:24 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after task-management pattern refresh.


- **2025-10-04 18:26 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/workflows/patterns/multi-agent-orchestration.md|E:files`templates/workflows/patterns/multi-agent-orchestration.md`] Updated multi-agent orchestration pattern to reference plan/tracker + Taskmaster sync.


- **2025-10-04 18:26 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after multi-agent orchestration updates.


- **2025-10-04 19:02 CEST** — [S:20251004|W:task87-replace-monolith|H:CODEX.md|E:files`CODEX.md`] Replaced WORKFLOWS.md/BUILDING-BETTER.md links with modular workflow, convention, and improvement docs.


- **2025-10-04 19:02 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after CODEX reference updates.


- **2025-10-04 19:04 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/HANDLERS.md|E:files`templates/HANDLERS.md`] Remapped handler registry links from WORKFLOWS.md anchors to modular handler files.


- **2025-10-04 19:04 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after handler registry updates.


- **2025-10-04 19:04 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/REGISTRY.md|E:files`templates/REGISTRY.md`] Updated registry links to modular workflow docs.


- **2025-10-04 19:05 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/MATRICES.md|E:files`templates/MATRICES.md`] Remapped matrices entries to modular handlers/workflows.


- **2025-10-04 19:05 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/tools/index.md|E:files`templates/tools/index.md`] Updated tools index link to domain workflow README.


- **2025-10-04 19:05 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/USER-GUIDE.md|E:files`templates/USER-GUIDE.md`] User guide references now point to common-workflows example.


- **2025-10-04 19:05 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/PROJECT-BLOG.md|E:files`templates/PROJECT-BLOG.md`] Project blog links updated to modular workflow overview.


- **2025-10-04 19:05 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after tool/user-guide/project-blog updates.


- **2025-10-04 19:06 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/behaviors/index.md|E:files`templates/behaviors/index.md`] Behavior index now references domain workflow overview.


- **2025-10-04 19:06 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/behaviors/work-tracking/update-tracker.md|E:files`templates/behaviors/work-tracking/update-tracker.md`] Updated tracker behavior link to plan/Taskmaster guidance.


- **2025-10-04 19:06 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after behavior updates.


- **2025-10-04 19:07 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/metadata/template-overview.md|E:files`templates/metadata/template-overview.md`] Replaced monolith entries with modular workflow/pattern sections.


- **2025-10-04 19:07 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/metadata/template-summary.csv|E:files`templates/metadata/template-summary.csv`] Removed monolith rows from template summary.


- **2025-10-04 19:07 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/metadata/template-inventory.txt|E:files`templates/metadata/template-inventory.txt`] Cleared monolith entries from template inventory.


- **2025-10-04 19:07 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after metadata updates.


- **2025-10-04 19:08 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/integration/architecture/template-architecture.md|E:files`templates/integration/architecture/template-architecture.md`] Updated architecture doc to reference modular workflow/improvement sections.


- **2025-10-04 19:08 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/BEHAVIORS.md|E:files`templates/BEHAVIORS.md`] Repointed VOID references to modular resolve-work-void handler.


- **2025-10-04 19:08 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/BUILDING-BETTER.md|E:files`templates/BUILDING-BETTER.md`] Updated internal guidance to modular workflow references.


- **2025-10-04 19:08 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/handlers/orchestrators/work-activity.md|E:files`templates/handlers/orchestrators/work-activity.md`] Routed work-activity orchestrator to modular handler docs.


- **2025-10-04 19:08 CEST** — [S:20251004|W:task87-replace-monolith|H:templates/registry/index.md|E:files`templates/registry/index.md`] Registry index quick link now points to modular workflow example.


- **2025-10-04 19:08 CEST** — [S:20251004|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan sync after architecture/behavior/registry updates.


- **2025-10-09 11:34 CEST** — [S:20251009|W:task87-replace-monolith|H:sessions/2025/10/2025-10-09-001-task87-replace-monolith.md|E:files`sessions/2025/10/2025-10-09-001-task87-replace-monolith.md`] Session resumed; plan sync + guard baseline captured before remediation work.

- **2025-10-09 11:37 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.1 --status=done`] CLI status aligned: 87.1 marked done.
- **2025-10-09 11:37 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.2 --status=done`] CLI status aligned: 87.2 marked done.
- **2025-10-09 11:38 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.3 --status=in-progress`] Implementation subtask set in-progress before remediation.
- **2025-10-09 11:43 CEST** — [S:20251009|W:task87-replace-monolith|H:output/scripts/apply_reference_fixes.py|E:files`output/scripts/apply_reference_fixes.py`] Script reviewed; contains outdated monolith targets (e.g., `templates/PATTERNS.md`), so remediation will proceed manually instead of running it.
- **2025-10-09 11:46 CEST** — [S:20251009|W:task87-replace-monolith|H:scripts/codex-guard|E:cmd`python3 scripts/codex-guard validate --include-untracked`] Guard baseline reconfirmed post-edit.
- **2025-10-09 12:55 CEST** — [S:20251009|W:task87-replace-monolith|H:templates/HANDLERS.md|E:files`templates/HANDLERS.md`] Replaced remaining WORKFLOWS.md anchors across handler registry, meta-routing patterns, matrices, and evidence behaviors with modular targets.
- **2025-10-09 12:57 CEST** — [S:20251009|W:task87-replace-monolith|H:templates/USER-GUIDE.md|E:files`templates/USER-GUIDE.md`] Updated user/integration docs (user guide, registry, conventions, guides, project blog) to reference modular integration guides instead of BUILDING-BETTER/PATTERNS.
- **2025-10-09 12:58 CEST** — [S:20251009|W:task87-replace-monolith|H:templates/WORKFLOWS.md|E:files`templates/WORKFLOWS.md`] Cleaned residual cross-links (system-improvement orchestrator, workflow index) so template suite no longer points at monolith files.
- **2025-10-09 13:00 CEST** — [S:20251009|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Recorded post-update plan sync.
- **2025-10-09 13:00 CEST** — [S:20251009|W:task87-replace-monolith|H:scripts/codex-guard|E:cmd`python3 scripts/codex-guard validate --include-untracked`] Guard passes on documentation sweep.
- **2025-10-09 13:00 CEST** — [S:20251009|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/guard-2025-10-09-1300.txt|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/guard-2025-10-09-1300.txt`] Guard log stored for replacement sweep.
- **2025-10-09 13:01 CEST** — [S:20251009|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/tests-2025-10-09-1301.txt|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/reports/domain-workflows/tests-2025-10-09-1301.txt`] Pytest regression run captured (20 passed).
- **2025-10-09 13:02 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.3 --status=done`] Subtask 87.3 marked complete (manual remediation finished).
- **2025-10-09 13:03 CEST** — [S:20251009|W:task87-replace-monolith|H:scripts/codex-guard|E:files`scripts/codex-guard`] Extended guard to block legacy WORKFLOWS/PATTERNS/BUILDING-BETTER references in templates.
- **2025-10-09 13:04 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.4 --status=done`] Subtask 87.4 (guard update) marked done.
- **2025-10-09 13:04 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.5 --status=done`] Documentation subtask marked done.
- **2025-10-09 13:05 CEST** — [S:20251009|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87.6 --status=done`] Regression subtask marked done (evidence logged).
- **2025-10-09 13:05 CEST** — [S:20251009|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Synced plan/tracker after closing subtasks.
- **2025-10-09 13:06 CEST** — [S:20251009|W:task87-replace-monolith|H:scripts/codex-guard|E:cmd`python3 scripts/codex-guard validate --include-untracked`] Guard passes with monolith enforcement enabled.

- **2025-10-11 14:10 CEST** — [S:20251011|W:task87-replace-monolith|H:sessions/2025/10/2025-10-11-001-task87-replace-monolith.md|E:files`sessions/2025/10/2025-10-11-001-task87-replace-monolith.md`] Follow-up session opened; plan/tracker reviewed.
- **2025-10-11 14:12 CEST** — [S:20251011|W:task87-replace-monolith|H:.plan_state/sync.log|E:cmd`python3 scripts/codex-task plan sync`] Plan/tracker synced for closure work.
- **2025-10-11 14:12 CEST** — [S:20251011|W:task87-replace-monolith|H:scripts/codex-guard|E:cmd`python3 scripts/codex-guard validate --include-untracked`] Guard baseline confirmed (no markdown changes yet).
- **2025-10-11 14:15 CEST** — [S:20251011|W:task87-replace-monolith|H:docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/CHANGELOG.md|E:files`docs/ai/work-tracking/active/20251004-task87-replace-monolith-ACTIVE/CHANGELOG.md`] Logged closure notes; verified plan-step checklist complete.
- **2025-10-11 14:15 CEST** — [S:20251011|W:task87-replace-monolith|H:task-master/set-status|E:cmd`task-master set-status --id=87 --status=done`] Task 87 closed in Task Master.

## Plan Compliance Checklist
- [x] plan-step-scope — Inventory legacy references and targets
- [x] plan-step-implement — Replace references and update guard/tests
- [x] plan-step-verify — Evidence bundle captured, guard/tests passing
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Completed Task 86 outputs provide new domain workflows
- Guard: scripts/codex-guard to enforce migration
