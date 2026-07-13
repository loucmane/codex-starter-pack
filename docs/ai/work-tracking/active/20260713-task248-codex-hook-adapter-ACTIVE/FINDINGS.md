# Findings

- 2026-07-13 — Codex matcher aliases such as Edit/Write decide whether a hook fires, but
  hook stdin remains canonical `tool_name: "apply_patch"` with the entire patch in
  `tool_input.command`. Aegis therefore needs a first-class canonical handler; alias-only
  registration is insufficient.
- 2026-07-13 — Real Codex 0.144.3 emitted one file-change tool item for a two-file patch.
  Aegis recorded one pending event containing both paths and one matching ledger mutation,
  validating atomic patch semantics rather than per-file reconstruction.
- 2026-07-13 — Codex hook trust is definition-hash scoped. Installing a syntactically valid
  hook file does not activate it; `/hooks` review is a required client-owned boundary and
  must remain visible in install/update guidance.
- 2026-07-13 — A workspace-write Codex session needs a writable XDG state root for the
  out-of-worktree SQLite ledger. The live smoke used an isolated writable
  `XDG_STATE_HOME`; in-worktree pending evidence remained independently available. This is
  a deployment precondition to surface during target rollout, not a reason to move the
  authoritative ledger into the worktree.
- 2026-07-13 — The full suite contains one safety test whose premise is that the governed
  repository is outside `/tmp`. A Task 248 worktree rooted under `/tmp` intentionally
  violates that premise; the remaining 1,953 tests pass locally and the exact assertion
  must be exercised in hosted CI or a detached non-`/tmp` checkout.
- 2026-07-13 — Taskmaster 0.43.1 AI-backed add/update operations can temporarily normalize
  the full source serialization. The repository's guided kickoff then performs a supported
  `set-status` transition that restores the established string-ID form; the final Task 248
  source diff is semantic and task-scoped. No manual `tasks.json` edit was used.
