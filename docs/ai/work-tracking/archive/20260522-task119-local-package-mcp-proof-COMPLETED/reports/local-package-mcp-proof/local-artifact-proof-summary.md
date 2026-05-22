# Local Artifact Proof Summary

## Scope

Task 119 proves the local package path before any TestPyPI or PyPI publishing work.

## Code Changes

- `aegis_foundation/mcp_registration.py` now validates `wheel` and `source` local artifact modes.
- Wheel mode requires an existing `.whl` file and renders an absolute `uvx --from` package spec.
- Source mode requires an existing directory with `pyproject.toml` and renders an absolute `uvx --from` package spec.
- `aegis certify-release` now runs a local-wheel MCP server config smoke with `uvx --from <wheel> aegis-mcp-server --describe-config`.
- The existing real target wheel MCP smoke now includes scope logging, implementation evidence logging, strict verification logging, closeout, and no source-checkout leakage checks.

## Verification

Commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_native_mcp_registration.py
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_release_distribution.py::test_distribution_doc_includes_public_and_local_install_snippets tests/meta_workflow_guard/test_aegis_release_distribution.py::test_mcp_client_setup_doc_covers_cross_agent_release_candidate_configs tests/meta_workflow_guard/test_aegis_release_distribution.py::test_release_policy_docs_cover_update_rollback_and_signing tests/meta_workflow_guard/test_aegis_release_distribution.py::test_ci_templates_and_release_matrix_cover_distribution_dimensions
PYTHONDONTWRITEBYTECODE=1 AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py::test_local_wheel_mcp_real_target_project_smoke_when_enabled
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_release_distribution.py tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_cross_project_smoke.py
PYTHONDONTWRITEBYTECODE=1 AEGIS_RUN_CERTIFICATION_SMOKE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py::test_release_certification_full_clean_smoke_when_enabled
PYTHONDONTWRITEBYTECODE=1 uv run aegis certify-release --source-dir . --dist-dir docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/reports/local-package-mcp-proof/dist --report-file docs/ai/work-tracking/active/20260522-task119-local-package-mcp-proof-ACTIVE/reports/local-package-mcp-proof/certification-report.json
```

Results:

- Native MCP registration tests: 18 passed.
- Focused registration + release documentation tests: 22 passed.
- Real local-wheel MCP target smoke: 1 passed in 7.49s.
- Broader Aegis regression slice: 81 passed, 4 skipped.
- Full release certification pytest smoke: 1 passed in 9.58s.
- Certification report: `status=passed`.
- Clean installed-wheel CLI smoke: `passed`.
- Local-wheel MCP server config smoke: `passed`.
- Full MCP stdio workflow proof: covered by focused pytest target.

## Artifacts

- Wheel: `dist/aegis_foundation-0.1.0-py3-none-any.whl`
  - SHA-256: `91aa51bd44771c56f04dd1266644764b3857dfbfbdedf4b113e5889d6e28a68a`
- Sdist: `dist/aegis_foundation-0.1.0.tar.gz`
  - SHA-256: `039739acab08f5d73cf6c384276ad37ebdc764225eaef29fd04694b255e683a4`
- Certification report: `certification-report.json`

## PyPI Gate

TestPyPI and PyPI publication remain explicitly deferred. The next publishing task can start only from this local artifact proof baseline.
