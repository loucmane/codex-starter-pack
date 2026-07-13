# Decisions

- 2026-07-13 — Task 239 is diagnostic-only. Use disposable `/tmp` worktrees, normalize
  checked-in evidence, and leave recorder/ledger/witness behavior unchanged until Task
  240 selects a correction from measured causes.
- 2026-07-13 — Retain the existing Git-common-dir store primitive for Task 240 unless
  later evidence contradicts the live and concurrent teardown tests. Task 240 should
  target capture transport, event typing, and hierarchical attribution rather than
  duplicating mutable state into each worktree.
- 2026-07-13 — Classify writable-state Claude as degraded (`attribution_missing`),
  inherited read-only-state Claude as failed (`parent_only_traffic`), and Codex as
  unsupported (`unsupported_surface`). Do not relabel parent gate decisions as child
  implementation evidence.
- 2026-07-13 — Check in only normalized coverage and hashes. Raw client output,
  transcripts, prompts, absolute paths, and temporary credential/config state remain
  outside the repository.
