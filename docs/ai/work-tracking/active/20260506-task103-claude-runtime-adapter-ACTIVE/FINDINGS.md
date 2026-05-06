# Findings

- 2026-05-06 - The AI-backed `task-master add-task --prompt ...` path still fails because the configured Claude Code provider exits with an API error; Task 103 was created through Taskmaster's manual `--title/--description/--details` path instead.
- 2026-05-06 - Task 10 remains the normal Taskmaster next item, but the user explicitly prioritized the Claude adapter because the foundation must support multimodal and multi-agent workflows.
- 2026-05-06 - `feat/claude-port-bootstrap` exists and must be treated as raw material only; no file from it is accepted without scope reconciliation, S:W:H:E provenance, and a port/rewrite/discard decision.
- 2026-05-06 - The bootstrap readiness script was a state reporter and exited successfully even when warning about missing workflow pointers. Task 103.2 replaces that behavior with a hard gate that exits `2` when required workflow state is missing or misaligned.
- 2026-05-06 - Readiness should not treat a dirty working tree as a blocker. It gates workflow identity and alignment; downstream guards, git checks, and pre-commit handle file cleanliness and protected-path policy.
- 2026-05-06 - Readiness must support linked Git worktrees because this foundation uses worktrees for parallel work. The implementation now asks Git whether the root is inside a work tree instead of assuming `.git` is a directory.
