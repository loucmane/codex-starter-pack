# Findings

- 2026-07-13 — The documented ledger store is already keyed by Git common directory,
  but the v1 event schema has no repository identity, worktree-root, HEAD, or
  `parent_agent_id` column. Asset/store sharing and attribution completeness must be
  measured separately.
- 2026-07-13 — Two real linked worktrees resolved the same repository identity, managed
  asset digests, and ledger path. All 10,159 pre-teardown event IDs remained visible
  after both worktrees and branches were removed normally; the store is not the source
  of the observed evidence loss.
- 2026-07-13 — With writable temporary client state, Claude 2.1.207 recorded a real
  `general-purpose` child Write and child pytest Bash call. The rows contain branch,
  child `agent_id`, and `agent_type`, but omit repository identity, worktree root, HEAD,
  and `parent_agent_id`. The pytest call is typed as mutation, and the expected missing
  Read emitted no failure row.
- 2026-07-13 — With the inherited read-only home state, Claude loaded project hooks but
  could not initialize session state; completed child work produced no nested-session
  ledger row. This environment-specific failure must not be generalized to writable
  Claude clients.
- 2026-07-13 — Codex CLI 0.144.0 completed mutation, expected-failure, and verification
  actions in a linked worktree, but the installed integration recorded only parent
  orchestration. Codex child capture is currently an explicit unsupported surface.
- 2026-07-13 — Deterministic replay covers all ten cause codes exactly once, and a
  concurrent two-connection regression preserves all 24 events after teardown.
