# Decisions

- 2026-07-14 — Preserve passive evidence and legacy S:W:H:E as complementary systems; defer
  Task 210 and stop before any Taskmaster-to-Gas-Town migration.

## 2026-07-14 — Derived vault is a view, never authority

- The vault may read ledger, capsule, task, Git, and legacy evidence, but it may not write back.
- Output must remain outside the source repository and must be safely disposable.
- Unknown, manually modified, symlinked, stale-inventory, or in-repository destinations fail
  closed rather than being adopted or overwritten.

## 2026-07-14 — Passive and legacy systems coexist

- The ledger owns observed facts, the capsule owns computed orientation, and the witness owns
  deterministic delivery proof.
- Plans, sessions, trackers, handoffs, decisions, findings, and implementation notes retain
  declared intent and human narrative that cannot be inferred from tool events.
- Generated sections may reduce duplicate ceremony, but no Task 243 evidence authorizes broad
  demotion, deletion, or cessation of generation.

## 2026-07-14 — Task 210 is no-go and should remain deferred

- Every parity row remains `keep` or `shadow`.
- The owner explicitly chose complementarity rather than retirement.
- A later change requires a separate per-surface owner decision and new evidence; Task 243 does
  not begin that work.

## 2026-07-14 — Stop before Taskmaster-to-Gas-Town migration

- Task 243 records a reviewed stopping checkpoint after source delivery.
- No Gas Town architecture, task mutation, scaffold, or migration action is implied by this
  audit. Work begins only after explicit owner instruction at the checkpoint.
