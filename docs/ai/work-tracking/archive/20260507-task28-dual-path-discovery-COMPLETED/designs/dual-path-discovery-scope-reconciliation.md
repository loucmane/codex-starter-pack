# Task 28 Dual-Path Discovery Scope Reconciliation

**Captured**: 2026-05-07 17:05 CEST  
**Task**: 28 - Implement Dual-Path Discovery

## Historical Task Wording

Task 28 originally asks for a fallback system for template discovery during migration:

- modular check
- compatibility map lookup
- legacy monolith search
- Serena semantic search
- error with suggestions
- fallback logging, path metrics, circuit breakers, cache warming, and discovery hints

That wording is migration-era context. Per the Task 4 backlog-alignment audit, old backlog tasks must be reconciled against the current repository and portable foundation before implementation.

## Current Repository Evidence

The current repository already has the core discovery chain in `scripts/template_registry.py`:

- `TemplateRegistry.resolve()` checks exact modular registry IDs from `templates/registry/index.json`.
- It then checks direct modular paths.
- It redirects legacy template paths through the Task 13 JSON-backed compatibility map.
- It can still resolve an existing legacy markdown file as a legacy record.
- It returns a typed Serena fallback action when local lookup misses and `allow_serena=True`.
- It raises or returns a clear error when local lookup misses and Serena fallback is disabled.
- Existing tests already cover the basic resolution order: modular, compatibility, legacy, Serena fallback, and strict error.

Task 8 established the portable registry API. Task 13 made the compatibility map durable and bidirectional. Task 21 made template frontmatter metadata schema validation durable. The current foundation spec requires portable, config-driven behavior and discourages parallel subsystems when existing core logic can be extended.

## Current Gap

Task 28 remains valid, but not as a new discovery subsystem. The proven current-state gap is that discovery decisions are not observable or helpful enough for callers:

- callers cannot inspect per-path usage metrics after resolution;
- `ResolutionResult` does not expose the discovery path taken as a structured trace;
- misses do not provide local suggestions or hints;
- Serena fallback is represented, but there is no visible distinction between a normal fallback and disabled/unavailable semantic fallback beyond the basic source/action fields;
- cache warming exists implicitly through lookup calls and TTL caching, but there is no explicit helper for common lookups;
- fallback/circuit-breaker language should be interpreted conservatively as local fallback observability, not a runtime dependency on a live Serena service.

## Reconciliation Decision

Implement Task 28 by extending the existing registry runtime:

- keep `TemplateRegistry.resolve()` as the single discovery API;
- add structured discovery traces and suggestions to `ResolutionResult`;
- add in-memory path usage metrics owned by each registry instance;
- add an explicit cache-warming helper for common IDs/paths;
- add lightweight local circuit-breaker semantics only for optional fallback hooks, if a hook is introduced;
- keep Serena as an operator/MCP fallback action, not an in-process dependency;
- keep all behavior portable through `load_repo_structure()`.

Do not create a second discovery engine, background service, persistent metrics database, live Serena integration, or migration-era monolith scanner in Task 28.

## Implementation Boundary

Expected code surface:

- `scripts/template_registry.py`
- `tests/meta_workflow_guard/test_template_registry.py`
- Task 28 work-tracking evidence under `reports/dual-path-discovery/`

Expected behavior:

- resolution result reports which discovery path fired;
- registry exposes snapshot/reset methods for discovery metrics;
- cache warming can resolve a list of common queries without failing the whole warmup on misses;
- misses include deterministic local suggestions from IDs, paths, titles, tags, or compatibility keys;
- existing modular, compatibility, legacy, Serena fallback, and strict-error behavior stays backward compatible.

## Acceptance

Task 28 is complete when:

- focused tests prove modular, compatibility, legacy, Serena fallback, and error paths still resolve in order;
- tests prove discovery metrics increment per path;
- tests prove cache warming records successes/failures without changing resolver semantics;
- tests prove local miss suggestions are deterministic and useful;
- `plan sync`, work-tracking audit, `codex-guard validate --include-untracked`, focused pytest, and `git diff --check` pass;
- Taskmaster subtasks 28.1 and 28.2 and parent Task 28 are marked done with targeted generated-file refresh.
