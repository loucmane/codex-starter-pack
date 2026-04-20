# 2026-04-20 Task 89 MCP Re-entry

## Context
- Current branch: `feat/task-89-work-tracking-enforcement`.
- Active work-tracking folder: `docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/`.
- Today's session: `sessions/2026/04/2026-04-20-001-task89-mcp-reentry.md`.
- The project was resumed after a long gap. Task 89 was previously verified, but the Codex runtime config no longer matched the documented MCP workflow.

## Finding
- The current `.codex/config.toml` had been migrated to a minimal working config with no MCP server declarations.
- The old `.codex/config.toml.bak` preserved the historical MCP intent, but it was not safe to restore wholesale because it included legacy command names, a home-directory override, optional stale MCPs, and embedded third-party secrets.

## Decision
- Keep the modern working config as the base.
- Restore only the core MCPs needed for this repo: `serena` and `taskmaster-ai`.
- Use the current Serena command shape: `uvx --from git+https://github.com/oraios/serena@229fac066237f7156c8fe2a9fa7166f95715e0b3 serena start-mcp-server --project-from-cwd`.
- Do not restore optional MCPs (`context7`, `sequential-thinking`, `firecrawl`, `elevenlabs`, `fpl`, `shadcn`) until there is a current use case and startup verification.

## Verification So Far
- `codex mcp list` showed enabled `serena` and `taskmaster-ai` after config repair.
- `codex mcp get serena --json` confirmed the corrected Serena transport config.
- Taskmaster MCP startup help completed successfully.
- Serena startup help completed successfully with the corrected `start-mcp-server` command.
- Taskmaster parent-status drift was corrected after review: Tasks 83 and 86 are now marked done, matching their completed subtasks.
- `task-master list` now reports Done 10, In Progress 0, Pending 87.

## Next Steps
- Finish protocol recovery by rerunning `python3 scripts/codex-task work-tracking audit`.
- Run `python3 scripts/codex-guard validate --include-untracked` after tracker/session updates.
- Review `.codex/config.toml` diff before committing.
- Decide separately whether optional MCPs should be added back.

## Process Note
- Do not run multiple `task-master set-status` mutations in parallel. The parallel April 20 attempt produced misleading success output while Task 86 remained `in-progress`; rerunning Task 86 sequentially fixed the persisted state.
