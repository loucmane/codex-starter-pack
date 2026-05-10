# Task 26 Critical Handler Templates Scope Reconciliation

## Context

Task 26 was created from older migration wording that assumed critical handler content still needed extraction from monolithic files. The historical task names three critical handlers:

- `start-new-work`
- `fix-problem`
- `test-implementation`

Current repository evidence shows the handler family is already mostly modular:

- `templates/handlers/triggers/development/start-new-work.md` exists with governed frontmatter.
- `templates/handlers/triggers/debug/fix-bug.md` exists with governed frontmatter and is the current canonical bug-fix handler.
- `templates/handlers/triggers/test/create-test-checkpoint.md` and `templates/handlers/triggers/test/validate-changes.md` exist with governed frontmatter and cover the current testing workflow.
- `templates/registry/handlers/triggers-registry.md`, `templates/REGISTRY.md`, `templates/workflows/handlers/intent-handlers.md`, and metadata surfaces already list the current handler files.
- `templates/metadata/template-metadata-policy.json` already enforces frontmatter on `templates/handlers/**/*.md`.

## Evidence

Read-only inspection on 2026-05-10 found:

- `TemplateRegistry.resolve("templates/HANDLERS.md", allow_serena=False)` returns a compatibility redirect to `templates/handlers/`, but `record=None`.
- `TemplateRegistry.resolve("start-new-work", allow_serena=False)` misses and only suggests `handlers-triggers-development-start-new-work`.
- `TemplateRegistry.resolve("fix-bug", allow_serena=False)` misses and only suggests `handlers-triggers-debug-fix-bug`.
- `TemplateRegistry.resolve("fix-problem", allow_serena=False)` misses and only suggests `handlers-triggers-debug-fix-bug`.
- `TemplateRegistry.resolve("test-implementation", allow_serena=False)` misses and suggests the current testing handlers.
- `templates/matrices/mapping/keyword-to-handler.md` still maps keyword `problem` to legacy `fix-problem`.

## Findings

### Already Satisfied

- The critical handler content is no longer trapped in a monolith.
- The current canonical handler files exist and pass the metadata policy.
- The modular trigger registry lists `start-new-work`, `fix-bug`, `create-test-checkpoint`, and `validate-changes`.

### Current-State Gaps

1. `templates/HANDLERS.md` compatibility lookup redirects to a bare directory instead of a concrete modular index record.
   - Risk: callers get a path but no metadata-bearing registry record.
2. Registry lookup does not resolve handler frontmatter IDs when the registry index uses path-derived IDs.
   - Risk: natural handler IDs like `start-new-work` and `fix-bug` do not load directly.
3. Legacy aliases from the old migration wording are not mapped.
   - Risk: `fix-problem` and `test-implementation` remain unresolved even though current equivalents exist.
4. The keyword matrix still points `problem` at `fix-problem`.
   - Risk: routing documentation sends users to a nonexistent handler ID.

## Decision

Implement the smallest current-state fix:

- Add `templates/handlers/index.md` as the canonical modular handler-family index.
- Redirect `templates/HANDLERS.md` compatibility mapping to `templates/handlers/index.md`.
- Register the handler index in `templates/registry/index.json`.
- Teach `TemplateRegistry` to resolve metadata IDs and explicit aliases for modular records.
- Add explicit aliases for the legacy names:
  - `fix-problem` -> `templates/handlers/triggers/debug/fix-bug.md`
  - `test-implementation` -> `templates/handlers/triggers/test/create-test-checkpoint.md`
- Update the keyword matrix so `problem` routes to the canonical `fix-bug` handler.
- Add focused tests proving:
  - modular registry records can resolve through frontmatter IDs and aliases;
  - real critical handler names and legacy aliases resolve to concrete handler files;
  - `templates/HANDLERS.md` redirects to the handler index record;
  - governed template metadata remains valid.

## Out of Scope

- Rewriting existing handler bodies without a failing test or broken reference.
- Creating new handler files named `fix-problem.md` or `test-implementation.md`; those are compatibility aliases, not the current canonical model.
- Replacing the existing trigger/orchestrator/operator registry family.
- Changing the broader compatibility-map schema beyond path redirects in this task.

## Evidence Plan

- Focused registry tests:
  - `python3 -m pytest tests/meta_workflow_guard/test_template_registry.py::test_registry_resolves_frontmatter_id_and_explicit_aliases_for_modular_records tests/meta_workflow_guard/test_template_registry.py::test_real_critical_handler_queries_resolve tests/meta_workflow_guard/test_template_registry.py::test_real_handlers_compatibility_redirect_resolves_to_index_record`
- Metadata validation:
  - `python3 -m pytest tests/meta_workflow_guard/test_guard_rules.py::test_real_template_frontmatter_schema_accepts_governed_templates`
- Final guard:
  - `python3 scripts/codex-guard validate --include-untracked`
