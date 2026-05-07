# Findings

- 2026-05-07 — Task 103 already implemented the initial Claude runtime adapter and is archived as completed. Task 105 is therefore a hardening and live-validation follow-up, not a duplicate adapter build.
- 2026-05-07 — Official Claude Code hook documentation confirms that `PreToolUse` receives tool JSON before execution and exit code `2` blocks the tool call. This supports the Task 103 dispatcher architecture as the primary enforcement layer.
- 2026-05-07 — Current Claude Code hook documentation also exposes broader hook surfaces than Task 103 currently registers: MCP tool names can be matched with `mcp__...`, `ConfigChange` can block configuration changes, `UserPromptExpansion` can block slash-command expansion, and task/subagent lifecycle hooks exist for team/subagent behavior. Task 105 must evaluate these surfaces instead of assuming file/Bash hooks are complete.
- 2026-05-07 — `.claude/engine/runtime-contract.md` is stale after Task 103 archive. It still says draft, says final evidence is pending, and points to active Task 103 paths instead of current completed/archive state.
- 2026-05-07 — The guided kickoff scaffold initially generated stale wizard-helper wording in the Task 105 plan. This was corrected before implementation so plan/tracker scope matches Claude runtime adapter hardening.
- 2026-05-07 — Current `.claude/settings.json` registered PreToolUse only for file tools and Bash. This left MCP tools outside the dispatcher despite official Claude Code docs documenting `mcp__...` matcher names.
- 2026-05-07 — Hook self-protection was incomplete. A ready Claude session could edit project `.claude/settings.json`; without a `ConfigChange` guard, weakened hooks could apply to the running session.
