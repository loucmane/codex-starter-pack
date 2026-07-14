# Task 243 — PR-4 Parity And Derived Obsidian Vault

- Built a deterministic, bounded, read-only Obsidian-compatible projection from the Aegis
  ledger, capsule, task truth, Git identity, and structural legacy inventory.
- The vault is disposable and non-authoritative: output stays outside the repository, has an
  exact ownership/hash manifest, publishes atomically, and never writes back.
- Source, Blog, and HP-Fetcher dogfood passed. Their measured legacy corpora retain 72,963,
  8,114, and 3,948 human-authored nonblank lines after generated marker blocks are excluded.
- The reviewed architecture is coexistence: ledger for observed facts, capsule for orientation,
  witness for delivery proof, and S:W:H:E files for declared intent and human narrative.
- All 20 PR-4 rows remain `keep` or `shadow`; Task 210 is deferred and no-go.
- The primary local capsule is stale at Task 252 and should be recomputed through the supported
  workflow after Task 243 merges. Do not overwrite the owner's unrelated local drift.
- Taskmaster-to-Gas-Town migration was not started and requires explicit owner authorization at
  the post-Task-243 stopping checkpoint.
