# Findings

- 2026-07-15 — Task 253 correctly removed the verifier's sole dependency on
  `install-report.json`, but its four safety properties were still synthesized from runtime
  constants rather than persisted as a schema-validated tracked contract.
- 2026-07-15 — The Blog Task 42 reproduction failed exactly one required check under the old
  source: `codex.hook_trust_guidance`; the ignored install report was absent.
- 2026-07-15 — A real clean secondary worktree can pass strict verification and closeout dry-run
  with no generated install report when the tracked contract is valid.
- 2026-07-15 — Whole-file mypy currently reports 266 pre-existing errors across the large installer
  and its mirrored copy; focused tests, Ruff, Black, schema parsing, py_compile, parity, and the full
  repository suite provide the regression signal for this task.
