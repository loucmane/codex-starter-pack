# Aegis MCP Release Candidate Contract

## Purpose

Task 114 answers one question: can Aegis be treated as a release-candidate MCP installer from outside this repository?

The answer must be evidence-backed. Internal package tests are not enough. The release candidate must be built as artifacts, installed into clean external targets, started as an MCP server outside the source checkout, and used to inspect, plan, install, status-check, and verify Aegis.

## Release Candidate Boundary

In scope:
- Build wheel and sdist from the Task 114 branch.
- Inspect package metadata, console scripts, bundled assets, and artifact contents.
- Install the built artifact into clean temporary projects.
- Run `aegis` CLI commands from outside the source repository.
- Run `aegis-mcp-server` from outside the source repository.
- Verify MCP tools, resources, and prompts are discoverable over stdio.
- Call installed MCP/CLI surfaces against clean target repositories.
- Document setup for Codex, Claude, and generic MCP clients.
- Produce a go/no-go recommendation for public MCP release readiness.

Out of scope:
- Publishing to PyPI as part of this task.
- Changing the Aegis package name unless a concrete blocker is found.
- Adding hosted MCP service infrastructure.
- Replacing local checkout and editable package workflows validated by Tasks 112 and 113.

## Release Channel Options

| Option | What It Proves | Pros | Risks |
| --- | --- | --- | --- |
| Local wheel/sdist artifact | Artifact correctness independent of source checkout | Fast, deterministic, no external registry dependency | Not a public install path by itself |
| GitHub release artifact | Downloadable release candidate from GitHub | Good first public-ish channel, supports checksums/provenance | Needs release automation and artifact retention policy |
| `uvx --from git+https://...` | Install from repository URL | Simple for early adopters | Couples installs to repo state and may hide packaging issues |
| TestPyPI | Registry install path without production PyPI | Strong registry rehearsal | Extra credentials/release workflow overhead |
| PyPI | Public install path | Best user experience | Should wait until RC evidence is green |

## Provisional Decision

Task 114 uses local wheel/sdist artifacts as the release-candidate baseline and documents GitHub release artifacts as the likely first public distribution channel if the RC passes.

PyPI publication remains a later task until the local artifact and clean-project MCP smoke tests pass without source-checkout assumptions.

## Clean-Project Matrix

Required evidence:
- CLI installed from wheel runs from a directory outside the source checkout.
- CLI can `inspect`, `plan-install`, `install`, `status`, and `verify` against a clean target.
- MCP server installed from wheel starts from a directory outside the source checkout.
- MCP stdio discovery lists expected tools, resources, and prompts.
- MCP calls exercise at least inspect, plan/status, and one read-only diagnostic path.

Preferred evidence:
- `uvx --from <wheel>` style invocation for version/status.
- `pipx run --spec <wheel>` style invocation for version/status.
- A documented generic MCP client config snippet using the installed `aegis-mcp-server`.

## Go/No-Go Criteria

Go for public release preparation if:
- Built artifacts include required Aegis assets and entry points.
- Clean-project CLI smoke passes from installed artifacts.
- Clean-project MCP stdio smoke passes from installed artifacts.
- Cross-agent setup docs are explicit enough for Codex, Claude, and generic MCP clients.
- Guard, Taskmaster health, plan sync, work-tracking audit, and diff-check pass.

No-go if:
- The installed CLI or MCP server requires repository-local paths.
- Packaged assets differ from source assets in a way that changes install behavior.
- MCP startup works only from editable installs.
- Any setup path requires undocumented manual copying.
- Release-channel docs cannot describe a reproducible install path.

## Evidence Targets

Store Task 114 evidence under:

`docs/ai/work-tracking/active/20260518-task114-aegis-mcp-release-candidate-ACTIVE/reports/aegis-mcp-release-candidate/`

Expected evidence files:
- `build-2026-05-18-rc.txt`
- `artifacts-2026-05-18-rc.txt`
- `tests-2026-05-18-clean-cli.txt`
- `tests-2026-05-18-clean-mcp.txt`
- `docs-2026-05-18-cross-agent.txt`
- `plan-sync-2026-05-18-final.txt`
- `taskmaster-health-2026-05-18-final.txt`
- `work-tracking-audit-2026-05-18-final.txt`
- `guard-2026-05-18-final.txt`
- `diff-check-2026-05-18-final.txt`
