# Task ID: 112

**Title:** Aegis Packaging and Invocation Contract

**Status:** done

**Dependencies:** 109 ✓, 110 ✓, 111 ✓

**Priority:** medium

**Description:** Define and implement the first stable external invocation contract for Aegis so fresh projects can run installer and MCP workflows without assuming commands are launched from this repository root. This task creates local-development and package-ready invocation paths, with tests and documentation, but does not publish Aegis publicly.

**Details:**

Codebase analysis summary:
- `pyproject.toml` is a Python 3.11 project with `click`, `jsonschema`, `mcp`, `pyyaml`, and `rich`, but it currently sets `[tool.uv] package = false` and has no package entrypoints, so `uvx`/`pipx`/console-script invocation is not yet defined.
- The deterministic installer source of truth already exists in `scripts/_aegis_installer.py`; key functions are `inspect_project`, `plan_install`, `install`, `verify`, `list_profiles`, and `explain_profile`. The core reads managed assets from an explicit `source_root`, including `schemas/aegis/*.schema.json`, `scripts/codex-task`, `scripts/codex-guard`, `scripts/_repo_structure.py`, `scripts/template_registry.py`, `scripts/template_governance.py`, `scripts/template_versioning.py`, and Claude gate scripts under `.claude/scripts/`.
- The local repository CLI wrapper already exists in `scripts/codex-task` under the `aegis` argparse group. It computes `REPO_ROOT` from the script path, which supports a local checkout, but Task 111 smoke helpers currently invoke it from `cwd=REPO_ROOT`, so the external-cwd contract remains unproven.
- The MCP control plane already exists in `aegis_mcp/server.py` plus `scripts/aegis-mcp-server`. `AegisMCPConfig.from_paths` supports `--source-root`, `--default-target-dir`, `AEGIS_SOURCE_ROOT`, and `AEGIS_DEFAULT_TARGET_DIR`, which should be carried into the external invocation contract rather than replaced.
- Existing coverage includes `tests/meta_workflow_guard/test_aegis_installer.py`, `test_aegis_installer_fixtures.py`, `test_aegis_mcp_server.py`, `test_aegis_mcp_contract_docs.py`, and Task 111’s `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py`. These prove installer correctness, MCP wrapper equivalence, and isolated temp-target behavior, but not package-style invocation or external-project MCP configuration.

Implementation approach:
1. Create Task 112 work-tracking artifacts before implementation, including option analysis, selected contract, evidence, and follow-up recommendations. Use an active folder such as `docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/` with `DECISIONS.md`, `FINDINGS.md`, `IMPLEMENTATION.md`, `HANDOFF.md`, and a design note such as `designs/aegis-invocation-contract.md`.
2. Define the supported V1 invocation contract explicitly. It should include at least these two forms: a development/local-checkout form using absolute paths from an external project cwd, and one package-style form if practical. The development form should look like `python3 /path/to/codex/scripts/codex-task aegis inspect --target-dir .`, `plan-install`, `install --apply`, and `verify`, plus MCP startup through `python3 /path/to/codex/scripts/aegis-mcp-server --source-root /path/to/codex --default-target-dir /path/to/project`. The package-style form should prefer local installable console scripts, for example `aegis ...` and `aegis-mcp-server ...` exercised through a local wheel/editable install, `uvx --from <local path or wheel> aegis ...`, `pipx run --spec <local path or wheel> aegis ...`, or a documented `python -m ...` module entrypoint if console scripts are not practical in this slice.
3. Preserve the existing architecture. Do not move installer semantics out of `scripts/_aegis_installer.py`. Keep `scripts/codex-task aegis ...` as the local repository wrapper. Keep `aegis_mcp/server.py` as the MCP wrapper/control plane. If a package-style CLI is added, implement it as a thin wrapper over `scripts._aegis_installer`; if argument handling would otherwise diverge from `scripts/codex-task`, extract only the small shared Aegis parser/dispatch layer needed to keep behavior consistent.
4. Add a package-ready Aegis CLI surface. A likely implementation is a small importable module such as `aegis_cli` or `aegis_foundation.cli` with `inspect`, `plan-install`, `install`, `verify`, `list-profiles`, and `explain-profile` subcommands mirroring the existing `scripts/codex-task aegis` JSON outputs and exit-code semantics. The package entrypoint should default `--target-dir` to the caller’s current working directory, not to this source repository, and should resolve Aegis source assets from either an explicit `--source-root`/`AEGIS_SOURCE_ROOT` override or the installed package’s bundled asset root.
5. Update packaging metadata only as far as needed for local package-style execution. If console scripts are chosen, update `pyproject.toml` with the minimal build backend and `[project.scripts]` entries for `aegis` and `aegis-mcp-server`, and change or justify the existing `[tool.uv] package = false` setting. Include required package data for schemas, gate scripts, local helper scripts, and adapter entrypoint assets. Do not publish to PyPI or any public registry in this task, and document any provisional package name as non-final if naming remains undecided.
6. Make MCP startup configurable from external projects. Ensure the selected package/dev contract can start the same `aegis_mcp.server:main` path and can run `--describe-config` from a temp project. Generate or document safe MCP configuration snippets for external projects, distinguishing local checkout from packaged invocation. Snippets should set an explicit target directory or document how the MCP client’s project cwd is resolved, and should avoid writing source-repository absolute paths into target `.aegis/` state except where the development snippet intentionally names the local checkout command.
7. Update user-facing documentation. Add or update a stable document such as `docs/aegis/invocation-contract.md` plus the Task 112 design note. Include copy-pasteable first-adoption commands for development checkout and package-style invocation; commands for `inspect`, `plan-install`, `install --apply`, `verify`, and MCP server configuration/startup; safety notes for `--apply` and MCP `acknowledge_report_write`; and a clear distinction between installed-target commands such as `python3 scripts/codex-task aegis verify` and external package/dev invocations.
8. Adjust existing embedded contract text only where necessary. Review `_render_contract`, `profile_payload`, manifest interface fields, and documentation tests for hard-coded `python3 scripts/codex-task aegis ...` assumptions. Preserve backward compatibility for installed Codex adapter targets, but add the new external invocation command names where the contract needs to describe adoption from outside the source repo.
9. Add explicit non-goals and follow-up boundaries. Do not implement public release publishing, automatic update migrations, rollback, hosted services, package signing, CI install templates, or a second installer engine. Document upgrade and rollback as the next distribution hardening work after the invocation contract is tested.
10. Record evidence and recommendation in work tracking. Include the option matrix, selected invocation forms, command evidence, any packaging limitations discovered, and the recommended next task for release/publish or update/rollback hardening. Refresh Taskmaster-generated artifacts with the narrow `python3 scripts/codex-task taskmaster generate-one --id 112` flow after status updates, and avoid broad generated-file refreshes unless explicitly scoped.

**Test Strategy:**

Add a focused invocation-contract test module, likely `tests/meta_workflow_guard/test_aegis_invocation_contract.py`, and keep Task 111 regression coverage green.

Required focused tests:
- Development checkout invocation: create a fresh external project under `tmp_path`, set subprocess `cwd` to that external project, and run `python3 <repo>/scripts/codex-task aegis inspect --target-dir .`, `plan-install --target-dir . --primary-agent claude --agent claude`, `install --target-dir . --primary-agent claude --agent claude --apply`, and `verify --target-dir .`. Assert JSON stdout, expected statuses, no mutation for inspect/plan, `.aegis/foundation-manifest.json`, `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, `.aegis/reports/verification-report.json`, copied schemas, gate files, and byte-for-byte preservation of seeded user files.
- Package-style invocation: exercise the exact selected contract from an external project cwd, not `cwd=REPO_ROOT`. If console scripts are selected, build or install the local package in a temp environment and run `aegis inspect`, `aegis plan-install`, `aegis install --apply`, and `aegis verify`. If `uvx`, `pipx`, or `python -m` is selected instead, the test must use that exact form and document why it is the V1 package-style contract. Assert the same filesystem and JSON behavior as the checkout path.
- Source-root resolution: verify package/dev commands do not require the caller to be inside `/home/loucmane/codex`; verify explicit `--source-root` or `AEGIS_SOURCE_ROOT` works for development checkout, and verify packaged invocation resolves bundled assets without copying or importing from the source checkout unless that is the documented development mode.
- Path leak guard: after install and verify, scan target `.aegis/` reports and generated project-facing docs for unintended absolute source repository paths such as `/home/loucmane/codex`. Allow only explicitly documented development MCP snippets outside installed target state.
- MCP external startup: from a fresh external target, run the selected dev and package MCP commands with `--describe-config` and assert resolved `source_root` and `default_target_dir` are correct. Add at least one stdio smoke using the existing `mcp.client.stdio` pattern from `tests/meta_workflow_guard/test_aegis_mcp_server.py` to list the `aegis.*` tools/resources/prompts or call `aegis.inspect` against the external target.
- MCP snippet documentation: add doc tests similar to `tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py` that assert the external-project snippets include the selected local checkout command, the selected package-style command, explicit target/source-root guidance, and no stale `foundation.*` or `foundation://` naming.
- Backward compatibility: run existing Task 111 smoke and Aegis regression coverage unchanged, especially `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py`, `test_aegis_installer.py`, `test_aegis_installer_fixtures.py`, `test_aegis_mcp_server.py`, `test_aegis_mcp_contract_docs.py`, and `test_aegis_schemas.py`.

Suggested command coverage:
- `python -m pytest tests/meta_workflow_guard/test_aegis_invocation_contract.py`
- `python -m pytest tests/meta_workflow_guard/test_aegis_cross_project_smoke.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py tests/meta_workflow_guard/test_aegis_schemas.py`
- If package metadata is changed, include a local package/install smoke such as a temp venv install, local wheel install, `uvx --from <local path or wheel>`, `pipx run --spec <local path or wheel>`, or the selected `python -m` invocation.
- Final workflow gates: `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`. Capture all evidence under the Task 112 work-tracking reports directory.

## Subtasks

### 112.1. Reconcile Aegis invocation scope and select the V1 contract

**Status:** done  
**Dependencies:** None  

Create the Task 112 scope record, option matrix, and selected external invocation contract before implementation.

**Details:**

Use the current boundaries confirmed in the codebase: installer semantics remain in `scripts/_aegis_installer.py`, the repository CLI wrapper is `scripts/codex-task` with `REPO_ROOT` derived from the script path, MCP startup is `aegis_mcp/server.py` plus `scripts/aegis-mcp-server`, and `pyproject.toml` currently has `[tool.uv] package = false` with no console scripts. Create `docs/ai/work-tracking/active/20260517-task112-aegis-packaging-invocation-contract-ACTIVE/` with `DECISIONS.md`, `FINDINGS.md`, `IMPLEMENTATION.md`, and `HANDOFF.md`, plus `designs/aegis-invocation-contract.md`. Record an option matrix for absolute local-checkout commands, local editable or wheel console scripts, `python -m` module invocation, `uvx --from`, and `pipx run --spec`; select the V1 supported forms and explicitly mark public publishing, automatic update migration, rollback implementation, package signing, hosted services, CI install templates, and a second installer engine as out of scope.

### 112.2. Add external-cwd local-checkout CLI tests and adoption docs

**Status:** done  
**Dependencies:** 112.1  

Prove the existing local checkout commands work when launched by absolute path from a fresh external project directory.

**Details:**

Create focused coverage, likely in `tests/meta_workflow_guard/test_aegis_invocation_contract.py`, that creates a temp target project and runs subprocesses with `cwd` set to that project rather than `REPO_ROOT`. Invoke commands through absolute paths such as `python3 /path/to/codex/scripts/codex-task aegis inspect --target-dir .`, `plan-install --target-dir . --primary-agent claude --agent claude`, `install --target-dir . --primary-agent claude --agent claude --apply`, and `verify --target-dir .`. Assert JSON stdout, expected exit codes, no dependence on relative `scripts/codex-task`, correct target-root resolution, no source repository mutation, and expected `.aegis/` reports in the target. Add the same copy-pasteable local-development workflow to `docs/aegis/invocation-contract.md` and the Task 112 design note, clearly distinguishing external adoption commands from installed-target commands such as `python3 scripts/codex-task aegis verify`.

### 112.3. Implement package-style Aegis CLI entrypoint or module path

**Status:** done  
**Dependencies:** 112.1, 112.2  

Add a package-ready invocation surface that mirrors the existing Aegis argparse behavior without duplicating installer logic.

**Details:**

Introduce a thin importable CLI layer, for example `aegis_cli` or `aegis_foundation.cli`, that exposes `inspect`, `plan-install`, `install`, `verify`, `list-profiles`, and `explain-profile` while delegating to `scripts._aegis_installer`. Keep JSON output and failure semantics aligned with `scripts/codex-task aegis`, including refused install and failed verify exit behavior. Resolve `--target-dir` relative to the caller cwd and default it to `.`, not the source repository. Resolve source assets from explicit `--source-root`, `AEGIS_SOURCE_ROOT`, or the installed package asset root. Update `pyproject.toml` minimally for local package execution, including a build backend, package discovery, `[project.scripts]` entries such as `aegis` and possibly `aegis-mcp-server`, and package data for schemas, helper scripts, Claude gate scripts, and adapter assets. If console scripts prove too broad for this slice, provide a tested `python -m ...` entrypoint and document why it is the selected package-style V1 path.

### 112.4. Define and test external MCP startup and configuration snippets

**Status:** done  
**Dependencies:** 112.1, 112.2, 112.3  

Extend the invocation contract to cover MCP startup from external projects for both local-checkout and package-style forms.

**Details:**

Preserve `AegisMCPConfig.from_paths`, `--source-root`, `--default-target-dir`, `AEGIS_SOURCE_ROOT`, and `AEGIS_DEFAULT_TARGET_DIR` as the MCP configuration contract. Add tests proving `python3 /path/to/codex/scripts/aegis-mcp-server --source-root /path/to/codex --default-target-dir /path/to/project --describe-config` works from an external project cwd, then add equivalent coverage for the selected package-style startup such as `aegis-mcp-server --default-target-dir . --describe-config` or `python -m ...`. Document safe MCP configuration snippets for external projects in `docs/aegis/invocation-contract.md`, including explicit target directory handling and MCP client cwd assumptions. Review contract-producing surfaces such as `_render_contract`, `profile_payload`, manifest interface fields, schema checks, and documentation tests for hard-coded `python3 scripts/codex-task aegis ...` assumptions; preserve installed Codex adapter compatibility while adding external command names where the adoption contract needs them.

### 112.5. Capture final evidence, refresh Taskmaster state, and hand off release follow-up

**Status:** done  
**Dependencies:** 112.1, 112.2, 112.3, 112.4  

Close Task 112 with evidence, documentation, generated artifacts, and a recommendation for the next distribution-hardening task.

**Details:**

Update Task 112 work-tracking files with the selected invocation forms, command evidence, package limitations, MCP snippet behavior, safety notes for `install --apply` and MCP `acknowledge_report_write`, and the exact non-goals. Ensure `docs/aegis/invocation-contract.md` and `designs/aegis-invocation-contract.md` contain first-adoption commands for `inspect`, `plan-install`, `install --apply`, `verify`, and MCP startup/configuration. Record the recommended next task for public release/publish hardening or update/rollback design without implementing those items. Use Taskmaster status or progress updates as appropriate and refresh only Task 112 generated output with `python3 scripts/codex-task taskmaster generate-one --id 112`; avoid broad `task-master generate` unless explicitly scoped.
