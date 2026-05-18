# Task ID: 113

**Title:** Aegis Release Hardening and Distribution Readiness

**Status:** done

**Dependencies:** 112 ✓

**Priority:** medium

**Description:** Harden the Aegis foundation installer and MCP server from the Task 112 local checkout/editable invocation contract into a production-ready release and distribution contract. Preserve the existing local checkout and editable package paths while adding public-package metadata, bundled assets, external install invocations, release policy, update/rollback guidance, MCP startup guidance, CI templates, verification matrix, and documentation.

**Details:**

Codebase analysis summary: Task 112 is complete and introduced `aegis_foundation/cli.py`, `aegis_mcp/server.py`, console scripts in `pyproject.toml` (`aegis` and `aegis-mcp-server`), `docs/aegis/invocation-contract.md`, and `tests/meta_workflow_guard/test_aegis_invocation_contract.py`. The current implementation is still explicitly development-oriented: `docs/aegis/invocation-contract.md` says wheel assets, `uvx`, `pipx`, signing, update migrations, rollback, hosted services, and CI install templates are deferred; `aegis_foundation/cli.py` resolves assets from `--source-root`, `AEGIS_SOURCE_ROOT`, or the editable checkout parent chain and raises an error that bundled wheel assets are deferred; `aegis_mcp/server.py` defaults `source_root` to the repository root and exposes deferred tools such as `aegis.plan_update`, `aegis.update`, and `aegis.rollback` only as limitations; `pyproject.toml` still uses the provisional distribution name `codex-starter-pack`, version `0.1.0`, `[tool.uv] package = false`, and does not declare package-data/resource bundling for top-level `schemas/`, `templates/`, `.claude/scripts/`, `docs/aegis/`, or installer-managed helper assets. Existing relevant tests include `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py`, `test_aegis_invocation_contract.py`, `test_aegis_mcp_server.py`, `test_aegis_mcp_contract_docs.py`, `test_aegis_installer.py`, `test_aegis_installer_fixtures.py`, and `test_aegis_schemas.py`.

Implementation approach: 1. Create Task 113 work-tracking artifacts under a new active folder such as `docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/` with `FINDINGS.md`, `DECISIONS.md`, `IMPLEMENTATION.md`, `HANDOFF.md`, `TRACKER.md`, a design note such as `designs/aegis-release-distribution-contract.md`, and a reports directory. Record that Task 113 extends, not replaces, the Task 112 local checkout and editable package invocation contract.

2. Decide and document the public distribution identity. Update `pyproject.toml` metadata from the provisional `codex-starter-pack` state to the selected public package contract, likely a distribution name such as `aegis-foundation` while keeping import packages `aegis_foundation` and `aegis_mcp` and console commands `aegis` and `aegis-mcp-server`. Add or confirm `description`, `readme`, `license`, `authors` or `maintainers`, `requires-python`, classifiers, keywords, project URLs, and supported Python versions. Keep command names stable unless there is a documented collision or naming risk.

3. Make versioning single-source and release-aware. Reconcile `pyproject.toml` version with `scripts/_aegis_installer.py` constants (`FOUNDATION_VERSION`, `INSTALLER_VERSION`, and `SCHEMA_VERSION`) and package `__init__` metadata. Add a small version/reporting surface if needed, for example `aegis --version` and an MCP/server diagnostic field, while preserving existing JSON output for installer subcommands. Document semver rules for CLI/MCP behavior, schema changes, managed asset changes, and prerelease builds in a release policy document such as `docs/aegis/release-policy.md`.

4. Implement wheel-safe asset resolution. Replace the current packaged-mode requirement for a checkout source root with a package resource resolver that can serve the same relative assets currently read by `scripts/_aegis_installer.py`: `schemas/aegis/*.schema.json`, managed Claude files such as `.claude/scripts/readiness.sh` and `.claude/scripts/pretooluse-gate.sh`, Codex helper files such as `scripts/codex-task`, `scripts/codex-guard`, `scripts/_repo_structure.py`, `scripts/template_registry.py`, `scripts/template_governance.py`, `scripts/template_versioning.py`, template/docs/config assets needed by the foundation contract, and `docs/aegis/*`. Prefer an explicit `aegis_foundation.assets` or `aegis_foundation.resources` layer using `importlib.resources` or a deterministic materialized asset root. Keep `--source-root` and `AEGIS_SOURCE_ROOT` working for checkout/development mode, but make normal wheel installs work without access to `/home/loucmane/codex`.

5. Update packaging configuration. Adjust `pyproject.toml` and, if necessary, add `MANIFEST.in` or setuptools package-data configuration so source distributions and wheels include every required asset. Revisit `[tool.uv] package = false`; for release readiness it should either be removed/changed or explicitly justified with a separate build path. Preserve `scripts` importability only if still required by existing tests and installed targets; avoid creating a second installer engine. Ensure executable helper scripts keep usable permissions or are written with explicit chmod handling during install.

6. Add public install and invocation documentation. Extend `docs/aegis/invocation-contract.md` or split release material into `docs/aegis/distribution.md`. Include production snippets for `pip install`, `pipx install` or `pipx run --spec`, and `uvx --from` for both CLI and MCP startup. Include local wheel snippets such as `uvx --from dist/<wheel> aegis ...` and `pipx run --spec dist/<wheel> aegis ...` for verification before publication, plus public snippets such as `uvx --from aegis-foundation aegis inspect --target-dir .` once the package name is selected. Preserve existing Task 112 local checkout snippets (`python3 /path/to/codex/scripts/codex-task ...`) and editable install snippets as supported development paths.

7. Harden MCP distribution guidance and startup discovery. Update `aegis_mcp/server.py` and docs so packaged `aegis-mcp-server --describe-config` correctly reports a bundled/source asset origin and a target directory from external cwd. Add MCP client snippets for local/offline stdio startup, `uvx` startup, `pipx` startup, and hosted/remote service guidance. If hosted MCP is not implemented in this task, document it as a policy-supported deployment pattern with clear transport, authentication, upgrade, and evidence requirements rather than pretending it is available. Keep existing `--transport` choices (`stdio`, `streamable-http`, `sse`) accurate and tested where possible.

8. Define update, migration, and rollback flows. At minimum, document the V1 operational flow for upgrading the Aegis package, checking installed target manifest/schema versions, re-running `plan-install`, applying reviewed changes, verifying, and rolling back through git or recorded backups. If feasible within scope, add read-only `aegis status` or `aegis plan-update` support that compares the target `.aegis/foundation-manifest.json` with the package versions and reports whether migration is needed; only add mutating update/rollback commands if they can reuse the existing installer safety model and have deterministic tests. Update MCP limitations/resources so deferred tool names remain honest.

9. Establish signing and release policy. Add release documentation covering artifact signing, provenance, and verification. Prefer a concrete policy such as Sigstore keyless signing for release artifacts, GitHub release provenance, checksum publication, and version-pinned install snippets. The task does not need to publish a package, but it must define what a signed release means and how downstream users verify the wheel/sdist before using `pipx` or `uvx`.

10. Add CI install templates and a release verification matrix. Provide reusable workflow snippets or templates under an appropriate docs or template path, for example `docs/aegis/ci-install-templates.md` or `templates/integration/cross-system/aegis-ci-install.md`, showing how projects install and verify Aegis in GitHub Actions using pinned versions, `pipx`, `uvx`, and local wheel artifacts. Add a matrix document covering OS, Python version, install method (`pip`, `pipx`, `uvx`, local wheel, editable), command surface (`aegis`, `aegis-mcp-server`), online/offline behavior, and target repo shapes from Task 111.

11. Keep installed-target compatibility intact. Do not remove or break `scripts/codex-task aegis ...`, generated target helper files, the existing Aegis manifest/report paths (`.aegis/foundation-manifest.json`, `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, `.aegis/reports/verification-report.json`), or MCP tool names already exposed by `aegis_mcp/server.py`. Any docs or code that now mention production package invocation must clearly distinguish external management commands from commands installed into target projects.

12. Close with tracked evidence. Update Taskmaster status/progress with implementation notes, refresh only Task 113 generated output via `python3 scripts/codex-task taskmaster generate-one --id 113` after status changes, and store command evidence for package build/install checks, package-data checks, MCP startup checks, docs checks, plan sync, Taskmaster health, work-tracking audit, codex guard, and diff-check under the Task 113 reports directory.

**Test Strategy:**

Create focused release-hardening coverage while keeping Task 111 and Task 112 regressions green. Required tests and evidence:

1. Packaging metadata tests: add a focused module such as `tests/meta_workflow_guard/test_aegis_release_distribution.py` that parses `pyproject.toml` and asserts the selected public package name, console scripts (`aegis`, `aegis-mcp-server`), required metadata, Python version, dependencies, package discovery, and package-data configuration are present. Assert the documented package name and command names match docs.

2. Wheel/sdist build tests: build artifacts using the selected local build command, for example `python -m build` or `uv build`, then inspect the wheel and sdist contents with `zipfile`/`tarfile`. Assert required assets are bundled: `schemas/aegis/*.schema.json`, Aegis docs, foundation templates/config assets, `.claude/scripts/*` needed by installs, Codex helper scripts, and MCP/server package modules. Assert stale checkout-only assumptions such as requiring `/home/loucmane/codex` are absent from packaged asset resolution.

3. External wheel install tests: create a temp venv outside the repository, install the built wheel, and from a fresh external target cwd run `aegis inspect --target-dir .`, `aegis plan-install --target-dir . --primary-agent claude --agent claude`, `aegis install --target-dir . --primary-agent claude --agent claude --apply`, and `aegis verify --target-dir .` without setting `AEGIS_SOURCE_ROOT`. Assert JSON output, expected statuses, no mutation for inspect/plan, generated `.aegis/` reports, copied schemas/gate files, preserved user files, and no absolute source-checkout path leaks in target `.aegis/` reports or generated project-facing docs.

4. `uvx` and `pipx` invocation evidence: where the tools are available in CI/local test environment, run local wheel or local path invocations from outside the repo, for example `uvx --from <wheel-or-project> aegis --version`, `uvx --from <wheel-or-project> aegis inspect --target-dir .`, and equivalent `pipx run --spec <wheel-or-project> aegis ...`. If either tool is not available, add deterministic docs/tests that validate snippets and record the skipped runtime evidence with a clear reason. Include public-package snippets in docs but verify local wheel snippets before publication.

5. Packaged MCP startup tests: from an external target, run installed `aegis-mcp-server --describe-config` and assert the target directory resolves to the external project and the asset/source origin is bundled or otherwise valid without checkout access. Add at least one stdio smoke using the existing `mcp.client.stdio` pattern from `tests/meta_workflow_guard/test_aegis_invocation_contract.py` to list `V1_TOOL_NAMES`, `RESOURCE_URIS`, and `PROMPT_NAMES`, and to call `aegis.inspect` against the external target. Add coverage for any documented `uvx` or `pipx` MCP startup form if feasible.

6. Package-data availability tests: exercise `aegis list-profiles`, `aegis explain-profile`, `aegis plan-install`, and `aegis verify` from an installed wheel after temporarily hiding or ignoring the source checkout. These tests must prove schemas and managed assets come from the package, not from the repository working tree. Include a negative test for missing/corrupt packaged assets if the resolver has explicit error handling.

7. Update/rollback documentation and optional command tests: if a read-only `status` or `plan-update` command is added, test installed, outdated, and mismatched manifest cases. If update/rollback remains guidance only, add documentation tests asserting `docs/aegis/release-policy.md` or `docs/aegis/distribution.md` includes version-pinning, upgrade, migration, rollback, and downgrade guidance, plus clear warnings about reviewed plans and git/backups.

8. Signing and release policy tests: add documentation/metadata tests asserting release policy covers semver, artifact signing, provenance, checksum verification, prerelease handling, and supported install channels. If signing automation is added, run the non-publishing verification path only, such as artifact checksum generation or signing dry-run, without requiring secret material.

9. CI template tests: add tests similar to existing workflow/doc checks in `tests/meta_workflow_guard/test_ci_workflows.py` and documentation tests that assert CI install templates include pinned version examples, `uvx` or `pipx` install paths, MCP startup where relevant, `aegis verify`, and evidence capture. Ensure snippets do not replace local checkout/editable guidance.

10. Regression suite: run existing Aegis tests unchanged, especially `python -m pytest tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_cross_project_smoke.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py tests/meta_workflow_guard/test_aegis_schemas.py`, plus the new release distribution test module.

11. Final workflow evidence: capture and store `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check` output in the Task 113 work-tracking reports directory. Acceptance requires these evidence files plus docs proving install/invocation from outside the repository, package data availability, MCP startup discovery, and update/rollback guidance.

## Subtasks

### 113.1. Create Task 113 release distribution design and work-tracking baseline

**Status:** done  
**Dependencies:** None  

Create the active Task 113 work-tracking folder and document the release-hardening contract before changing package behavior.

**Details:**

Add `docs/ai/work-tracking/active/20260517-task113-aegis-release-hardening-ACTIVE/` with `FINDINGS.md`, `DECISIONS.md`, `IMPLEMENTATION.md`, `HANDOFF.md`, `TRACKER.md`, `designs/aegis-release-distribution-contract.md`, and a `reports/` directory. Record the current state discovered in `pyproject.toml`, `aegis_foundation/cli.py`, `aegis_mcp/server.py`, `docs/aegis/invocation-contract.md`, and Task 112 handoff notes: local checkout and editable invocation are supported, public wheel assets and release operations are still deferred. Explicitly decide that Task 113 extends the Task 112 contract without replacing `scripts/codex-task aegis ...`, editable installs, existing `.aegis/*` report paths, or current MCP tool names.

### 113.2. Update public package metadata and single-source version contract

**Status:** done  
**Dependencies:** 113.1  

Convert provisional package metadata into a release-aware public distribution contract and align version reporting.

**Details:**

Update `pyproject.toml` from the provisional `codex-starter-pack` state to the selected public distribution identity, likely `aegis-foundation`, while preserving import packages `aegis_foundation` and `aegis_mcp` plus console scripts `aegis` and `aegis-mcp-server`. Add release-grade metadata including description, readme, license, maintainers/authors, Python support, classifiers, keywords, and project URLs. Reconcile `pyproject.toml` version with `aegis_foundation.__version__` and `scripts/_aegis_installer.py` constants (`FOUNDATION_VERSION`, `INSTALLER_VERSION`, `SCHEMA_VERSION`) through a small single-source version module or equivalent deterministic check. Add `aegis --version` and an MCP diagnostic/version field without breaking existing JSON output for installer subcommands.

### 113.3. Implement wheel-safe asset resolver and package data bundling

**Status:** done  
**Dependencies:** 113.2  

Make Aegis installer assets available from installed wheels and sdists without requiring the source checkout path.

**Details:**

Introduce an explicit resource layer such as `aegis_foundation/resources.py` or `aegis_foundation/assets.py` using `importlib.resources` or a deterministic materialized asset root. Preserve `--source-root` and `AEGIS_SOURCE_ROOT` for checkout and editable development mode, but make default packaged mode resolve bundled assets instead of raising the current deferred wheel-assets error in `aegis_foundation/cli.py`. Update `pyproject.toml` package-data configuration and add `MANIFEST.in` if needed so wheels and sdists include `schemas/aegis/*.schema.json`, managed `.claude/scripts/*` helper assets required by `_aegis_installer.py`, Codex helper files such as `scripts/codex-task`, `scripts/codex-guard`, `_repo_structure.py`, `template_registry.py`, `template_governance.py`, `template_versioning.py`, relevant `templates/registry/*` assets, and `docs/aegis/*`. Revisit `[tool.uv] package = false` and either remove/change it for release builds or document an explicit alternate build path. Ensure executable managed helper files retain executable behavior via package metadata or installer chmod handling.

### 113.4. Verify external installed CLI invocation and document public install snippets

**Status:** done  
**Dependencies:** 113.3  

Prove the `aegis` console command works from a built wheel and document supported external install methods.

**Details:**

Extend `docs/aegis/invocation-contract.md` or add `docs/aegis/distribution.md` with production install and invocation examples for `pip install`, `pipx install` or `pipx run --spec`, `uvx --from`, local wheel invocation (`uvx --from dist/<wheel> aegis ...`, `pipx run --spec dist/<wheel> aegis ...`), and the selected public package name (`uvx --from aegis-foundation aegis inspect --target-dir .`). Preserve existing Task 112 local checkout and editable snippets as supported development paths. Add local-wheel CLI smoke coverage that installs the built artifact into an isolated environment or invokes it through available tooling, runs `aegis inspect`, `plan-install`, `install --apply`, and `verify` from an external target cwd, and confirms no installed target reports leak the source checkout path. For `uvx` and `pipx`, run real checks when available and record explicit skip evidence when the binary or offline constraints prevent execution.

### 113.5. Harden packaged MCP startup and asset-origin discovery

**Status:** done  
**Dependencies:** 113.3  

Make `aegis-mcp-server` report and use bundled assets correctly when started from an installed package.

**Details:**

Update `aegis_mcp/server.py` so `AegisMCPConfig.from_paths()` can use the same asset resolver as the CLI and report a clear asset origin such as `source` or `package` in `--describe-config`. Preserve explicit `--source-root`, `AEGIS_SOURCE_ROOT`, `--default-target-dir`, and `AEGIS_DEFAULT_TARGET_DIR`, but make packaged startup from an external cwd resolve the default target directory independently from the package asset root. Keep existing transports (`stdio`, `streamable-http`, `sse`) accurate. Update MCP docs with local/offline stdio, local wheel, `uvx`, `pipx`, and hosted/remote deployment guidance; if hosted MCP is not implemented, describe it as a policy-supported deployment pattern with transport, authentication, upgrade, and evidence requirements rather than as an available service. Ensure schema/resource reads such as `aegis://schemas/foundation-manifest` come from bundled or source assets consistently.

### 113.6. Define update rollback migration and signing release policy

**Status:** done  
**Dependencies:** 113.2, 113.3  

Document and, where safely scoped, implement read-only release lifecycle surfaces for upgrades and rollbacks.

**Details:**

Add release lifecycle documentation such as `docs/aegis/release-policy.md` and `docs/aegis/update-rollback.md` covering semver rules for CLI, MCP, schema, and managed asset changes; prerelease builds; package upgrade flow; manifest/schema version checks; `plan-install` review before applying changed assets; verification after upgrades; rollback through git or recorded backups; and no direct writes to `.aegis/`. Define artifact signing and provenance policy using concrete mechanisms such as Sigstore keyless signing, GitHub release provenance, checksums, and version-pinned install snippets. If it can reuse the current installer safety model deterministically, add read-only `aegis status` or `aegis plan-update` support that compares `.aegis/foundation-manifest.json` with packaged versions and reports migration needs without mutating the target. Keep MCP `aegis://limitations` honest by either exposing matching read-only tools or retaining deferred `aegis.update` and `aegis.rollback` limitations clearly.

### 113.7. Add CI install templates and release verification matrix

**Status:** done  
**Dependencies:** 113.4, 113.5, 113.6  

Provide reusable CI guidance and a matrix that defines what release readiness must prove.

**Details:**

Create `docs/aegis/ci-install-templates.md`, `docs/aegis/release-verification-matrix.md`, or an equivalent template path such as `templates/integration/cross-system/aegis-ci-install.md`. Include GitHub Actions snippets for pinned public package installs, local wheel artifact verification, `pip`, `pipx`, and `uvx` paths, plus commands for `aegis --version`, `aegis inspect`, `aegis plan-install`, `aegis verify`, and `aegis-mcp-server --describe-config`. The verification matrix should cover OS, Python version, install method (`pip`, `pipx`, `uvx`, local wheel, editable), command surface (`aegis`, `aegis-mcp-server`), online/offline behavior, bundled asset checks, MCP startup mode, and representative target repository shapes from Task 111.

### 113.8. Run final release hardening regressions and archive handoff evidence

**Status:** done  
**Dependencies:** 113.1, 113.2, 113.3, 113.4, 113.5, 113.6, 113.7  

Collect final evidence, update Taskmaster state, and prepare a complete handoff for Task 113 completion.

**Details:**

Run the focused Aegis release-hardening tests plus existing regressions such as `test_aegis_invocation_contract.py`, `test_aegis_cross_project_smoke.py`, `test_aegis_mcp_server.py`, `test_aegis_mcp_contract_docs.py`, `test_aegis_installer.py`, `test_aegis_installer_fixtures.py`, and `test_aegis_schemas.py`. Store command outputs under the Task 113 reports directory for package build/install checks, package-data/archive checks, local wheel CLI checks, MCP startup checks, docs checks, Taskmaster health, work-tracking audit, codex guard, and diff-check. Update Taskmaster implementation notes and statuses through commands rather than manual `tasks.json` edits, then refresh only Task 113 generated output with `python3 scripts/codex-task taskmaster generate-one --id 113`. Finish `HANDOFF.md`, `IMPLEMENTATION.md`, `FINDINGS.md`, `DECISIONS.md`, and `TRACKER.md` with exact evidence paths and any deferred publication items, without publishing to PyPI as part of this task.
