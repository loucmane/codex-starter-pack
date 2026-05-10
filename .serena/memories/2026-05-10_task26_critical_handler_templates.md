# Task 26 Critical Handler Templates

Date: 2026-05-10
Branch: feat/task-26-critical-handler-templates
Session: sessions/2026/05/2026-05-10-004-task26-critical-handler-templates.md
Plan: plans/2026-05-10-task26-critical-handler-templates.md
Work tracking: docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/

## Scope Reconciliation

Task 26 historical wording said to migrate critical handler templates (`start-new-work`, `fix-problem`, `test-implementation`) from monoliths. Current evidence shows handler bodies already exist under `templates/handlers/**` with governed frontmatter. The actual current-state gap is registry/discovery compatibility:

- `templates/HANDLERS.md` redirected to `templates/handlers/` with `record=None`.
- `TemplateRegistry.resolve("start-new-work")`, `resolve("fix-bug")`, and `resolve("create-test-checkpoint")` missed because registry index IDs are path-derived and frontmatter IDs were not aliases.
- Legacy names `fix-problem` and `test-implementation` missed despite current equivalents.
- `templates/matrices/mapping/keyword-to-handler.md` routed keyword `problem` to nonexistent `fix-problem`.

## Implementation

Implemented the scoped fix:

- Added `templates/handlers/index.md` as the modular handler-family landing page.
- Updated `templates/registry/compatibility-map.json` so `templates/HANDLERS.md` redirects to `templates/handlers/index.md`.
- Registered `handlers-index` in `templates/registry/index.json`.
- Added explicit aliases in registry index: `fix-problem` -> `fix-bug`, `test-implementation` -> `create-test-checkpoint`.
- Updated `scripts/template_registry.py` so modular records resolve through frontmatter `id` values and explicit aliases.
- Updated keyword matrix so `problem` routes to `fix-bug`.
- Added focused tests in `tests/meta_workflow_guard/test_template_registry.py`.
- Updated metadata surfaces for `templates/handlers/index.md`.

## Evidence So Far

- `docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/designs/critical-handler-templates-scope-reconciliation.md`
- `docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/reports/critical-handler-templates/tests-2026-05-10-registry-guard.txt` — 82 passed.
- `docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/reports/critical-handler-templates/plan-sync-2026-05-10.txt` — plan sync recorded.

## Remaining

- Log this Serena memory in tracker/session.
- Rerun work-tracking audit.
- Run `python3 scripts/codex-guard validate --include-untracked`.
- Mark subtask 26.2 and parent Task 26 done if final verification passes.
- Capture final handoff, health/diff evidence, commit, and push.