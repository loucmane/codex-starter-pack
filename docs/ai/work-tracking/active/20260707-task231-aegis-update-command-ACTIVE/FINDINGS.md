# Findings

- 2026-07-07 — HP-Fetcher update failure mode is not a missing primitive; it is a
  missing composition. Operators had to manually chain `runtime update`, `plan-install`,
  `install --apply`, `verify`, `brief --check`, and `brief`, then decide which strict
  workflow failures were stale evidence versus update blockers.
- 2026-07-07 — Update success must be scoped to the managed refresh. Old strict
  workflow-state failures, such as HP-Fetcher Task 80 residue, belong in the update
  report but must not prevent refreshing stale managed assets and the computed capsule.
