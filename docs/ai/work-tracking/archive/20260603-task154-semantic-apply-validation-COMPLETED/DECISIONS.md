# Decisions

- 2026-06-03 — _Pending_ — capture decisions with context.
- 2026-06-03 — Keep path and semantic gates as separate verdicts — path validation still catches unexpected files/modes/symlinks, while semantic validation catches unexpected content changes inside expected aggregate files.
- 2026-06-03 — Canonicalize both sides before diffing — Taskmaster's number-to-string ID/dependency normalization and version-scoped structural defaults are factored out before asserting only the target status changed.
- 2026-06-03 — Treat semantic drift as rollback-worthy — a test-enabled live write that changes the right files but the wrong content now rolls back and reports `live_semantic_delta_mismatch`.
