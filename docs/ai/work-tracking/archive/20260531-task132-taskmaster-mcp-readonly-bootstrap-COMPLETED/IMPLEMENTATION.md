# Task 132 Allow Read-Only Taskmaster MCP Discovery During Aegis Bootstrap – Implementation Notes

## Planned Workstreams
- `.claude/scripts/gate_lib.py`: added `TASKMASTER_READ_ONLY_MCP_TOOL_SUFFIXES`, MCP name normalization helpers, `mcp_is_taskmaster_tool()`, and `mcp_is_read_only_taskmaster_discovery()`.
- `.claude/scripts/gate_lib.py`: changed `mcp_is_mutation()` so Taskmaster MCP tools are handled before generic MCP regexes; only `help`, `get_tasks`, `next_task`, and `get_task` are non-mutating.
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`: mirrored the runtime gate change for installed projects.
- `tests/claude_adapter/test_pretooluse_gates.py`: added positive coverage for allowed Taskmaster discovery tools and negative coverage for mutations, unknown Taskmaster MCP tools, and a `forget_task` suffix edge case.
- Documentation: updated CLAUDE/runtime docs plus source and packaged Aegis docs to describe the narrow pre-kickoff discovery carve-out.
