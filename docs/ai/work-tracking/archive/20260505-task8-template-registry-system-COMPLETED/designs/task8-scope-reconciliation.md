# Task 8 Scope Reconciliation

## Current Evidence

- `templates/registry/index.json` exists and currently contains 99 static entries. Entries expose only `id`, `path`, `tags`, and either `goodFirstHandler` or `goodFirstWorkflow`.
- `templates/registry/index.md` is a human navigation index, not a reusable lookup API.
- `templates/metadata/template-summary.csv`, `templates/metadata/template-inventory.txt`, and `templates/metadata/template-overview.md` provide generated discovery surfaces with richer file metadata, but no runtime registry class.
- `templates/metadata/template-metadata-policy.json` defines the enforced frontmatter policy by path family.
- `scripts/codex-guard` has frontmatter parsing and metadata validation helpers, but those are embedded in guard enforcement rather than exposed as a registry/search abstraction.
- `scripts/template-ssot-scanner/scanner.py` extracts heading and reference metadata for scanner outputs, but it does not parse canonical YAML frontmatter into a reusable registry index.
- `scripts/_repo_structure.py` is the portability boundary. New registry code must derive the templates root from `load_repo_structure()` instead of hardcoding repository paths.
- Existing tests validate static registry/metadata surfaces, but there are no tests for a `TemplateRegistry` API, cache behavior, search, or fallback resolution.

## Reconciliation Decision

Task 8 is still valid, but the implementation should be narrower and current-state based:

- Do not regenerate or replace the existing static registry surfaces during the scope step.
- Do not treat Taskmaster's historical wording as a mandate to rebuild the whole template system.
- Implement the missing reusable registry API over existing files and policy surfaces.
- Keep the registry portable by using configured roots from `_repo_structure.py`.
- Treat Serena as an external operator fallback, not an in-process dependency. The registry can return a typed `serena_search` fallback candidate, while an agent or MCP caller performs the actual search.

## Proven Gap

The repository has registry data, metadata summaries, and guard validation, but it lacks a centralized `TemplateRegistry` class that callers can use for:

- loading registry entries from the configured templates root
- parsing frontmatter from template markdown files
- searching by id, type, category, tags, and text terms
- resolving template identifiers through a deterministic fallback chain
- caching index builds with TTL and explicit invalidation
- testing discovery performance and fallback behavior without relying on manual `rg`

## Implementation Boundary For 8.2

Expected code surface:

- Add a small registry module, likely `scripts/template_registry.py`.
- Add focused tests, likely `tests/meta_workflow_guard/test_template_registry.py`.
- Reuse `scripts/_repo_structure.py` for root configuration.
- Read `templates/registry/index.json` as the modular registry source.
- Parse YAML-style frontmatter from markdown files with a local lightweight parser or a shared helper if a clean helper already exists.
- Provide cache invalidation and TTL behavior without committing runtime output files.

Expected behavior:

- Exact id lookup prefers `templates/registry/index.json`.
- Compatibility lookup maps known legacy monolith names such as `REGISTRY.md`, `HANDLERS.md`, `WORKFLOWS.md`, `PATTERNS.md`, and `BUILDING-BETTER.md` to modular/current surfaces where the repository already documents a replacement.
- Legacy path lookup can still resolve an existing file under the configured templates root.
- Serena fallback should be represented as a structured fallback action when local registry or legacy lookup cannot resolve an identifier.
- Final miss should return or raise a clear error, depending on the API shape chosen in implementation.

## Verification Boundary

Focused tests should cover:

- portable root handling with a temporary repo structure
- frontmatter parsing for id, type, status, category, and tags
- search by id, type, category, and tags
- fallback order: modular registry, compatibility map, legacy file, Serena fallback, error
- cache hit, TTL refresh, and explicit invalidation
- performance target for warm lookup/search, using deterministic local fixtures rather than broad filesystem timing

