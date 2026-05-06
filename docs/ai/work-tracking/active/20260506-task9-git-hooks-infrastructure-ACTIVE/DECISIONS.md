# Decisions

- 2026-05-06 - Prioritize Task 9 as the active workflow container for GitHub auth-cache guidance because the changed files are Git/readiness/hook-system surfaces, even though Taskmaster next reported Task 10.
- 2026-05-06 - Keep the SSH/GPG cache guidance as a reusable system-template update, not a private memory or one-off archive note.
- 2026-05-06 - Treat `--no-verify`, signing disablement, or remote changes as explicit user-authorized bypasses only; expired auth cache must be refreshed rather than bypassed.
- 2026-05-06 - Scope Task 9.2 to the proven current gap: local hook installation/parity and missing coverage, not re-creating already-existing pre-commit and CI guard wiring.
- 2026-05-06 - Do not implement untracked `.git/hooks/` scripts as the canonical solution; use tracked config, tested scripts, and documented install/verify commands so the foundation remains portable.
- 2026-05-06 - Treat secret scanning, ruff, pre-push enforcement, and protected-path policy as candidate extensions that require their own baseline evidence before implementation.
- 2026-05-06 - Add `python3 scripts/codex-task hooks verify` as the tracked parity check instead of committing local `.git/hooks/` contents; default mode reports missing local hook install as a warning so CI and fresh clones can still inspect state, while `--require-installed` is the local strict gate.
- 2026-05-06 - Close this workspace's local hook gap with `.venv/bin/pre-commit install` after capturing the expected strict verifier failure; final strict verification now passes without introducing an untracked hook script as the canonical source.
