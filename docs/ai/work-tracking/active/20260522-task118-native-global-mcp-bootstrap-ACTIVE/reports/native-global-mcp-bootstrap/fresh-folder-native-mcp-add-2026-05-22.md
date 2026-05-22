# Fresh Folder Native MCP Add Smoke

Date: 2026-05-22
Fresh project: `/tmp/aegis-native-mcp-fresh-h6VVTd`

## Setup

Created a brand-new temporary folder and initialized an empty Git repository:

```bash
mktemp -d /tmp/aegis-native-mcp-fresh-XXXXXX
git init -b main
```

Built a local wheel as the packaged artifact under the fresh folder:

```bash
uv build --wheel --out-dir /tmp/aegis-native-mcp-fresh-h6VVTd/dist
```

Built artifact:

```text
/tmp/aegis-native-mcp-fresh-h6VVTd/dist/aegis_foundation-0.1.0-py3-none-any.whl
```

## Native Client Registration

Initial registration without local uv environment directories wrote `.mcp.json`, but Claude reported `Status: Failed to connect` because sandboxed `uvx` attempted to write to user-global uv cache/tool directories.

Working registration:

```bash
claude mcp add --scope project aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from /tmp/aegis-native-mcp-fresh-h6VVTd/dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
```

Verification:

```bash
claude mcp get aegis
```

Result:

```text
aegis:
  Scope: Project config (shared via .mcp.json)
  Status: Connected
  Type: stdio
  Command: uvx
  Args: --from /tmp/aegis-native-mcp-fresh-h6VVTd/dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
  Environment:
    UV_CACHE_DIR=.aegis/uv-cache
    UV_TOOL_DIR=.aegis/uv-tools
```

## MCP Tool Flow

Used the registered `.mcp.json` entry as the source of truth, launched the MCP server through the same command, and ran:

- `list_tools`
- `aegis.inspect`
- `aegis.plan_install`
- `aegis.install`
- `aegis.kickoff`
- `aegis.log`
- `aegis.verify`
- `aegis.closeout`
- `.claude/scripts/readiness.sh --quick`

Summary payload:

```json
{
  "closeout_status": "passed",
  "created_paths": {
    "aegis_manifest": true,
    "claude_readiness": true,
    "claude_settings": true,
    "closeout_report": true,
    "mcp_config": true,
    "plans_current": true,
    "sessions_current": true,
    "smoke_file": true,
    "verification_report": true,
    "work_tracking_active": true
  },
  "implement_log_status": "logged",
  "inspect_before": false,
  "install_status": "applied",
  "kickoff_status": "started",
  "plan_status": "dry_run",
  "project": "/tmp/aegis-native-mcp-fresh-h6VVTd",
  "readiness_returncode": 0,
  "readiness_stdout": "READY | task=1",
  "scope_log_status": "logged",
  "tools_present": [
    "aegis.closeout",
    "aegis.inspect",
    "aegis.install",
    "aegis.kickoff",
    "aegis.log",
    "aegis.verify"
  ],
  "verify_log_status": "logged",
  "verify_status": "passed"
}
```

## Generated Registration Fresh Folder

Created a second brand-new temporary folder:

```text
/tmp/aegis-native-mcp-generated-fresh-8iFVuv
```

Built a fresh wheel into that folder and registered the MCP server through the new Task 118 package CLI, not by hand-writing `.mcp.json`:

```bash
python3 -m aegis_foundation.cli mcp execute-registration \
  --client claude \
  --scope project \
  --source-mode wheel \
  --artifact /tmp/aegis-native-mcp-generated-fresh-8iFVuv/dist/aegis_foundation-0.1.0-py3-none-any.whl \
  --target-dir . \
  --cwd /tmp/aegis-native-mcp-generated-fresh-8iFVuv
```

Generated native command:

```bash
claude mcp add --scope project aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from /tmp/aegis-native-mcp-generated-fresh-8iFVuv/dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
```

Native client verification:

```text
aegis:
  Scope: Project config (shared via .mcp.json)
  Status: Connected
  Type: stdio
  Command: uvx
  Args: --from /tmp/aegis-native-mcp-generated-fresh-8iFVuv/dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
  Environment:
    UV_CACHE_DIR=.aegis/uv-cache
    UV_TOOL_DIR=.aegis/uv-tools
```

Then launched the MCP server from the generated `.mcp.json` and ran the same install/kickoff/log/verify/closeout/readiness flow:

```json
{
  "closeout_status": "passed",
  "created_paths": {
    "aegis_manifest": true,
    "claude_readiness": true,
    "claude_settings": true,
    "closeout_report": true,
    "mcp_config": true,
    "plans_current": true,
    "sessions_current": true,
    "smoke_file": true,
    "verification_report": true,
    "work_tracking_active": true
  },
  "implement_log_status": "logged",
  "inspect_before": false,
  "install_status": "applied",
  "kickoff_status": "started",
  "plan_status": "dry_run",
  "project": "/tmp/aegis-native-mcp-generated-fresh-8iFVuv",
  "readiness_returncode": 0,
  "readiness_stdout": "READY | task=1",
  "scope_log_status": "logged",
  "tools_present": [
    "aegis.closeout",
    "aegis.inspect",
    "aegis.install",
    "aegis.kickoff",
    "aegis.log",
    "aegis.verify"
  ],
  "verify_log_status": "logged",
  "verify_status": "passed"
}
```

## Conclusion

The native `claude mcp add` path successfully installed and operated the full Aegis ecosystem in freshly created folders after registration included project-local uv cache/tool directories.

The stronger generated path also passed: `aegis mcp execute-registration` produced the native Claude registration command, `claude mcp get aegis` connected, and the MCP tools installed Aegis, created workflow scaffolding, logged S:W:H:E evidence, verified, closed out, and left readiness `READY | task=1` in a new folder. This is the acceptance shape Task 118 needs: native MCP registration first, project-local Aegis runtime install second, then kickoff/log/verify/closeout gates inside the target project.
