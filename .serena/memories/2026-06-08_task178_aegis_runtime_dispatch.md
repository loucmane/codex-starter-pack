# Task 178 - Aegis Runtime Dispatch Update Flow

Implemented dynamic Aegis runtime dispatch so downstream projects can update runtime/gate fixes without full scaffold reinstall after a one-time dispatcher bootstrap refresh.

Key changes:
- Installer now manages `.aegis/runtime.env` and manifest `runtime` metadata with source root, commit, dirty state, pointer path, update command, and explicit reinstall-required bootstrap surfaces.
- Installed Claude hook scripts are rendered as stable dispatchers that call `./.aegis/bin/aegis hook <phase>` while source-tree hook scripts remain the runtime implementation for direct tests and fallback behavior.
- Local `.aegis/bin/aegis` shim now prefers `AEGIS_SOURCE_ROOT` or `.aegis/runtime.env` before global package resolution, so runtime fixes from `/home/loucmane/codex` are picked up without rewriting scaffold files.
- CLI added `aegis hook {pretooluse,posttooluse,stop,path,bash,configchange,readiness}` plus `aegis runtime status` and `aegis runtime update --apply`.
- MCP added `aegis.runtime_status` and `aegis.runtime_update` with target confinement and apply-required mutation guarding.
- Gate classifier treats `runtime status` and dry-run `runtime update` as read-only, and `runtime update --apply` as sanctioned Aegis maintenance before task binding.
- Manifest schema and packaged assets were updated, including `runtime` managed-file kind.

Verification:
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/claude_adapter/test_pretooluse_gates.py`
- Result: 252 passed, 1 skipped.
- `task-master validate-dependencies` / `python3 scripts/codex-task taskmaster health` passed with all 177 tasks done and zero invalid dependency refs.

Workflow notes:
- Task 178 and subtasks 178.1-178.5 marked done.
- Task 164 completed active tracker archived to remove multiple-ACTIVE guard issue.
- Task 178 active session/plan/tracker created after implementation because the commit guard required current work tracking aligned to branch task id.