# Aegis Release Verification Matrix

This matrix defines the minimum release-readiness coverage for `aegis-foundation`.

## Dimensions

| Dimension | Required Values |
| --- | --- |
| OS | `ubuntu-latest`, `macos-latest` |
| Python | `3.11`, `3.12` |
| Install method | `pip`, `uvx`, `pipx`, `local-wheel`, `editable` |
| Command surface | `aegis`, `aegis-mcp-server` |
| CLI operations | `aegis --version`, `aegis inspect`, `aegis status`, `aegis plan-install`, `aegis install --apply`, `aegis verify` |
| MCP operations | `aegis-mcp-server --describe-config`, stdio startup, `aegis.inspect`, `aegis.status`, tool/resource/prompt discovery |
| Asset origin | `package`, `source` |
| Connectivity | online package resolution, offline/local wheel |
| Target shape | empty repo, Python/library repo, web/app repo, docs-heavy Task 101-style repo, partial existing Aegis install |
| Evidence | install plan, install report, verification report, build log, package artifact list, MCP config output |

## Required Checks

Every release candidate must prove:

- packaged assets are used when no `--source-root` or `AEGIS_SOURCE_ROOT` is supplied
- source checkout assets are used only when explicitly requested
- local wheel invocation works without `/home/loucmane/codex`
- `uvx --from aegis-foundation==0.1.0` works for CLI snippets after publication
- `pipx run --spec aegis-foundation==0.1.0` works for CLI snippets after publication
- `aegis-mcp-server --describe-config` reports `asset_origin=package` from installed packages
- MCP stdio startup lists tools, resources, and prompts
- MCP `aegis.inspect` and `aegis.status` are read-only
- `aegis.install` requires explicit `--apply` / MCP `apply=true`
- `aegis.verify` writes and preserves `.aegis/reports/verification-report.json`
- release policy covers signing, provenance, checksums, prereleases, update, rollback, and downgrade

## Target Repository Shapes

The release suite should reuse the Task 111 target-shape coverage:

- empty repository
- Python/library repository with `pyproject.toml`, README, and `src/...`
- web/app repository with `package.json`, app/source directories, and existing docs
- docs-heavy Task 101-style repository
- partial existing Aegis install with `.aegis/foundation-manifest.json`, `.aegis/contract.md`, or adapter files already present

## Evidence Paths

Release evidence must include these target-side reports when applicable:

```text
.aegis/reports/install-plan.json
.aegis/reports/install-report.json
.aegis/reports/verification-report.json
```

Task work-tracking evidence must include:

```text
reports/aegis-release-hardening/build-*.txt
reports/aegis-release-hardening/artifacts-*.txt
reports/aegis-release-hardening/tests-*.txt
reports/aegis-release-hardening/mcp-describe-*.txt
reports/aegis-release-hardening/status-*.txt
```

## Release Decision

A release candidate is not ready until every required dimension has either:

- passing automated evidence, or
- a documented deferral with owner, risk, and follow-up task.

Policy-only claims are not release evidence.
