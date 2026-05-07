# Task 21 Frontmatter Schema Scope Reconciliation

## Current-State Findings

- Task 91 already established the portable metadata baseline: `title`, `type`, and `status`.
- `templates/metadata/template-metadata-policy.json` already scopes metadata enforcement by repo-local include/exclude policy.
- `scripts/codex-guard` already enforces required keys for governed template documents through `validate_template_metadata()`.
- Existing enforcement is intentionally policy-driven and cross-project aware through `.codex/config.toml` repo-structure roots.
- Existing enforcement is not yet schema-backed: frontmatter is parsed as simple strings, lists are not typed, and values such as `status` are not validated against a contract.

## Scope Decision

Task 21 should not batch-rewrite every template or create a parallel frontmatter subsystem. The current proven gap is to make the existing metadata policy enforcement schema-backed and typed.

Implementation should:

- add a permanent template frontmatter JSON Schema contract under `templates/metadata/`
- keep `template-metadata-policy.json` as the repo-local scope and rollout control
- teach `scripts/codex-guard` to parse YAML frontmatter with the existing PyYAML dependency
- validate governed template frontmatter against the schema before checking required policy keys
- preserve family-specific extension fields by allowing additional properties unless the policy later tightens them
- keep existing Task 91 rollout boundaries intact

## Out of Scope

- broad template frontmatter migration across all `templates/**`
- replacing `TemplateRegistry.parse_frontmatter()` unless registry behavior requires it later
- adding a separate migration/generator CLI before the schema-backed validation gap is proven
- requiring historical Taskmaster fields like `dependencies`, `triggers`, and `exports` for every governed template immediately

## Evidence Links

- `templates/engine/core/portable-foundation-spec.md`
- `templates/metadata/template-metadata-policy.json`
- `docs/ai/work-tracking/archive/20260421-task91-standardize-template-metadata-COMPLETED/designs/template-metadata-schema.md`
- `scripts/codex-guard`

