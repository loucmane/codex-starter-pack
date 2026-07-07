# Task 231 Unified Aegis project update command – Implementation Notes

## Planned Workstreams
- Add `project_update()` to the shared installer module. It composes runtime pointer
  update, managed install plan/apply, verification reporting, and capsule compile/check.
- Expose the command as package-style `aegis update --target-dir . [--apply]`.
- Expose the same command through the repository wrapper:
  `python3 scripts/codex-task aegis update --target-dir . [--apply]`.
- Expose the same update primitive through MCP as `aegis.update`, so long-running
  Claude/MCP sessions can use the composed updater instead of manually chaining
  runtime/install/verify/brief steps.
- Keep verification failures as report evidence rather than update failure when the
  managed refresh itself succeeds.
- Cover dry-run, apply, manual-review refusal, and wrapper CLI behavior in
  `tests/meta_workflow_guard/test_aegis_installer.py`; cover MCP update behavior in
  `tests/meta_workflow_guard/test_aegis_mcp_server.py`.
