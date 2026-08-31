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
