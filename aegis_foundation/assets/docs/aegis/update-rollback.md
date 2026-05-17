# Aegis Update And Rollback Guide

This guide defines the safe operational flow for updating Aegis in an installed target project.

## Update Flow

1. Pin the package version you intend to test.

```bash
uvx --from aegis-foundation==0.1.0 aegis status --target-dir .
```

2. If `aegis status` reports `migration_required=false`, no package migration is required. Run verification after local environment or hook changes.

```bash
uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
```

3. If `aegis status` reports `migration_required=true`, inspect the target and generate a reviewed plan before applying anything.

```bash
uvx --from aegis-foundation==0.1.0 aegis inspect --target-dir .
uvx --from aegis-foundation==0.1.0 aegis plan-install --target-dir . --primary-agent claude --agent claude
```

4. Review `.aegis/reports/install-plan.json`. Do not apply the plan if it contains unsafe overwrite or manual-review operations.

5. Apply only after review:

```bash
uvx --from aegis-foundation==0.1.0 aegis install --target-dir . --primary-agent claude --agent claude --apply
```

6. Verify immediately:

```bash
uvx --from aegis-foundation==0.1.0 aegis verify --target-dir .
```

7. Preserve `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, and `.aegis/reports/verification-report.json` as evidence.

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

- `aegis install --apply` after plan review
- `aegis verify` after acknowledging report writes
- project-owner Git rollback or backup restoration

Read-only surfaces:

- `aegis inspect`
- `aegis status`
- `aegis plan-install`
- MCP `aegis.inspect`
- MCP `aegis.status`
- MCP `aegis.plan_install`

## Deferred Commands

Task 113 keeps mutating update and rollback automation deferred:

- `aegis.plan_update`
- `aegis.update`
- `aegis.rollback`

These commands must not be documented as available until they reuse the installer safety model, require explicit apply confirmation for mutations, and produce evidence reports.
