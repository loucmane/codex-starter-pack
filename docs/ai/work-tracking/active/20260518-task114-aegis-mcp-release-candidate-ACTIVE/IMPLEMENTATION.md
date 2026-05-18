# Task 114 Aegis MCP Release Candidate Validation – Implementation Notes

## Planned Workstreams
- `114.1` Scope and matrix: define the release-candidate boundary, install target matrix, release-channel options, and go/no-go criteria before implementation.
- `114.2` Artifact baseline: build wheel/sdist, inspect metadata, entry points, and package data.
- `114.3` Clean CLI smoke: install from artifacts into clean target projects and exercise `inspect`, `plan-install`, `install`, `status`, and `verify`.
- `114.4` Clean MCP smoke: start installed `aegis-mcp-server` over stdio outside the repository and verify discovery plus selected calls.
- `114.5` Cross-agent docs: document Codex, Claude, and generic MCP client setup with the chosen first release channel.
- `114.6` Final evidence: run regression and workflow gates, then record a concrete go/no-go for public MCP release readiness.

## Completion Notes
- Built local wheel/sdist release-candidate artifacts into `/tmp/aegis-task114-rc-20260518`.
- Confirmed wheel and sdist include Aegis assets, `aegis` and `aegis-mcp-server` entry points, package metadata, schemas, scripts, docs, and MCP server code.
- Ran the clean installed-artifact CLI smoke from an external target; result: `1 passed`.
- Ran the clean installed-artifact MCP stdio smoke from an external target; result: `1 passed`.
- Added `docs/aegis/mcp-client-setup.md` and the packaged asset copy for Codex, Claude, and generic MCP client setup.
- Final Aegis-focused regression passed with `50 passed, 2 skipped`; the skipped tests are the opt-in wheel smokes captured separately.

## Release Readiness Recommendation
Go for preparing a GitHub release-candidate artifact flow. Do not publish to PyPI yet; PyPI should be a separate release task after GitHub artifact checksums/provenance and clean downstream install evidence are finalized.
