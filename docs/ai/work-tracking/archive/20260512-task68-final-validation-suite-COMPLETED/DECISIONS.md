# Decisions

- 2026-05-12 — Implement Task 68 as `python3 scripts/codex-task validation final-suite`, an orchestrator over existing validators. Do not create parallel security, performance, cost, reference, or compatibility engines. The suite will provide dry-run planning, execute mode, per-check evidence logs, JSON summary, Markdown sign-off runbook, and explicit failure behavior.
- 2026-05-12 — Keep generated telemetry/report outputs task-scoped when the final suite runs by passing report directories under the suite evidence folder. This prevents final validation from dirtying repo-level `reports/latest` files while still preserving complete report evidence for review.
