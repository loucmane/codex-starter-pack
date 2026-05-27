# Task 126 Verification

## Focused Acceptance Suite

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_acceptance_assertions.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_cross_project_smoke.py tests/meta_workflow_guard/test_aegis_release_distribution.py
```

Result: passed, 83 passed, 4 skipped.

Skipped optional smoke tests:

- `AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE`
- `AEGIS_RUN_CERTIFICATION_SMOKE`
- `AEGIS_RUN_WHEEL_SMOKE`
- `AEGIS_RUN_WHEEL_MCP_SMOKE`

## Lint

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check tests/meta_workflow_guard/aegis_acceptance_assertions.py tests/meta_workflow_guard/test_aegis_acceptance_assertions.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
```

Result: passed.
