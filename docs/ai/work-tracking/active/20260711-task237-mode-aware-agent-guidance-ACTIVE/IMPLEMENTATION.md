# Task 237 Make Managed Agent Guidance Truthful And Mode-Aware – Implementation Notes

## Completed Workstreams

- Added one shared mode-aware managed-entrypoint renderer with a 25-nonblank-line contract.
- Routed Claude, Codex, and Agents renderers through the shared contract.
- Made existing Codex entrypoint merging unconditional so repeat updates preserve project bytes.
- Added explicit markers for fresh Claude and Agents entrypoints.
- Added checksum-backed migration for exact manifest-owned markerless Claude runtimes while
  preserving modified markerless files conservatively.
- Updated the upstream `CODEX.md` managed block and synchronized the packaged installer mirror.
- Added fresh install, stale-block update, repeat-install idempotence, project-byte preservation,
  markerless migration, negative advisory-ceremony, strict-reference, and source/package parity
  coverage.
- Updated the target E2E contract so strict workflow details are asserted in
  `.aegis/contract.md`, not the compact entrypoint.
- Ran live Blog preview plus isolated advisory apply/idempotence dogfood.

## Behavior Boundary

No hook, gate, readiness, enforcement, ledger, witness, capsule, closeout, or Taskmaster runtime
behavior changed. Task 237 changes rendered instructions and safe installer ownership handling
only.
