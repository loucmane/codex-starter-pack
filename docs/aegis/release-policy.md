# Aegis Release Policy

This policy defines how Aegis Foundation releases are versioned, verified, published, and consumed. It complements `docs/aegis/distribution.md`, `docs/aegis/update-rollback.md`, `docs/aegis/ci-install-templates.md`, and `docs/aegis/release-verification-matrix.md`.

## Versioning

Aegis uses semantic versioning for the public package `aegis-foundation`.

- Patch releases fix bugs, documentation, packaging metadata, and non-breaking managed asset updates.
- Minor releases add backward-compatible CLI, MCP, schema, or managed asset capabilities.
- Major releases may introduce incompatible CLI/MCP behavior, schema changes, manifest migrations, or managed asset semantics.
- Prerelease builds use standard prerelease identifiers such as `0.2.0rc1`, `0.2.0b1`, or `1.0.0a1` and must not be used as default production pins.

The following version fields must stay aligned unless a migration note explicitly says otherwise:

- package version: `aegis_foundation.__version__`
- installer version: `.aegis/foundation-manifest.json` field `installer_version`
- foundation version: `.aegis/foundation-manifest.json` field `foundation_version`
- schema version: `.aegis/foundation-manifest.json` field `schema_version`

Schema version changes require a release note entry describing whether existing manifests remain valid and whether `aegis status` reports migration required.

## Artifact Policy

Every release candidate must produce:

- source distribution
- wheel
- checksums for every published artifact
- provenance metadata tied to the repository commit
- signed release artifacts or attestations

Preferred signing mechanism: Sigstore keyless signing with GitHub Actions provenance. If Sigstore is unavailable, the release notes must document the temporary signing mechanism, checksum verification steps, and the reason the preferred path was not used.

## Verification Before Publish

Before publication, run the release verification matrix:

```bash
uv build --sdist --wheel --out-dir dist
aegis certify-release --source-dir . --dist-dir dist/aegis-release-candidate --report-file reports/aegis-release-certification/certification-report.json
python3 -m pytest tests/meta_workflow_guard/test_aegis_release_distribution.py
python3 -m pytest tests/meta_workflow_guard/test_aegis_installer.py::test_release_certification_inspects_artifacts_and_writes_report
AEGIS_RUN_CERTIFICATION_SMOKE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_installer.py::test_release_certification_full_clean_smoke_when_enabled
AEGIS_RUN_WHEEL_SMOKE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_release_distribution.py::test_local_wheel_cli_smoke_when_enabled
AEGIS_RUN_WHEEL_MCP_SMOKE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_release_distribution.py::test_local_wheel_mcp_stdio_smoke_when_enabled
AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py::test_local_wheel_mcp_real_target_project_smoke_when_enabled
aegis status --target-dir /path/to/test-project
```

The release owner must preserve build, test, checksum, and signing evidence with the release notes.

TestPyPI and PyPI publication are blocked until the local artifact MCP target smoke passes and its evidence shows a fresh project can install, kickoff, log S:W:H:E evidence, verify, and close out without a source checkout dependency.

## Consumption Policy

Automation must pin the package version once public releases exist:

```bash
uvx --from aegis-foundation==0.1.0 aegis inspect --target-dir .
uvx --from aegis-foundation==0.1.0 aegis status --target-dir .
uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
```

Floating installs are acceptable only for local exploration:

```bash
uvx --from aegis-foundation aegis inspect --target-dir .
```

## MCP Release Policy

Packaged MCP startup must report `asset_origin=package` unless the user explicitly supplies `--source-root` or `AEGIS_SOURCE_ROOT`.

Hosted MCP service deployment is supported as a release pattern only after the service documents:

- transport
- authentication
- version pinning
- artifact provenance
- upgrade and rollback procedure
- verification evidence

Task 113 does not publish a hosted MCP service.

## Release Notes

Each release note must include:

- package version
- source commit
- supported Python versions
- install snippets
- upgrade path
- rollback path
- signing/provenance verification
- known policy-only limitations
- schema and manifest compatibility notes
