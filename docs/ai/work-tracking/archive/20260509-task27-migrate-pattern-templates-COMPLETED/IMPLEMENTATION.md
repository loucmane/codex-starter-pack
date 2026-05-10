# Task 27 Migrate Pattern Templates – Implementation Notes

## Planned Workstreams
- Scope reconciliation: compare historical Task 27 wording against the current portable foundation and avoid remigrating already-modular pattern content.
- Pattern index/discovery: add `templates/patterns/index.md`, update `templates/registry/compatibility-map.json`, and register the index in `templates/registry/index.json`.
- Metadata enforcement: add a `pattern-templates` rule to `templates/metadata/template-metadata-policy.json`.
- Metadata surfaces: update `templates/metadata/template-inventory.txt`, `template-summary.csv`, and `template-overview.md` for the new pattern index.
- Tests/evidence: add focused tests for policy matching and real compatibility redirect behavior, then capture pytest/guard/audit evidence under `reports/pattern-template-migration/`.

## Scope Boundary
- Do not rewrite existing pattern modules unless a test or registry check proves a current defect.
- Do not rename the pattern family to a new convention without evidence that the current names break discovery.
- Keep implementation aligned with existing portable registry and metadata-policy mechanisms.

## Implemented
- Added `templates/patterns/index.md` with canonical links to all modular pattern families.
- Updated `templates/registry/compatibility-map.json` so `templates/PATTERNS.md` redirects to `templates/patterns/index.md`.
- Registered `patterns-index` in `templates/registry/index.json`.
- Added `pattern-templates` to `templates/metadata/template-metadata-policy.json`.
- Updated metadata surfaces for the new pattern index.
- Added focused tests for policy selection and real compatibility redirect behavior.
