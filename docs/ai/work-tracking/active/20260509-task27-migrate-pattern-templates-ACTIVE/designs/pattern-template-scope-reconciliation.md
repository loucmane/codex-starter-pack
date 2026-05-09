# Task 27 Pattern Template Scope Reconciliation

## Context

Task 27 was created from an older migration plan that described extracting a `PATTERNS.md` monolith, creating a pattern index, migrating work-tracking/session patterns, updating fallback discovery, and validating pattern dependencies.

Current repository evidence shows most of that historical scope is already complete:

- `templates/PATTERNS.md` is already a modular legacy entrypoint.
- `templates/patterns/` already contains routing, selection, evidence, work-tracking, session, and integration pattern modules.
- Pattern modules already carry YAML frontmatter with `title`, `type`, `status`, `category`, and dependencies/related metadata where relevant.
- `templates/metadata/template-overview.md`, `template-summary.csv`, and `template-inventory.txt` already list existing pattern modules.
- `scripts/template_registry.py` already has a compatibility-map fallback chain for legacy monolith paths.

## Findings

### Already Satisfied

- Monolith extraction is complete: `templates/PATTERNS.md` is an index, not the source of the pattern body content.
- Work-tracking and session pattern modules exist:
  - `templates/patterns/work-tracking/work-patterns.md`
  - `templates/patterns/work-tracking/progress-patterns.md`
  - `templates/patterns/work-tracking/documentation-patterns.md`
  - `templates/patterns/session/session-patterns.md`
  - `templates/patterns/session/state-patterns.md`
  - `templates/patterns/session/continuation-patterns.md`
- Legacy discovery exists through `templates/registry/compatibility-map.json`.

### Current-State Gaps

1. `templates/registry/compatibility-map.json` redirected `templates/PATTERNS.md` to the bare directory `templates/patterns/`.
   - Evidence: `TemplateRegistry.resolve("templates/PATTERNS.md")` returned a compatibility redirect with `record=None`.
   - Risk: callers receive a target path but no concrete registry record, so metadata, dependency, and search behavior are weaker than other modular families.
2. There was no `templates/patterns/index.md` modular landing page.
   - `templates/PATTERNS.md` existed as a legacy top-level navigation file, but the modular pattern family had no in-family index target.
3. `templates/metadata/template-metadata-policy.json` did not govern `templates/patterns/**/*.md`.
   - Existing pattern modules had metadata, but guard policy did not enforce that it stays valid.

## Decision

Implement the smallest current-state fix:

- Add `templates/patterns/index.md` as the canonical modular pattern-family index.
- Redirect `templates/PATTERNS.md` compatibility mapping to `templates/patterns/index.md`.
- Register the pattern index in `templates/registry/index.json` so the redirect returns a concrete modular record.
- Add a `pattern-templates` metadata-policy rule governing `templates/patterns/**/*.md`.
- Add focused tests proving:
  - the pattern metadata rule matches pattern templates;
  - real governed templates still validate, now including pattern templates;
  - `TemplateRegistry.resolve("templates/PATTERNS.md")` returns the pattern index record.

## Out of Scope

- Rewriting existing pattern modules.
- Renaming pattern files to a new `pattern-workflow-variant.md` convention without current evidence that the existing names are harmful.
- Moving session or work-tracking lifecycle behavior out of the current portable workflow foundation.
- Replacing registry/discovery behavior already covered by Tasks 8, 13, and 25.

## Evidence Plan

- Focused tests:
  - `python3 -m pytest tests/meta_workflow_guard/test_guard_rules.py::test_select_template_metadata_rule_matches_pattern_templates tests/meta_workflow_guard/test_guard_rules.py::test_real_template_frontmatter_schema_accepts_governed_templates tests/meta_workflow_guard/test_template_registry.py::test_real_patterns_compatibility_redirect_resolves_to_index_record`
- Broader focused family:
  - `python3 -m pytest tests/meta_workflow_guard/test_guard_rules.py tests/meta_workflow_guard/test_template_registry.py`
- Guard:
  - `python3 scripts/codex-guard validate --include-untracked`
