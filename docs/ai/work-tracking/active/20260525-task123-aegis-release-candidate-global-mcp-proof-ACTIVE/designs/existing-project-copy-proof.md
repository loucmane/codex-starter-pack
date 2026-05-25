# Task 123 Existing-Project Copy Proof

## Objective

Prove Aegis can be installed and used from outside this repository against a copied existing project, not only against synthetic fresh fixtures.

## Primary Acceptance Path

1. Build a local release-candidate artifact from this repository.
2. Use that artifact from a non-repo working directory.
3. Register/start Aegis MCP through the intended global/native command path.
4. Install Aegis into a copied existing project through MCP.
5. Run a realistic Claude workflow in the copy:
   - Aegis MCP handles control-plane operations.
   - Native tools perform source edits and project verification.
   - Installed hooks enforce readiness and pending S:W:H:E tracking.
6. Close out through Aegis:
   - `aegis.verify` strict passes.
   - `aegis.closeout_ready` is proven read-only.
   - `aegis.closeout` passes.
   - Changed source evidence appears in session, plan, tracker, implementation log, changelog, and handoff.

## Existing Project Handling

The original project must not be mutated. The live target must be a copy under `/tmp`, for example:

```bash
/tmp/aegis-task123-existing-project-copy
```

The copy baseline must record:

- original source path
- copied target path
- whether the project already had `.aegis`, `.claude`, `.mcp.json`, `.taskmaster`, `.serena`, `sessions`, `plans`, or `docs/ai/work-tracking`
- initial `git status --short --branch` in the copy
- initial file inventory summary

## Control-Plane vs Implementation Split

Aegis MCP is used for:

- inspect/status/next
- plan_install/install
- kickoff
- log
- verify
- closeout_ready
- closeout

Native agent tools are used for:

- reading source files
- editing source files
- running project tests/smoke commands
- inspecting git status/diff

This preserves the model validated in Tasks 121 and 122. MCP installs and governs the workflow; it does not become a general-purpose source-editing interface.

## Release Boundary

Task 123 does not publish to TestPyPI or PyPI unless a separate explicit decision is recorded. Publication remains blocked until the local artifact/global MCP path and copied existing-project live proof both pass.

The expected final recommendation is one of:

- `publish-ready`
- `publish-deferred`
- `publish-blocked`

with concrete evidence and risks.

## Evidence To Capture

- build command and artifact paths
- artifact checksums
- package version and Python/uv versions
- MCP registration payload and rendered command
- `aegis-mcp-server --describe-config` from the copied project
- MCP tool/resource/prompt discovery
- install/kickoff/log/verify/closeout outputs
- `closeout_ready` read-only snapshot evidence
- project source diff
- project verification output
- no source-checkout leakage scan
- uninstall/rollback notes

