# Findings

- 2026-07-14 — The repeated failure was `python3: can't open file '/home/loucmane/codex/.claude/scripts/gate_lib.py'`: project hook definitions resolved through absolute commands in the mutable Aegis source checkout, so a transiently absent source runtime file became a shared availability dependency.
- 2026-07-14 — Current installer output is safer than the affected local definition: generated Codex commands resolve the target Git root and installed shell hooks are rendered as stable dispatchers that prefer the target's `.aegis/bin/aegis` shim.
- 2026-07-14 — The source checkout's `.codex/hooks.json` is untracked operator state and is out of scope for direct mutation. The upstream fix must flow through generated assets, exact legacy-handler adoption, validation, and supported project updates.
- 2026-07-14 — Missing policy runtime cannot silently allow mutation. PreToolUse needs concise fail-closed behavior; passive evidence and Stop paths need bounded non-recursive degradation so one missing file cannot spam every turn.
- 2026-07-14 — Task kickoff exposed a separate source-readiness ordering cycle: completed-source derivation runs before the next ACTIVE envelope exists. The supported wizard kickoff created that envelope; Task 252 will document but not broaden scope to that independent behavior unless implementation requires it.
