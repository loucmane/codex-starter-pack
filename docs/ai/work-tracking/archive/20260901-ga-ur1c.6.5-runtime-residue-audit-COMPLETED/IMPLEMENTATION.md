# Bead ga-ur1c.6.5 Detect untracked city tmux runtime residue – Implementation Notes

## Implemented Workstreams

- Bumped the deterministic continuity snapshot to v2 and added one city-global runtime surface.
- Captured the native session ledger only through structured `gc session list --json`, projecting only stable identity and lifecycle fields.
- Added a read-only same-UID procfs observer for session-leading `tmux -L city` servers. It recognizes bare and absolute `argv[0]`, never reads process environments or opens the tmux socket, and records only PID/SID/PPID/UID, kernel start ticks, cmdline digest, and sorted children.
- Required stable rereads of proc stat, cmdline, and child membership. Visibility or identity drift becomes `unknown` and fails closed; a process conclusively disappearing during reread is absent.
- Added deterministic audit classifications for untracked, missing, split-brain, and unobservable city runtime, while retaining explicit warning-only readability for historical v1 snapshots.
- Updated the JSON schema, contract, plugin README, and hermetic RED/GREEN coverage.

## Verification So Far

- Focused continuity suite: `40 passed`.
- Related workflow regression suite: `482 passed`.
- Ruff and `git diff --check`: pass.
- Initial full-suite attempt: `2404 passed, 21 skipped, 73 failed`; all failures were classified as a test-harness temp-root mismatch because `PYTEST_DEBUG_TEMPROOT` was outside `tempfile.gettempdir()`.
- Environment-corrected rerun of the exact failed set: `73 passed` with no source change.
- Clean full-suite rerun with aligned pytest and Python temp roots: `2477 passed, 21 skipped` in `230.31s`.
- Live snapshot/audit/status: deterministic BLOCKED on the preserved PID `3136806` residue; no process or lifecycle mutation.
