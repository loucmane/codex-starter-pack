# Final Verification

Date: 2026-05-22 17:41 CEST

## Focused Changed-Surface Tests

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-task120-uv-cache-final2 UV_TOOL_DIR=/tmp/aegis-task120-uv-tools-final2 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py::test_installed_web_target_real_feature_change_updates_full_workflow tests/meta_workflow_guard/test_aegis_release_distribution.py::test_distribution_doc_includes_public_and_local_install_snippets tests/meta_workflow_guard/test_aegis_release_distribution.py::test_mcp_client_setup_doc_covers_cross_agent_release_candidate_configs tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py::test_local_cli_shim_resolves_packaged_asset_source_root
```

Result:

```text
24 passed in 3.65s
```

## Broad Aegis Slice

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-task120-uv-cache-broad-final UV_TOOL_DIR=/tmp/aegis-task120-uv-tools-broad-final uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_release_distribution.py tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_cross_project_smoke.py tests/claude_adapter/test_pretooluse_gates.py
```

Result:

```text
102 passed, 4 skipped in 35.65s
```

Skipped tests were explicit opt-in smoke tests:

- full release certification smoke
- local wheel CLI smoke
- local wheel MCP smoke
- real target-project MCP smoke

Those flows were covered earlier in Task 120 evidence where explicitly enabled.

## Workflow Gates

Commands and results:

```text
python3 scripts/codex-task plan sync
Plan sync recorded for plans/2026-05-22-task120-fresh-local-install-proof.md

python3 scripts/codex-task work-tracking audit
Audit passed: no issues found.

python3 scripts/codex-guard validate --include-untracked
Guard validation passed: all S:W:H:E entries look compliant.

python3 scripts/codex-task taskmaster health
Taskmaster health: OK
Tasks: 120
Statuses: done=119, in-progress=1
Invalid dependency refs: 0

bash .claude/scripts/readiness.sh --quick
READY | task=120

git diff --check
clean
```
