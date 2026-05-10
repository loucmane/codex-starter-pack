# Task 26 Migrate Critical Handler Templates – Implementation Notes

## Planned Workstreams
- Scope reconciliation: compare historical Task 26 migration wording against the current modular handler state.
- Handler-family discovery: add a concrete modular handler index and make the `templates/HANDLERS.md` compatibility redirect return a registry record.
- Registry aliasing: allow modular records to resolve through frontmatter `id` values and explicit legacy aliases.
- Critical handler routing: map legacy `fix-problem` and `test-implementation` names to current canonical handlers, and clean the keyword matrix.
- Verification: add focused registry tests and run guard-rule metadata coverage.

## Implemented
- Added `templates/handlers/index.md` as the canonical modular handler-family landing page.
- Updated `templates/registry/compatibility-map.json` so `templates/HANDLERS.md` redirects to `templates/handlers/index.md`.
- Registered `handlers-index` in `templates/registry/index.json`.
- Added explicit critical-handler aliases in `templates/registry/index.json`:
  - `fix-problem` -> `templates/handlers/triggers/debug/fix-bug.md`
  - `test-implementation` -> `templates/handlers/triggers/test/create-test-checkpoint.md`
- Updated `scripts/template_registry.py` so modular records are also indexed by frontmatter `id` and explicit aliases.
- Updated `templates/matrices/mapping/keyword-to-handler.md` so keyword `problem` routes to canonical `fix-bug`.
- Updated metadata surfaces for the new handler index.
- Added focused tests in `tests/meta_workflow_guard/test_template_registry.py`.

## Verification
- `python3 -m pytest tests/meta_workflow_guard/test_template_registry.py tests/meta_workflow_guard/test_guard_rules.py`
  - Evidence: `reports/critical-handler-templates/tests-2026-05-10-registry-guard.txt`
  - Result: 82 passed.
