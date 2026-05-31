# Task 132 Taskmaster MCP Read-Only Bootstrap

- Date: 2026-05-31
- Branch: `feat/task-132-taskmaster-mcp-readonly-bootstrap`
- Scope: allow read-only Taskmaster MCP discovery during Aegis bootstrap/readiness-blocked states while keeping Taskmaster mutations and unknown Taskmaster MCP tools blocked.
- Implementation: added explicit Taskmaster MCP discovery allowlist in `.claude/scripts/gate_lib.py` and mirrored it to `aegis_foundation/assets/.claude/scripts/gate_lib.py`.
- Allowed pre-kickoff Taskmaster MCP tools: `help`, `get_tasks`, `next_task`, `get_task`; both `taskmaster_ai` and hyphenated `taskmaster-ai` server spellings covered.
- Blocked coverage: `set_task_status`, `update_task`, `update_subtask`, `add_task`, `expand_task`, `parse_prd`, `generate`, dependency/move operations, `show`, `forget_task`, and unknown Taskmaster MCP actions while readiness is `BLOCKED`.
- Docs updated: `CLAUDE.md`, `.claude/engine/runtime-contract.md`, `.claude/engine/claude-readiness.md`, source and packaged `docs/aegis/{invocation-contract,mcp-client-setup,public-adoption-flow}.md`.
- Verification: focused suite passed (`89 passed, 1 skipped`); full pytest passed with git signing disabled in test subprocesses (`812 passed, 4 skipped`). Initial full pytest failed only because global git config forced GPG signing in a temp-repo commit test.
- Active work tracking: `docs/ai/work-tracking/active/20260531-task132-taskmaster-mcp-readonly-bootstrap-ACTIVE/`.