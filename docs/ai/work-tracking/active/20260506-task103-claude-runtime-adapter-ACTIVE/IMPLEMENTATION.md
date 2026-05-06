# Task 103 Claude Runtime Adapter and Multimodal Workflow Enforcement – Implementation Notes

## Planned Workstreams
- Subtask 103.1: reconcile the bootstrap branch, ownership boundary, hookability taxonomy, and runtime file contract.
- Subtask 103.2: implement readiness as a hard gate.
- Subtask 103.3: implement Claude PreToolUse mutation gates.
- Subtask 103.4: port or rewrite approved Claude adapter files.
- Subtask 103.5: prove behavior with tests, guard evidence, handoff, and Serena memory.

## Non-Negotiable Acceptance Standard
- Documentation and memory are not sufficient. The deliverable is a gated runtime that mechanically prevents invalid Claude actions where the tool surface is hookable.
- Every enforcement claim must be backed by a passing test or explicitly labeled policy-only with limitations documented in `DECISIONS.md` and `HANDOFF.md`.
- The system must be multimodal/multi-agent: it must account for Codex, Claude, shell, MCP, memory stores, GitHub flows, and future agent/tool surfaces without assuming one text-only execution path.

## Subtask 103.2 - Readiness Hard Gate
- Added `.claude/scripts/readiness.sh` as a read-only hard gate. It discovers the repo root, parses the current branch task ID, verifies the Taskmaster parent status, checks `sessions/current`, `sessions/state.json`, `plans/current`, the ACTIVE work-tracking folder, and tracker/plan checklist alignment.
- Added `.claude/engine/claude-readiness.md` to document readiness states, exit codes, and required alignment.
- Added `tests/claude_adapter/test_readiness_gate.py` with isolated temporary git repositories so the tests do not mutate the real project state, including a linked Git worktree regression where `.git` is a file.
- Captured live readiness evidence in `reports/claude-runtime-adapter/readiness-2026-05-06-pass.txt`.
- Captured focused pytest evidence in `reports/claude-runtime-adapter/tests-2026-05-06-readiness.txt`.

## Subtask 103.3 - PreToolUse Mutation Gates
- Added `.claude/scripts/pretooluse-gate.sh` as the dispatcher for Claude `Edit`, `Write`, `MultiEdit`, `NotebookEdit`, and `Bash` tool calls.
- Added `.claude/scripts/gate_lib.py` to keep JSON hook parsing, path normalization, readiness dispatch, and Bash command classification centralized and testable.
- Added `.claude/scripts/codex-path-guard.sh` for direct file-tool protected path checks.
- Added `.claude/scripts/bash-command-guard.sh` for tested Bash bypass patterns, including redirection to `CODEX.md`, `sed -i` against `templates/**`, and Python `open(..., "w")` against `scripts/codex-*`.
- Added `.claude/settings.json` to register the PreToolUse dispatcher and avoid the broad write-capable Bash allowlist from the bootstrap branch.
- Added `tests/claude_adapter/test_pretooluse_gates.py` with isolated temporary git repositories so hook behavior is tested without mutating the real project.
- Captured focused pytest evidence in `reports/claude-runtime-adapter/tests-2026-05-06-pretooluse.txt`.
- Captured `.claude/settings.json` syntax evidence in `reports/claude-runtime-adapter/settings-json-2026-05-06-pretooluse.txt`.

## Taskmaster/MCP Runtime Update
- Verified npm registry stable latest for `task-master-ai` as `0.43.1` in `reports/claude-runtime-adapter/taskmaster-npm-view-2026-05-06.json`.
- Updated the installed `task-master` CLI from `0.26.0` to `0.43.1`; evidence is stored in `reports/claude-runtime-adapter/taskmaster-version-2026-05-06.txt`.
- Updated `.mcp.json` and `.cursor/mcp.json` to use `--package=task-master-ai@latest`.
- Added Taskmaster Task 104 as the follow-up for a targeted task-file generation helper; evidence is stored in `reports/claude-runtime-adapter/task-104-show-2026-05-06.txt`.
- Confirmed `task-master generate` still lacks a single-task generation flag in `0.43.1`; evidence is stored in `reports/claude-runtime-adapter/taskmaster-generate-help-2026-05-06.txt`.
