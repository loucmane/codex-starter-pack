# Findings

- 2026-08-30 — Fresh-worktree readiness and kickoff currently form an ordering paradox:
  readiness correctly refuses missing source evidence, but the routing skill asks agents to
  run readiness before invoking the supported kickoff that creates that evidence.
- 2026-08-30 — The readiness renderer's `./.aegis/bin/aegis next` remediation is unavailable
  in both the canonical source checkout and a newly created linked worktree. Tracked source
  adapters must be the durable continuation surface.
- 2026-08-30 — Existing source and installed Aegis kickoff implementations already provide
  most transition mechanics. The missing layer is deterministic orchestration and recovery,
  not another policy engine.
