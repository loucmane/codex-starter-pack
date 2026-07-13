# Findings

- 2026-07-13 — Managed-update behavior was cohesive enough to extract without moving installer orchestration, mutable target state, or report I/O. A callback-based stdlib core keeps source and package execution on one implementation.
- 2026-07-13 — Existing tests monkeypatch the installer's private `_legacy_managed_checksum`; bypassing that seam caused a focused regression even though default behavior matched. Thin installer resolvers preserve compatibility without duplicating the algorithm.
- 2026-07-13 — Fixed operation digests catch classification drift that byte-only asset tests miss. The three consumer fixtures exercise fresh install, known-prior upgrade, project-authored entrypoints, and custom Codex hooks.
- 2026-07-13 — The live Blog and HP-Fetcher previews contain more operations than the synthetic goldens because their installed runtimes are older, but both classify every operation as safe and report zero conflict/manual-review paths. They were not mutated.
- 2026-07-13 — The full-suite reconcile failure is environmental: a test expects the governed repository to be outside the system temp directory, while this isolated worktree is under `/tmp`. Task 242 and untouched Task 240 both return `candidate_already_done` instead of the earlier `target_not_isolated_temp` refusal.
- 2026-07-13 — The opt-in real-target wheel MCP harness attempts kickoff immediately after installation without acknowledging the required client-reload marker. It fails identically before this extraction; basic wheel CLI and MCP stdio validation pass.
- 2026-07-13 — Hosted CI from a normal checkout is the correct proof for the unchanged temp-location assertion. Changing the safety test or reload contract in this refactor would hide unrelated behavior and broaden scope.
