# Task 144 Scope Note

Task 144 is not adding a wizard or a mutating reconcile mode. The kickoff template names
this artifact `wizard-flow.md`; for this task it records the scoped contract boundary.

## Scope

- Add a durable Aegis contract document for reconcile promotion criteria.
- Add focused regression tests around the CLI and MCP reconcile surfaces.
- Preserve `aegis reconcile` as report-only and read-only.
- Prove the command does not mutate the working tree during a smoke run.

## Non-Scope

- No Taskmaster status mutation from reconcile.
- No Aegis closeout automation from reconcile.
- No git writes, branch deletion, PR writes, or generated-task refreshes from reconcile.
- No `--apply`, `--auto`, `--fix`, `--set-status`, `--closeout`, `--mutate`, or similar
  mutation flags on reconcile.

## Design Boundary

Future reconcile mutation work must be a separate task with operator confirmation, audit
breadcrumbs, rollback evidence, and high-confidence proof requirements. Ambiguous findings
remain manual-only until a later task proves a narrower safe rule.
