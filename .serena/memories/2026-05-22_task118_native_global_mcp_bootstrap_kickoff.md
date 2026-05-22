# Task 118 Native Global MCP Bootstrap Kickoff

Date: 2026-05-22
Branch: `feat/task-118-native-global-mcp-bootstrap`
Session: `sessions/2026/05/2026-05-22-002-task118-native-global-mcp-bootstrap.md`
Plan: `plans/2026-05-22-task118-native-global-mcp-bootstrap.md`
Work tracking: `docs/ai/work-tracking/active/20260522-task118-native-global-mcp-bootstrap-ACTIVE/`
Taskmaster task: 118

## Purpose
Task 118 makes Aegis globally installable and registerable from fresh projects through native MCP client commands, not manual config-file edits. The default happy path should be commands like `claude mcp add ...` and `codex mcp add ...` that point at a packaged `aegis-mcp-server`.

## Scope
- Add deterministic native MCP registration command generation for Claude and Codex.
- Support package, pinned package, GitHub URL/ref, local wheel, and source checkout install modes.
- Add execute and verify flows that use native clients with argv lists and no `shell=True`.
- Keep manual `.mcp.json` / config-file writes as explicit fallback only.
- Update source and packaged docs so internet/global install is the primary documented path.
- Prove fresh-project bootstrap does not depend on `/home/loucmane/codex` existing locally.

## Boundaries
- Preserve `aegis-mcp-server` command shape from `aegis_mcp/server.py`.
- Keep installer behavior in the existing Aegis runtime/installer core; do not create a second installer engine.
- Do not require Taskmaster or Serena in target projects. Aegis should use them only when available.
- Do not treat manual MCP config snippets as the primary install path.

## Current State
- Task 117 was pushed as `feat/task-117-aegis-closeout-gate` at commit `7ed9bed`.
- Task 118 is in progress and depends on Task 117.
- The Task 118 workflow has branch/session/plan/ACTIVE work tracking and readiness is `READY | task=118`.
- The initial kickoff plan had generic wizard wording; it was corrected to the native MCP bootstrap scope before implementation.

## Resume
Start by implementing and testing the native MCP registration contract:
1. Add a small registration model/module for clients, scopes, source modes, and generated argv.
2. Wire package CLI and repo wrapper commands.
3. Add generation, execution, missing-client, and verification parser tests.
4. Update docs and packaged assets.
5. Run the focused Task 118 test matrix plus plan sync, work-tracking audit, guard, and diff-check.
