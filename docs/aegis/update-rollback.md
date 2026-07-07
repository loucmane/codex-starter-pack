# Aegis Update And Rollback Guide

This guide defines the safe operational flow for updating Aegis in an installed target project.

## Update Flow

For a normal installed project, use the composed update command first. It wraps the
runtime pointer refresh, managed asset plan/apply, verification reporting, and capsule
compile in one safety-checked flow.

```bash
uvx --from aegis-foundation==0.1.0 aegis update --target-dir .
uvx --from aegis-foundation==0.1.0 aegis update --target-dir . --apply
```

The dry-run form writes no target files. The apply form refuses unsafe overwrites and
manual-review install operations, writes `.aegis/reports/update-report.json`, preserves
the target's current enforcement mode, and reports verification failures without hiding
them. Verification failures caused by old workflow state are evidence to review; they do
not make a successful managed-asset refresh look like a failed update. The update report
also exposes those stale-state findings under `workflow_state_evidence` so operators can
distinguish update failures from inherited residue such as stale current-work folders,
branch/task mismatch, missing workflow report directories, or pending-tracking queues.

Use the lower-level flow when you need to inspect each step manually.

1. Pin the package version you intend to test.

```bash
uvx --from aegis-foundation==0.1.0 aegis status --target-dir .
uvx --from aegis-foundation==0.1.0 aegis doctor --target-dir .
```

2. Inspect the target and generate a reviewed plan before applying anything.

```bash
uvx --from aegis-foundation==0.1.0 aegis inspect --target-dir .
uvx --from aegis-foundation==0.1.0 aegis plan-install --target-dir . --primary-agent claude --agent claude
```

3. Review `.aegis/reports/install-plan.json`. Do not apply the plan if it contains unsafe overwrite or manual-review operations.

4. Apply only after review:

```bash
uvx --from aegis-foundation==0.1.0 aegis install --target-dir . --primary-agent claude --agent claude --apply
```

5. Verify immediately:

```bash
uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
```

6. Refresh the computed capsule when the target installs capsule assets:

```bash
uvx --from aegis-foundation==0.1.0 aegis brief --target-dir . --reason manual >/dev/null
uvx --from aegis-foundation==0.1.0 aegis brief --target-dir . --check
```

7. Preserve `.aegis/reports/update-report.json`, `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, and `.aegis/reports/verification-report.json` as evidence.

## Rollback Flow

Rollback is intentionally Git-first in this release. Aegis does not mutate target files during `aegis status` and does not implement a mutating `aegis rollback` command in Task 113.

Use one of these rollback sources:

- Git branch, commit, or tag from before the Aegis update
- recorded backup created by the project owner before `aegis install --apply`
- reviewed copy of the previous managed files from the release evidence packet

After rollback:

```bash
uvx --from aegis-foundation==0.1.0 aegis status --target-dir .
uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
```

If verification fails, keep the failed verification report and fix the target through a reviewed plan. Do not edit `.aegis/` directly.
Use `aegis doctor` before any manual rollback repair to classify whether the target has safe mechanical drift or requires human review.

## Downgrade Flow

Downgrades are treated as migrations to an older package. They require the same status, inspect, plan-install, apply, and verify sequence as upgrades.

```bash
uvx --from aegis-foundation==0.1.0 aegis status --target-dir .
uvx --from aegis-foundation==0.1.0 aegis plan-install --target-dir . --primary-agent claude --agent claude
uvx --from aegis-foundation==0.1.0 aegis install --target-dir . --primary-agent claude --agent claude --apply
uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
```

Do not downgrade across a schema version boundary unless the release notes explicitly say the older package can read the newer manifest schema.

## Direct Write Policy

Do not write `.aegis/` directly. Direct writes bypass the installer safety model and invalidate release evidence.

Allowed mutation surfaces:

- `aegis update --apply` after dry-run review
- `aegis install --apply` after plan review
- `aegis verify` after acknowledging report writes
- project-owner Git rollback or backup restoration

Read-only surfaces:

- `aegis inspect`
- `aegis status`
- `aegis doctor`
- `aegis update` without `--apply`
- `aegis repair` without `--apply`
- `aegis plan-install`
- MCP `aegis.inspect`
- MCP `aegis.status`
- MCP `aegis.doctor`
- MCP `aegis.repair` with `apply=false`
- MCP `aegis.plan_install`

## Deferred Commands

Single-repo `aegis update` is available. The broader fleet and rollback automation remain deferred:

- `aegis.plan_update`
- `aegis.fleet_update`
- `aegis.rollback`

These commands must not be documented as available until they reuse the installer safety model, require explicit apply confirmation for mutations, and produce evidence reports.
