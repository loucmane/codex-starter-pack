# Decisions

- 2026-05-06 - Prioritize Task 9 as the active workflow container for GitHub auth-cache guidance because the changed files are Git/readiness/hook-system surfaces, even though Taskmaster next reported Task 10.
- 2026-05-06 - Keep the SSH/GPG cache guidance as a reusable system-template update, not a private memory or one-off archive note.
- 2026-05-06 - Treat `--no-verify`, signing disablement, or remote changes as explicit user-authorized bypasses only; expired auth cache must be refreshed rather than bypassed.
