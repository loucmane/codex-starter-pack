# Task 43 Scope Reconciliation - Template Testing Framework

## Current Task Text

Task 43 asks for a comprehensive template testing framework:

- `TemplateTestCase` base class
- template execution mocking
- template behavior assertions
- fixture system for test data
- coverage tracking for templates
- mutation testing
- benchmark suite
- visual regression testing for UI templates

## Current Repository Reality

This repository is a portable workflow/template foundation. The templates are Markdown instructions, metadata documents, engine docs, registry entries, and workflow conventions. They are not executable UI templates and there is no service runtime or browser-rendered template surface to run visual regression against.

Existing evidence already covers several adjacent surfaces:

- `scripts/template_registry.py` provides template discovery, registry lookup, search, compatibility redirects, dependency extraction, and serializable discovery API responses.
- `tests/meta_workflow_guard/test_template_registry.py` already uses repeated fixture helpers for repo config, template docs, registry indexes, and compatibility maps.
- `tests/meta_workflow_guard/cross_project_fixtures.py` provides portable repo-shape fixtures, but not template-specific assertions.
- `scripts/codex-guard` and related tests validate metadata policy compliance.
- Task 20 CI now runs Python tests in GitHub Actions.

## Scope Decision

Implement a reusable Python template-testing helper instead of production-style template execution infrastructure.

Chosen implementation target:

- Add `scripts/template_testing.py`.
- Provide a `TemplateTestCase` helper class for tests that need portable template fixtures.
- Provide fixture helpers for repo config, Markdown templates, registry indexes, and compatibility maps.
- Provide assertion helpers over `TemplateRegistry` and `TemplateDiscoveryAPI`.
- Provide lightweight mock rendering for `{{ placeholder }}` style template snippets, enough for behavior tests without executing agent workflows.
- Provide registry coverage reporting so tests can assert fixture templates are registered and registry paths exist.
- Add focused tests under `tests/meta_workflow_guard/test_template_testing.py`.

## Out Of Scope

The following historical Task 43 terms are not implemented in this repository task:

- UI visual regression testing.
- Browser screenshots.
- Benchmark suites.
- Mutation testing.
- Production template execution engines.
- External rendering or test services.

Those features only make sense when a target product has actual executable templates or UI output. This foundation currently needs portable, deterministic test helpers for Markdown template contracts.

## Acceptance Criteria

- Template fixture helpers work with configured `templates_root`, not only this repo's default `templates/` root.
- Assertions can prove registered template lookup, search, dependencies, and compatibility resolution.
- Coverage reporting flags unregistered Markdown fixtures and missing registry paths.
- Mock rendering substitutes known placeholders and reports unresolved placeholders deterministically.
- Focused tests cover success and failure behavior.
- Full pytest, plan sync, work-tracking audit, guard, and diff-check evidence are captured before Task 43 closes.
