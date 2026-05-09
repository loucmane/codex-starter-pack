# Task 27 - Migrate Pattern Templates Kickoff

Date: 2026-05-09
Branch: feat/task-27-migrate-pattern-templates
Taskmaster: Task 27 in progress; 27.1 scope reconciliation completed; 27.2 implementation in progress.

Key findings:
- Historical Task 27 wording was stale: PATTERNS.md had already been modularized into templates/patterns/.
- Current concrete gaps were discovery/enforcement gaps, not a need to rewrite pattern modules.
- TemplateRegistry.resolve("templates/PATTERNS.md") redirected to templates/patterns/ with record=None before this task.
- templates/metadata/template-metadata-policy.json did not govern templates/patterns/**/*.md even though pattern modules already had frontmatter.

Implementation direction:
- Add templates/patterns/index.md as the canonical modular pattern-family index.
- Redirect compatibility-map entry for templates/PATTERNS.md to templates/patterns/index.md.
- Register patterns-index in templates/registry/index.json.
- Add pattern-templates metadata-policy rule.
- Add focused tests for metadata rule selection and concrete compatibility redirect record.

Evidence so far:
- Scope doc: docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/designs/pattern-template-scope-reconciliation.md
- Focused broader tests: 79 passed in docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/reports/pattern-template-migration/tests-2026-05-09-pattern-policy-registry.txt
