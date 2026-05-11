# Findings

- 2026-05-11 — Current repository evidence shows agent runtimes exist independently (`CODEX.md`, `.claude/`, canary rollout stages), but there is no machine-readable matrix that validates recognized agents, runtime contract versions, feature support, fallback expectations, transformations, and compatibility metrics.
- 2026-05-11 — Historical agent integration docs still describe older `.claude/agents/` layouts that do not match the current Claude runtime adapter; Task 62 should point future agent additions at the new compatibility matrix rather than preserving stale prose as the source of truth.
