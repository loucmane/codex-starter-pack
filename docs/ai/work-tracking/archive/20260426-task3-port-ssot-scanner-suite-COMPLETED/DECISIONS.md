# Decisions

- 2026-04-26 — Start Task 3 as scanner-suite reconciliation rather than direct source copying from the older FPL MCP path. Current Codex scanner files are the source of truth until a specific gap is proven.
- 2026-04-26 — Complete `plan-step-scope` once stale-baseline boundaries are documented; keep the actual scanner audit and any code changes under `plan-step-implement`.
- 2026-04-26 — Treat FPL MCP as historical context only. The operational authority for Task 3 is the current Codex starter-pack foundation and the scanner behavior required by guard, metadata, template drift, metrics, and portability workflows.
- 2026-04-26 — Implement conservative modular extraction rather than a broad scanner rewrite: `scan_core.py`, `report_generator.py`, and `validation_interface.py` provide explicit seams while preserving current scanner behavior.
- 2026-04-26 — Keep full-run scanner diagnostics non-blocking for noisy known issues like broken references, but make migrated-monolith references fail by default. Configured severities are emitted as report findings for downstream enforcement decisions.
- 2026-04-26 — Do not add parallelism/caching for Task 3; default runtime exclusions and no-checkpoint execution reduce the full runner to about 1.33 seconds and avoid the previous generated-artifact bloat.
