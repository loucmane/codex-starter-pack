# Task 255 Host-Scoped Codex Remote Control Trust Management – Implementation Notes

## Implemented Workstreams

- `aegis_foundation/codex_remote_trust.py` — host state, validation, projection, locking, transactions, and diagnostics.
- `aegis_foundation/cli.py` — nested `aegis codex bridge` and `aegis codex trust` commands.
- `docs/aegis/codex-remote-control-trust.md` and packaged mirror — operator contract and rollout.
- `tests/meta_workflow_guard/test_codex_remote_trust.py` — unit, security, concurrency, rollback, and CLI integration coverage.

No Blog paths or host configuration files are implementation targets for this upstream phase.

## Runtime Contract

- Durable authorization lives in `trusted-projects.toml` under the effective Remote Control `CODEX_HOME`; adding and removing authority is preview-only without `--apply`.
- Aegis composes only its delimited `[projects]` projection and preserves every byte outside that block. Exact unmanaged trusted entries remain externally owned; conflicting or aliased unmanaged entries fail closed.
- Project paths are absolute, canonical directory identities. The allowlist is strict TOML schema version 1, requires complete authority metadata and UTC timestamps, and uses mode `0600`.
- Mutations re-read state under an OS-backed lock, atomically replace files, fsync, validate durable state, preserve existing config mode, and maintain an exact last-known-good config. Rollback verifies restored bytes and raises a terminal error if incomplete.
- `aegis codex bridge status|plan|apply` and `aegis codex trust status|add|remove` expose the lifecycle. Status distinguishes normal project trust, Remote authorization, effective Remote trust, tracked hook-review guidance, hook-definition digest, and unknowable client-local trust.
- Aegis never imports normal-home trust or hooks, never copies connector/session/auth state, never symlinks homes/configs, and always leaves exact hook approval to `/hooks`.

## Verification So Far

- 42 Task 255 tests passed, including malformed TOML, marker corruption, duplicates, canonical aliases, symlink refusal, restrictive modes, concurrency, lock timeout, transaction rollback, terminal rollback failure, idempotence, config-byte preservation, CLI lifecycle, and changed hook hashes.
- 37 adjacent Codex adapter/bootstrap/schema tests passed.
- 14 release-distribution tests passed; the two documented opt-in wheel/MCP smokes were skipped.
- 153 installer tests passed; the documented opt-in release-certification smoke was skipped.
- Ruff and mypy passed for the new module/test surface; Black is clean for new files; `git diff --check` passed.
- A live read-only status against the real normal and Remote Control homes explained Blog's warning without writing either home or the Blog checkout.
- The explicit installed-wheel CLI smoke passed, proving the new top-level CLI import, packaged module, and console entrypoint work from the built distribution.
- The full repository run passed 2,100 tests with four documented opt-in smokes skipped. Its only default-run failure was a pre-existing test whose isolated-temp predicate treats the source worktree as temporary when the complete worktree is under `/tmp`; the exact test passed with a non-overlapping `TMPDIR`. Full details are in `reports/codex-remote-trust-bridge/task-verification.md`.
