# Task 61 Implement Template Discovery Optimization – Implementation Notes

## 2026-05-11 - Registry Discovery Optimization

Implemented a narrow `TemplateRegistry` index-construction optimization:

- `TemplateRegistry._build_index()` now passes paths already loaded from `templates/registry/index.json` into fallback markdown discovery.
- `TemplateRegistry._discover_markdown_records()` skips those modular paths before reading/parsing frontmatter.
- Existing behavior is preserved: modular records still win, unregistered markdown templates are still discovered, and the final record count remains 261 on the current repository.
- Added `test_registry_skips_modular_paths_during_markdown_discovery()` to prove modular markdown files are not reparsed when fallback discovery scans the template tree.

Measured effect:

- Before: 362 frontmatter calls, 261 unique paths, 101 duplicate frontmatter paths.
- After: 261 frontmatter calls, 261 unique paths, 0 duplicate frontmatter paths.
- Focused registry cold samples after implementation: median `0.025243s`, max `0.025753s`, 261 records.

Evidence:

- `reports/template-discovery-optimization/registry-profile-baseline-2026-05-11.txt`
- `reports/template-discovery-optimization/registry-profile-after-2026-05-11.txt`
- `reports/template-discovery-optimization/registry-cold-baseline-samples-2026-05-11.txt`
- `reports/template-discovery-optimization/registry-cold-after-samples-2026-05-11.txt`
- `reports/template-discovery-optimization/tests-registry-focused-2026-05-11.txt`
