# Task 21 Template Frontmatter Schema – Implementation Notes

## Planned Workstreams
- Scope reconciliation: complete. Task 91 already owns the portable `title` / `type` / `status` rollout and policy-driven enforcement; Task 21 focuses on the missing schema-backed validation layer.
- Schema contract: complete. Added `templates/metadata/template-frontmatter.schema.json` with typed optional fields and status enum validation while allowing family-specific extension keys.
- Policy integration: complete. `templates/metadata/template-metadata-policy.json` now points governed rules at the schema through the defaults block.
- Guard integration: complete. `scripts/codex-guard` now parses YAML frontmatter through PyYAML, loads the configured schema through `jsonschema`, reports normalized schema violations, and still applies policy-required key checks.
- Tests: focused guard tests passed with `66 passed`.
