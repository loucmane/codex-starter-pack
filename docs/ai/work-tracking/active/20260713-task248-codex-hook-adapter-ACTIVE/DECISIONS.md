# Decisions

- 2026-07-13 — Treat canonical `apply_patch` as one atomic mutation. Preserve every path
  and operation while selecting the first affected path only as the primary evidence
  pointer.
- 2026-07-13 — Fail closed on malformed patch structure in strict mode and record the
  would-block decision in advisory mode. Never guess at partially parseable patches.
- 2026-07-13 — Reuse the shared `.claude/scripts` runtime for Codex dispatch rather than
  fork policy logic. Codex-only installation is independent of the Claude adapter, while
  source/package parity remains mechanically testable.
- 2026-07-13 — Manage `.codex/hooks.json` only when absent or semantically identical.
  Existing divergent content is owner-controlled and requires manual review.
- 2026-07-13 — Keep exact hook-hash approval attended and client-owned. Neither installer,
  update, smoke tests, nor Blog rollout may bypass `/hooks` trust.
- 2026-07-13 — Preserve the out-of-worktree ledger model. The smoke grants an isolated
  writable XDG state root instead of weakening storage architecture for the test.
