# Derived Obsidian Vault Dogfood

**Date**: 2026-07-14
**Mode**: read-only source inspection; output only under `/tmp`
**Repositories mutated**: none
**Aegis enforcement changed**: no

## Result

The source repository, Blog, and HP-Fetcher all build deterministic Obsidian-compatible vaults
from their existing task, ledger, capsule, and preserved legacy evidence. A second build over
the same authoritative snapshot is a no-op in all three repositories.

| Fixture | Total ledger rows | High-signal rows | Stable identity edges | Tasks + subtasks | Legacy documents | Human legacy lines | Generated files | First build | Second build |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Aegis source | 15,463 | 204 | 117 | 637 | 2,175 | 72,963 | 3,089 | 0.77 s | current/no-op |
| Blog | 2,506 | 97 | 42 | 39 | 214 | 8,114 | 353 | 0.30 s | current/no-op |
| HP-Fetcher | 45,473 | 1,047 | 1,573 | 367 | 33 | 3,948 | 2,518 | 1.22 s | current/no-op |

The Blog ledger was being written by another active session during diagnosis. The table is the
bounded snapshot used by the successful final build (`source_digest`
`9878880752358944aa31bfca0dd4aec36e2472a3ecc71d1e8bfc6ac8728ab3b7`), not a claim that its
append-only row count will remain fixed.

## Output Locations

- Source: `/tmp/aegis-task243-vault-dogfood`
- Blog: `/tmp/blog-aegis-vault-task243`
- HP-Fetcher: `/tmp/hpfetcher-aegis-vault-task243`

These disposable outputs are intentionally outside every repository and are not delivery
artifacts.

## Source Evidence

- Ledger classes: 13,493 gate decisions, 1,766 mutations, 85 delivery, 41 scope, 9 session
  starts, 7 task-truth, 42 tool failures, and 20 verification events.
- High-signal projection: 204 rows; low-level gate/mutation rows remain in the ledger.
- Legacy corpus: 2,175 documents, 72,963 human-authored nonblank lines, 10,085 headings, 4,125
  checkboxes, 8,281 S:W:H:E entries, and only 7 generated blocks.
- First provisional build failed closed at the 2,000-document ceiling. The measured corpus
  justified raising that explicit ceiling to 5,000; no ownership, byte, or atomicity guard was
  relaxed.
- Final source digest: `029e33bdc0e552413ecf9fe32cc14c862bf80e64fbd851d54471f2bb0a2d3d7f`.

## Blog Evidence

- Snapshot ledger classes: 1,233 gate decisions, 1,176 mutations, 17 delivery, 7 operator
  authority, 26 scope, 16 session starts, 10 task-truth, and 21 witness events.
- Capsule orientation: Task 41, status `done`, branch-derived next action
  `review_task_41_done`.
- Legacy corpus: 214 documents, 8,114 human-authored nonblank lines, 1,269 headings, 638
  checkboxes, 1,173 S:W:H:E entries, and 97 generated blocks.
- The 8,114 human lines prove that passive evidence and generated projections do not replace
  the repository's planning, rationale, and handoff record.
- Final snapshot digest: `9878880752358944aa31bfca0dd4aec36e2472a3ecc71d1e8bfc6ac8728ab3b7`.

## HP-Fetcher Evidence

- Ledger classes: 22,922 gate decisions, 21,504 mutations, 68 delivery, 395 scope, 49 session
  starts, 2 task-truth, 470 tool failures, and 63 verification events.
- Capsule orientation still identifies superseded Task 80 as `done` through `current-work`,
  preserving the known stale-pointer fixture rather than repairing or hiding it.
- Legacy corpus: 33 documents, 3,948 human-authored nonblank lines, 225 headings, 114
  checkboxes, 956 S:W:H:E entries, and no generated projection blocks.
- The deduplicated topology contains 1,573 identity edges. This is tractable as a graph while
  projecting 45,473 individual event rows would not be.
- Final snapshot digest: `199a6a0af3d571304fe1883727ead07416d15b5b2161f17dec9ed57c16e75662`.

## Defect Found And Corrected

Sandboxed read-only SQLite opening could access the database file but not create the WAL shared
memory sidecar. The existing reader built its select list while the column probe was empty and
only then reopened immutably, yielding real row counts with every field projected as `NULL`.

The corrected reader reopens immutably and resolves columns before query construction. Live and
packaged `ledger_lib.py` remain byte-identical, and the regression proves a witness row retains
its event ID, type, and outcome after the simulated failed WAL metadata probe.

## Coexistence Conclusion

The vault adds useful graph navigation and bounded cross-surface relationships, but the corpus
quantifies why it must complement rather than replace S:W:H:E:

- the ledger owns observed facts;
- the capsule owns computed orientation;
- the witness owns deterministic delivery proof;
- legacy files retain tens of thousands of lines of human rationale and task narrative;
- the vault links and inventories those sources without becoming authority.

No broad demotion or retirement is supported by this dogfood alone.
