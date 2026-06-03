# Task 156 Verification - Taskmaster Single Authority

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -q
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py -q
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py -q
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py -q
PYTHONDONTWRITEBYTECODE=1 uv run ruff check --ignore E402 scripts/_aegis_installer.py aegis_foundation/assets/scripts/_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer.py
PYTHONDONTWRITEBYTECODE=1 uv run python scripts/codex-task taskmaster health
PYTHONDONTWRITEBYTECODE=1 uv run python scripts/codex-task work-tracking audit
PYTHONDONTWRITEBYTECODE=1 uv run python scripts/codex-guard validate --include-untracked
git diff --check
```

## Results
- Installer suite: `66 passed, 1 skipped`
- MCP server suite: `48 passed`
- Reconcile shadow/apply suite: `34 passed`
- Reconcile write apparatus suite: `19 passed`
- Ruff: `All checks passed!`
- Taskmaster health: `OK` (`done=156, pending=2`)
- Work-tracking audit: passed
- Codex guard: passed
- Diff whitespace check: passed

## Notes
- The `E402` lint ignore is for the installer module's existing intentional `sys.path` bootstrap before importing the packaged version module.
- The unreadable Taskmaster test is skipped when running as root because `chmod 000` cannot make the file unreadable to root.
