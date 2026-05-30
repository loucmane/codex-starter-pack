# Task ID: 132

**Title:** Allow Read-Only Taskmaster MCP Discovery During Aegis Bootstrap

**Status:** pending

**Dependencies:** 131 ✓

**Priority:** medium

**Description:** Harden the installed Claude/Aegis PreToolUse gate so read-only Taskmaster MCP discovery can run while readiness is BLOCKED, without opening any Taskmaster mutation path before Aegis kickoff or after closeout rules permit it.

**Details:**

Codebase analysis: the relevant enforcement path is `.claude/scripts/pretooluse-gate.sh`, which delegates to `.claude/scripts/gate_lib.py`. MCP classification currently happens in `mcp_is_mutation()`, using generic read-only and mutation regexes plus Aegis-specific suffix handling. Existing focused coverage lives in `tests/claude_adapter/test_pretooluse_gates.py`, including blocked readiness fixtures, blocked mutating Taskmaster MCP calls, generic read-only MCP allowance, unknown MCP fail-closed behavior, and the post-closeout Taskmaster completion allowance. Documentation that must stay aligned includes `.claude/engine/runtime-contract.md`, `.claude/engine/claude-readiness.md`, `CLAUDE.md`, `docs/aegis/invocation-contract.md`, and `docs/aegis/mcp-client-setup.md`.

Implement a narrow, explicit Taskmaster MCP read-only allowlist in `.claude/scripts/gate_lib.py` rather than relying only on broad verb regexes. Add a helper such as `mcp_is_read_only_taskmaster_discovery(payload)` that normalizes Claude MCP tool names with the existing lower/underscore pattern and returns true only for Taskmaster discovery tools like `mcp__taskmaster_ai__help`, `mcp__taskmaster_ai__get_tasks`, `mcp__taskmaster_ai__next_task`, and `mcp__taskmaster_ai__get_task` (include the hyphenated server spelling if current settings expose `mcp__taskmaster-ai__*`). Treat these tools as non-mutating even when `.aegis/state/current-work.json` is absent, Aegis is not installed, or readiness is BLOCKED because no branch/session/plan/work-tracking state exists.

Keep fail-closed mutation behavior intact. Explicitly confirm that Taskmaster MCP tools including `set_task_status`, `update_task`, `update_subtask`, `add_task`, `expand_task`, `parse_prd`, `generate`, dependency changes, moves, and any unknown Taskmaster MCP action remain mutations when readiness is BLOCKED. Preserve the existing `payload_is_post_closeout_taskmaster_completion()` behavior: only the matching task `set_task_status done/completed` and generated-file refresh allowance after completed Aegis closeout should bypass blocked readiness, and no broader pre-kickoff Taskmaster mutation carve-out should be introduced.

Best-practice constraints for this safety gate: use a positive allowlist for side-effect-free discovery, normalize tool names once to avoid alias drift, keep unknown MCP calls persistent by default, avoid inspecting untrusted arguments for read-only tools except for path-protection checks already present, and make tests assert both the allowed path and adjacent denied paths so later broad regex changes cannot silently widen permissions.

Update docs to describe the carve-out in the same language as the existing workflow: before `aegis.kickoff`, agents may use read-only Taskmaster MCP discovery (`help`, `get_tasks`, `next_task`, `get_task`) or the CLI equivalents to find the external numeric task when available; Taskmaster mutations remain blocked until readiness is READY, except for the existing post-closeout completion bookkeeping path. Also update packaged or asset mirrors if this repo requires runtime files/docs to be mirrored into `aegis_foundation/assets/...` for distribution tests.

**Test Strategy:**

Add focused regressions in `tests/claude_adapter/test_pretooluse_gates.py` using the existing blocked repo fixture. Assert `mcp__taskmaster_ai__help`, `mcp__taskmaster_ai__get_tasks`, `mcp__taskmaster_ai__next_task`, and `mcp__taskmaster_ai__get_task` return 0 with empty stderr while readiness is BLOCKED and no current Aegis work exists. Include the currently configured hyphenated server alias if applicable.

Add parameterized negative tests proving `mcp__taskmaster_ai__set_task_status`, `update_task`, `update_subtask`, `add_task`, `expand_task`, `parse_prd`, and `generate` still return 2 with the readiness BLOCKED message before kickoff. Keep or extend the existing unknown MCP test so unknown Taskmaster MCP names also fail closed.

Re-run the existing post-closeout tests to prove the completed-closeout allowance still permits only matching Taskmaster completion and generate refresh, while mismatched status changes and source mutations stay blocked. Run at minimum `pytest tests/claude_adapter/test_pretooluse_gates.py`; if docs/assets mirrors are updated, also run the relevant Aegis contract/doc tests such as `pytest tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py tests/meta_workflow_guard/test_aegis_installer.py -q` or the narrow targets that validate packaged documentation consistency.
