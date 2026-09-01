# Decisions

- 2026-08-31 — Trust only hook identities returned by `hooks/list` whose source path, event,
  matcher, command, timeout, handler metadata, and current hash match the merge-bound generated
  Aegis contract. Caller identity and remembered project trust are not authority.
- 2026-08-31 — Prove denial by submitting a synthetic Codex-shaped PreToolUse envelope directly
  to the installed target-local gate. Never invoke `spawn_agent`; the canary records
  `child_launch_attempted=false`.
- 2026-08-31 — Restore the synthetic canary's user config byte/mode/owner-exact on success and on
  every failure. Persistent project trust is a separate transaction that rolls back on failure
  and must prove a byte-identical second application before success.



## Progress Log

- **2026-09-01 11:16** — [S:20260901|W:ga-ur1c.4.1-transactionally-prove-managed-codex-delegation-denial|H:scripts/codex-task:sessions-continue|E:plans/2026-08-31-ga-ur1c.4.1-transactionally-prove-managed-codex-delegation-denial.md] Resolved generated pointer drift only through the supported continuation transaction so session, plan, tracker, and sync evidence remain one atomic authority surface.
