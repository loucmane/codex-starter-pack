# Findings

- 2026-05-06 - The AI-backed `task-master add-task --prompt ...` path still fails because the configured Claude Code provider exits with an API error; Task 103 was created through Taskmaster's manual `--title/--description/--details` path instead.
- 2026-05-06 - Task 10 remains the normal Taskmaster next item, but the user explicitly prioritized the Claude adapter because the foundation must support multimodal and multi-agent workflows.
- 2026-05-06 - `feat/claude-port-bootstrap` exists and must be treated as raw material only; no file from it is accepted without scope reconciliation, S:W:H:E provenance, and a port/rewrite/discard decision.
- 2026-05-06 - The bootstrap readiness script was a state reporter and exited successfully even when warning about missing workflow pointers. Task 103.2 replaces that behavior with a hard gate that exits `2` when required workflow state is missing or misaligned.
- 2026-05-06 - Readiness should not treat a dirty working tree as a blocker. It gates workflow identity and alignment; downstream guards, git checks, and pre-commit handle file cleanliness and protected-path policy.
- 2026-05-06 - Readiness must support linked Git worktrees because this foundation uses worktrees for parallel work. The implementation now asks Git whether the root is inside a work tree instead of assuming `.git` is a directory.
- 2026-05-06 - The bootstrap settings allowed broad read/write-capable Bash helpers like `awk`, `printf`, and `echo`. Task 103.3 replaces that with a narrower project `.claude/settings.json` and routes mutation-capable tools through the PreToolUse dispatcher.
- 2026-05-06 - Bash command parsing remains best-effort. The verified claim is limited to tested command-string patterns; untested shell grammar remains a Task 103.5 evidence/policy surface and Task 9 CI/pre-commit concern.
- 2026-05-06 - `task-master generate` in Taskmaster `0.43.1` still does not provide a single-task output flag. The clean workaround is temp-output generation plus copying only the requested `task_<id>.txt`; Task 104 tracks turning this into a first-class helper.
- 2026-05-06 - The repo and Cursor MCP configs were unpinned (`task-master-ai` without `@latest`). This usually resolves current packages through `npx`, but explicit `task-master-ai@latest` is clearer and keeps MCP launch intent aligned with the installed CLI.
