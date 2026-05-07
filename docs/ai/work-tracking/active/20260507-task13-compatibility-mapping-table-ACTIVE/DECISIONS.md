# Decisions

- 2026-05-07 — Keep compatibility resolution inside `scripts/template_registry.py` instead of creating a parallel subsystem. Rationale: Task 8 already established the registry fallback chain and callers should continue using `TemplateRegistry.resolve()`.
- 2026-05-07 — Move the compatibility table into `templates/registry/compatibility-map.json`. Rationale: compatibility mappings are registry data and need versioning/review separate from Python code.
- 2026-05-07 — Reject duplicate legacy keys and duplicate current targets. Rationale: bidirectional lookup must be deterministic; ambiguous reverse mappings should fail during table loading rather than resolve silently.
