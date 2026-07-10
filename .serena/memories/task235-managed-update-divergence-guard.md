# Task 235 Managed Update Divergence Guard

## Context

HP-Blog Task 56 proved that path-based manifest ownership was insufficient: a safe-looking
managed update replaced a committed, locally hardened `scripts/codex-guard` and removed its
completed-archive tracker fallback.

## Implemented Contract

- Canonical and packaged `codex-guard` now prefer one ACTIVE tracker and otherwise resolve only
  a completed current-work path under the archive root ending in `-COMPLETED`.
- New foundation manifests record `sha256:` checksums for materialized managed assets.
- Managed updates compare installed bytes to that baseline before overwriting.
- Legacy source-backed assets recover prior expected bytes from
  `runtime.source_root`/`runtime.source_commit` with `git show`.
- Local divergence becomes a managed `manual-review`; pristine stale assets remain upgradeable.
- `project_update --apply` retains the original manifest baseline after advancing runtime state.

## Evidence

- Guard tests: 83 passed.
- Installer/schema/asset parity tests: 138 passed, one opt-in certification smoke skipped.
- Live HP-Blog Task 56 dry-run: zero conflicts, zero manual reviews, five safe modifications,
  byte-identical guard skip, and no target-tree mutation.
- Authoritative MCP/schema/installer suite: 188 passed, one opt-in smoke skipped.
- Full repository suite: 1,749 passed, four explicit opt-in smokes skipped.

## Continuation Boundary

Task 235 implementation, authoritative integration, full-suite, and repository guard checks are
complete. Deliver it upstream, then retry the blocked HP-Blog Task 56 update only from the stable
merged commit. The downstream retry must pass all completed-state regressions and produce a
second update preview with zero managed changes.
