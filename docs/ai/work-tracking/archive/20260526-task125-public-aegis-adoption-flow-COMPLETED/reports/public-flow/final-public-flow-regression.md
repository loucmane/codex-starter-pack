# Final Public Flow Regression

## Date

2026-05-27

## Command

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_release_distribution.py
```

## Result

```text
109 passed, 3 skipped in 21.81s
```

## Coverage

This focused regression slice covers:

- public `aegis init`
- public `aegis start`
- local-task kickoff without Taskmaster or Serena
- `aegis mcp register claude`
- MCP tool exposure for `aegis.init` and `aegis.start`
- invocation contract documentation
- release/distribution documentation

Skipped tests were optional release certification/wheel smoke checks controlled by environment variables.

