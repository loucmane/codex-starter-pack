# Handoff - Task 180

## Current State

Task 180 is active on `feat/task-180-observation-artifact-collection`.

## Goal

Add a safe `aegis observe stop --collect-artifacts` path that collects only known observation byproducts and leaves observation mode fail-closed for all unsafe or unknown deltas.

## Implemented

- `--collect-artifacts` added to CLI, Codex helper proxy, and MCP observe stop.
- Known artifacts move under `.aegis/reports/observations/<observation-id>/artifacts/`.
- Raw cleanup remains blocked during observation.
- Unsafe dirty state still blocks even when collection is requested.

## Validation Target

- Focused observation stop tests passed.
- Installer and MCP suites passed.
- Remaining: final Taskmaster dependency validation, work-tracking audit, commit guard, and commit.
