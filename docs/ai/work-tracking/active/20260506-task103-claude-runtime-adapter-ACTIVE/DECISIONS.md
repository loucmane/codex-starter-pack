# Decisions

- 2026-05-06 - Prioritize Task 103 ahead of Task 10 by explicit user direction because the Claude adapter is foundational for multimodal/multi-agent operation across Codex, Claude, shell, MCP, memory, GitHub, and future tool surfaces.
- 2026-05-06 - Use Taskmaster's manual task/subtask creation path because the AI-backed Claude Code provider failed; this keeps `tasks.json` managed by Taskmaster commands rather than manual edits.
- 2026-05-06 - Treat `feat/claude-port-bootstrap` as reference material only. Scope reconciliation must classify every file before any port, and rejected files must be documented.
- 2026-05-06 - The acceptance standard is behavioral: the Claude adapter is not done unless a cold Claude session is mechanically blocked from hookable persistent mutations without matching task/session/plan/work-tracking state.
- 2026-05-06 - Implement readiness as a branch/task/session/plan/tracker alignment gate, not a general repository cleanliness gate. This keeps readiness usable during legitimate implementation while still allowing PreToolUse gates to block all persistent mutations when workflow identity is absent.
- 2026-05-06 - Require exactly one ACTIVE work-tracking folder for the current task in readiness. This matches the current project workflow and prevents Claude from choosing between multiple active audit trails.
