# Task 29 Create Template Lifecycle Management – Implementation Notes

## Planned Workstreams
- Scope reconciliation: completed in `designs/template-lifecycle-scope-reconciliation.md`.
- Lifecycle policy: add a repo-local policy file under `templates/metadata/` for states, compatibility mappings, transition rules, and deprecation thresholds.
- Lifecycle helper: add an audit-only Python module for transition validation, semantic version bumping, warnings, migration notices, and archival recommendations.
- Schema fields: extend template frontmatter schema to include lifecycle metadata needed by the helper.
- Evidence: capture focused lifecycle tests, registry/guard metadata tests, full pytest, plan sync, audit, guard, and diff-check.

## Implemented Lifecycle Contract
- Added `templates/metadata/template-lifecycle-policy.json` with canonical states, compatibility status mappings, transition rules, deprecation thresholds, and version bump levels.
- Added `scripts/template_lifecycle.py` as an audit-only helper for policy loading, transition validation, semantic version bumping, registry lifecycle audits, and deprecated-template warnings.
- Extended `templates/metadata/template-frontmatter.schema.json` with `review` and `archived` statuses plus lifecycle fields: `deprecated_since`, `archive_after`, `replacement`, and `migration_notice`.
- Added lifecycle metadata to `templates/behaviors/session/compaction-detection.md`, the existing deprecated tombstone.
- Added `tests/meta_workflow_guard/test_template_lifecycle.py` for policy loading, transition rules, semver bumps, deprecation thresholds, schema lifecycle fields, ignored aggregate statuses, and real registry lifecycle audits.

## Initial Verification
- Focused lifecycle tests: `10 passed`.
- Focused lifecycle/registry/metadata guard selection: `38 passed`.
- Lifecycle audit: `Template lifecycle audit: 221 records, 0 issue(s)`.

## Evidence
- `reports/template-lifecycle-management/tests-2026-05-08-lifecycle.txt` - focused lifecycle tests, `10 passed`.
- `reports/template-lifecycle-management/tests-2026-05-08-lifecycle-registry-guard.txt` - lifecycle, registry, and metadata guard selection, `38 passed`.
- `reports/template-lifecycle-management/lifecycle-audit-2026-05-08.txt` - lifecycle audit, `221 records, 0 issue(s)`.
- `reports/template-lifecycle-management/tests-2026-05-08-full-pytest.txt` - full pytest, `334 passed`.
- `reports/template-lifecycle-management/taskmaster-health-2026-05-08.txt` - Taskmaster full-graph health.
- `reports/template-lifecycle-management/plan-sync-2026-05-08.txt` - plan/tracker sync.
- `reports/template-lifecycle-management/work-tracking-audit-2026-05-08.txt` - active work-tracking audit.
- `reports/template-lifecycle-management/guard-2026-05-08.txt` - guard validation.
- `reports/template-lifecycle-management/diff-check-2026-05-08.txt` - whitespace diff check.
- `.serena/memories/2026-05-08_task29_template_lifecycle_management.md` - Serena continuity memory.
