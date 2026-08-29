# Bead ga-6w1y Repair CI and Aegis delivery contract – Implementation Notes

## Implemented Workstreams

### Reproducible Python CI
- Replaced floating `pip` resolution with `uv sync --locked --all-groups` and frozen,
  no-sync execution.
- Declared supported Python as `>=3.11,<3.15` and test 3.11, 3.12, 3.13, and 3.14.
- Preserved full-suite coverage while removing Taskmaster installation from routine
  matrix jobs.

### Conditional Legacy Compatibility
- Added `scripts/aegis-ci-taskmaster-compatibility` as the single modular producer for
  context, cascade, accumulation, and precision evidence.
- Added a path classifier so pinned Taskmaster 0.43.1/Node 22 is provisioned only for
  compatibility-relevant changes and post-merge runs.
- Kept Taskmaster read-only/compatibility-only; Beads remain lifecycle authority.

### Workflow Integrity and Bounded Execution
- Pinned every external action to an immutable full commit SHA.
- Added explicit least-privilege permissions, job timeouts, stale-PR cancellation, and
  credential-free checkouts.
- Removed duplicate non-main push triggers from guard workflows.

### Delivery and Dependency Security
- Aligned Aegis autonomous delivery with the repository-enabled merge-commit method.
- Added Dependency Review as policy-required evidence and a pinned workflow.
- Added grouped weekly Dependabot updates for GitHub Actions and the `uv` ecosystem.

## Local Verification
- Locked install and lock consistency: PASS.
- Full suite: `2254 passed, 21 skipped`.
- Focused Aegis/package parity: `353 passed, 3 skipped`.
- Pinned Taskmaster compatibility: full-graph health PASS and `116 passed`.
- Workflow YAML parsing, Ruff, `git diff --check`, and modular-helper formatting: PASS.
- Source gates: readiness `READY` (8/8), plan sync PASS, guard PASS, strict drift
  findings `0`, work-tracking audit PASS.
