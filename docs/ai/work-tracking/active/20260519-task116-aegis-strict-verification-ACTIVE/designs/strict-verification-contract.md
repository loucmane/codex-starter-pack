# Task 116 Strict Verification Contract

## Purpose

Task 116 turns the Task 115 installed-project workflow into a release gate. The deliverable is not another smoke test. It is a strict, machine-readable verification and certification layer that can fail an Aegis release candidate before it reaches GitHub artifacts or PyPI.

## Runtime Contract

`aegis verify --strict` must run from the shared Aegis core and be exposed through the package CLI, the repo wrapper, and MCP when practical. Every surface delegates to the same verifier.

Strict verification must pass in target projects that do not contain Taskmaster or Serena. Those integrations are optional unless the Aegis current-work payload explicitly marks them required.

Required strict check groups:

- `manifest.*`: manifest presence, schema validity, version alignment, managed file paths, and file-vs-directory correctness.
- `runtime.*`: required Aegis files, executable scripts, project-local `.aegis/bin/aegis`, and no source-root dependency for installed targets.
- `workflow.*`: session, plan, tracker, findings, decisions, implementation, changelog, handoff, reports, and packaged workflow template completeness.
- `claude.*`: Claude hook wiring for PreToolUse, PostToolUse, and Stop when Claude support is installed.
- `mutation.*`: pending tracking, `aegis log` surface updates, mismatched pending evidence refusal, and read-only `/dev/null` redirects not creating pending tracking.
- `protection.*`: protected-path refusal for direct file writes and Bash redirections.
- `integrations.*`: Taskmaster and Serena detected/absent/required state reported without becoming a hard dependency by default.

Strict verification writes `.aegis/reports/verification-report.json` with `mode: "strict"`, a top-level status, a summary, categorized check records, and actionable failed check IDs.

## Release Certification Contract

Certification is the release-candidate gate that proves artifacts, not the source checkout, work.

Required certification stages:

- Build wheel and sdist from the current checkout.
- Compute SHA-256 checksums for every artifact.
- Capture provenance: git commit, dirty-worktree status, package version, Python version, build command, artifact sizes, and timestamps.
- Inspect wheel/sdist contents for Aegis assets, entry points, schemas, workflow templates, and runtime scripts.
- Install from the built artifact into clean temporary target projects without `AEGIS_SOURCE_ROOT`.
- Run installed CLI smoke: `aegis --version`, inspect, plan-install, install, status, `verify --strict`, kickoff, readiness, mutation tracking/logging, and protected-path refusal.
- Run MCP smoke where practical: list tools/resources/prompts, inspect, and strict verify.
- Emit `reports/aegis-release-certification/certification-report.json` with schema version, status, artifacts, checksums, provenance, target smokes, MCP smoke, strict verification report paths, failures, and publishing handoff.

## Implementation Boundaries

- Reuse `scripts/_aegis_installer.py` as the shared core.
- Thread core behavior through `aegis_foundation/cli.py`, `scripts/codex-task`, and `aegis_mcp/server.py`.
- Keep shell orchestration thin; reusable logic belongs in Python functions/modules.
- Keep full certification matrix scalable. The PR CI path can run focused non-env-gated coverage while heavier matrices stay workflow-dispatch or env-gated.

## Acceptance

- `aegis verify --strict` passes for healthy installed targets and fails with specific check IDs for missing hooks, missing workflow templates, broken local shim, broken mutation tracking, missing workflow surfaces, protected-path bypasses, and explicitly required missing integrations.
- Release certification builds artifacts, validates checksums/provenance, installs from artifacts into clean targets, runs strict verification and runtime smokes, and writes a deterministic JSON report.
- CI runs enough strict verification and certification coverage that regressions cannot silently pass.
- Documentation states that GitHub release artifacts with checksums/provenance/certification report come before any PyPI publication task.
