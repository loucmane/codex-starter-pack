# Task 46 Create Template Import/Export System – Implementation Notes

## Planned Workstreams
- [x] Add a `template bundle-plan` subcommand to `scripts/codex-task`.
- [x] Use `TemplateRegistry` and `TemplateDiscoveryAPI` for template resolution and dependency discovery.
- [x] Emit deterministic JSON and Markdown artifacts that preview target conflicts without copying or extracting template files.
- [x] Add focused parser and behavior tests in `tests/meta_workflow_guard/test_codex_task.py`.

## Implemented Command

```bash
python3 scripts/codex-task template bundle-plan \
  --template <id-or-path> \
  --target-dir <target-repo> \
  --report-file <manifest.json> \
  --runbook-file <runbook.md>
```

The helper resolves requested templates, recursively includes frontmatter dependencies, records unresolved templates/dependencies, maps template paths into the target repository's configured template root, classifies target status as `identical`, `different`, `missing`, `source-missing`, or `not-checked`, and emits static JSON/Markdown artifacts. It does not copy files, create ZIP archives, extract imports, contact marketplaces, sign bundles, or mutate target repositories.

## Evidence

- Bundle manifest: `reports/template-import-export-system/bundle-plan-2026-05-13.json`
- Bundle runbook: `reports/template-import-export-system/bundle-plan-2026-05-13.md`
- Focused tests: `reports/template-import-export-system/tests-2026-05-13-codex-task.txt`
- Focused codex-task + registry tests: `reports/template-import-export-system/tests-2026-05-13-focused.txt`
- Verification: `reports/template-import-export-system/plan-sync-2026-05-13.txt`, `work-tracking-audit-2026-05-13.txt`, `taskmaster-health-2026-05-13.txt`, `guard-2026-05-13.txt`, and `diff-check-2026-05-13.txt`
