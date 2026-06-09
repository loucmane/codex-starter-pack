# Task 183 - Safe Aegis Repair While Blocked

Date: 2026-06-09
Branch: `feat/task-183-safe-repair-while-blocked`

Implemented a targeted PreToolUse gate hardening so doctor-prescribed Aegis safe repair apply can run when readiness is already BLOCKED. This fixes the HP-Coach deadlock where a completed observation had a malformed plan scaffold and both CLI/MCP `aegis repair --apply` were refused by the same readiness state they needed to repair.

Changed files:
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `tests/claude_adapter/test_pretooluse_gates.py`
- Taskmaster/work-tracking files for task 183

Behavior:
- Allows strict single-segment CLI `aegis repair --apply` while readiness is BLOCKED.
- Allows direct MCP `mcp__aegis__aegis_repair` with `apply: true` while readiness is BLOCKED.
- Still blocks out-of-project target dirs, pending tracking conflicts, compounded shell mutations, closeout, Taskmaster mutations, and file writes.

Validation:
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py -q` -> 126 passed.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py -q` -> 270 passed, 1 skipped.
- Taskmaster validation and health passed after marking task 183 done.