# Task 113 Aegis Release Hardening and Distribution Readiness – Implementation Notes

## Planned Workstreams
- `113.2` — Public package metadata and single-source version contract.
- `113.3` — Wheel-safe asset resolver and package-data bundling.
- `113.4` — External installed CLI invocation and public install snippets.
- `113.5` — Packaged MCP startup and asset-origin discovery.
- `113.6` — Update, rollback, migration, and signing release policy.
- `113.7` — CI install templates and release verification matrix.
- `113.8` — Final release-hardening regressions and handoff evidence.

## Startup Notes
- `113.1` completed the release/distribution contract baseline in `designs/aegis-release-distribution-contract.md`.
- Implementation starts with `113.2` because public package identity and versioning shape the later wheel, `uvx`, `pipx`, and MCP packaged startup behavior.

## 113.2 Progress
- Updated `pyproject.toml` from provisional `codex-starter-pack` metadata to the working public distribution identity `aegis-foundation`.
- Added release metadata: readme, license text, authors/maintainers, keywords, classifiers, project URLs, and stable console scripts.
- Added `aegis_foundation.version` as the package identity/version module and aligned `aegis_foundation.__version__`, installer foundation/install versions, and schema version constants through imports and tests.
- Added `aegis --version` without changing existing JSON output for installer subcommands.
- Added MCP `--describe-config` diagnostic fields for distribution name, foundation version, installer version, and schema version.
- Updated invocation-contract docs with release package identity and version diagnostic expectations.
- Added `tests/meta_workflow_guard/test_aegis_release_distribution.py` and updated invocation-contract MCP assertions.

## Evidence
- `reports/aegis-release-hardening/tests-2026-05-17-release-metadata.txt` — `13 passed` for release-distribution and invocation-contract coverage.

## 113.3 Progress
- Added `aegis_foundation/assets/` as the packaged Aegis asset root, populated with schemas, Claude gate scripts, Codex helper scripts, the Aegis invocation doc, and compatibility matrix data needed by installer/MCP behavior.
- Added `aegis_foundation.resources` for package resource access.
- Updated package configuration with `MANIFEST.in`, setuptools namespace package discovery, and explicit package-data globs including hidden `.claude` assets.
- Updated the package CLI to fall back to packaged assets when no checkout source root is supplied.
- Updated MCP config defaults to use packaged assets when no `--source-root` or `AEGIS_SOURCE_ROOT` is supplied.
- Added `scripts/_aegis_installer.py` to Codex-managed install assets so target-side `scripts/codex-task` has its Aegis dependency.
- Added a root `README.md` and SPDX-style license expression to remove release build warnings.
- Verified wheel and sdist artifacts include required Aegis runtime assets.

## 113.3 Evidence
- `reports/aegis-release-hardening/tests-2026-05-17-package-assets.txt` — `15 passed` for package-data and invocation-contract coverage.
- `reports/aegis-release-hardening/build-2026-05-17-package-assets.txt` — local wheel/sdist build evidence.
- `reports/aegis-release-hardening/artifacts-2026-05-17-package-assets.txt` — wheel/sdist asset inspection evidence.

## 113.4 Progress
- Added `docs/aegis/distribution.md` with local wheel, public `pip`, `uvx`, `pipx`, installed CLI, installed MCP, and hosted-service guidance.
- Linked `docs/aegis/invocation-contract.md` to the distribution contract while preserving Task 112 development checkout and editable package guidance.
- Added distribution snippet assertions and an opt-in local wheel CLI smoke in `tests/meta_workflow_guard/test_aegis_release_distribution.py`.
- Verified the built wheel installs into a temp venv and runs `aegis --version`, `inspect`, `plan-install`, `install --apply`, and `verify` from an external target without `AEGIS_SOURCE_ROOT`.
- Verified local wheel `uvx --from` and `pipx run --spec` invocations.

## 113.4 Evidence
- `reports/aegis-release-hardening/tests-2026-05-17-distribution-docs.txt` — default distribution docs and invocation regressions (`16 passed, 1 skipped`).
- `reports/aegis-release-hardening/tests-2026-05-17-local-wheel-cli.txt` — opt-in local wheel CLI smoke (`1 passed`).
- `reports/aegis-release-hardening/uvx-2026-05-17-local-wheel.txt` — local wheel `uvx --from` evidence.
- `reports/aegis-release-hardening/pipx-2026-05-17-local-wheel.txt` — local wheel `pipx run --spec` evidence.

## 113.5 Progress
- Updated `aegis_mcp.server.AegisMCPConfig` so packaged/default startup resolves the asset root from `aegis_foundation.assets`, reports `asset_origin=package`, and uses the external current working directory as the default target.
- Preserved explicit `--source-root` / `AEGIS_SOURCE_ROOT` development behavior with `asset_origin=source`.
- Updated MCP config and entrypoint tests to assert the new release diagnostic payload instead of the old checkout-only payload.
- Added an opt-in local wheel MCP stdio smoke that builds the wheel, starts `aegis-mcp-server` via `uvx --from <wheel>`, lists tools/resources/prompts, and calls `aegis.inspect` against an external target.
- Updated `docs/aegis/distribution.md` with packaged MCP `asset_origin` expectations and local-wheel MCP smoke snippets.

## 113.5 Evidence
- `reports/aegis-release-hardening/build-2026-05-17-mcp-origin.txt` — rebuilt wheel/sdist after MCP package-origin changes.
- `reports/aegis-release-hardening/mcp-describe-2026-05-17-local-wheel.txt` — local wheel `uvx --from` MCP `--describe-config` evidence showing `asset_origin=package` and packaged asset root.
- `reports/aegis-release-hardening/tests-2026-05-17-local-wheel-mcp.txt` — opt-in local wheel MCP stdio smoke (`1 passed`).
- `reports/aegis-release-hardening/tests-2026-05-17-mcp-package.txt` — MCP/distribution regression coverage (`37 passed, 2 skipped`).

## 113.6 Progress
- Added read-only `status` support in `scripts/_aegis_installer.py` to compare installed manifest versions against packaged foundation/installer/schema versions without mutating the target.
- Added package CLI `aegis status --target-dir ...` and local checkout wrapper `python3 scripts/codex-task aegis status --target-dir ...`.
- Added MCP `aegis.status` as a read-only tool and removed it from the deferred-tool list in `aegis://limitations`.
- Added `docs/aegis/release-policy.md` covering semantic versioning, prereleases, signing/provenance, checksums, version pinning, hosted MCP release constraints, and release notes.
- Added `docs/aegis/update-rollback.md` covering update, migration, downgrade, Git-first rollback, direct-write restrictions, and deferred mutating update/rollback commands.
- Updated invocation/distribution docs and packaged docs assets with the `aegis status` flow.

## 113.6 Evidence
- `reports/aegis-release-hardening/tests-2026-05-17-release-policy.txt` — focused release policy, MCP, and invocation coverage (`48 passed, 2 skipped`).
- `reports/aegis-release-hardening/build-2026-05-17-release-policy.txt` — rebuilt wheel/sdist after status and policy docs changed.
- `reports/aegis-release-hardening/tests-2026-05-17-local-wheel-cli.txt` — opt-in local wheel CLI smoke after adding `aegis status` (`1 passed`).
- `reports/aegis-release-hardening/tests-2026-05-17-local-wheel-mcp.txt` — opt-in local wheel MCP smoke after adding `aegis.status` (`1 passed`).
- `reports/aegis-release-hardening/status-2026-05-17-local-wheel.txt` — local wheel `uvx --from` `aegis status` evidence.

## 113.7 Progress
- Added `docs/aegis/ci-install-templates.md` with GitHub Actions snippets for pinned public package installs, `pip`, `uvx`, `pipx`, local wheel release-candidate smoke, editable development installs, MCP `--describe-config`, and evidence upload paths.
- Added `docs/aegis/release-verification-matrix.md` covering OS, Python, install method, command surface, CLI operations, MCP operations, asset origin, connectivity, target repository shapes from Task 111, and required evidence.
- Linked the CI template and release matrix docs from the distribution and release policy docs.
- Packaged the new docs under `aegis_foundation/assets/docs/aegis/`.

## 113.7 Evidence
- `reports/aegis-release-hardening/tests-2026-05-17-ci-matrix.txt` — focused docs/package coverage for CI templates and release matrix (`49 passed, 2 skipped`).
- `reports/aegis-release-hardening/build-2026-05-17-ci-matrix.txt` — rebuilt wheel/sdist after adding the CI and release matrix docs to packaged assets.

## 113.8 Progress
- Removed the stale `[tool.uv] package=false` development marker now that `aegis-foundation` builds and installs as a release package.
- Added a release-distribution assertion preventing `package=false` from returning.
- Ran the final Aegis regression suite and workflow gates after Taskmaster closeout.

## 113.8 Evidence
- `reports/aegis-release-hardening/build-2026-05-17-final.txt` — final wheel/sdist build after release metadata cleanup.
- `reports/aegis-release-hardening/tests-2026-05-17-final-aegis.txt` — final Aegis regression suite (`89 passed, 2 skipped`).
- `reports/aegis-release-hardening/plan-sync-2026-05-17-final.txt` — final plan sync.
- `reports/aegis-release-hardening/taskmaster-health-2026-05-17-final.txt` — final Taskmaster health.
- `reports/aegis-release-hardening/work-tracking-audit-2026-05-17-final.txt` — final work-tracking audit.
- `reports/aegis-release-hardening/guard-2026-05-17-final.txt` — final guard pass.
- `reports/aegis-release-hardening/diff-check-2026-05-17-final.txt` — final diff-check output.
