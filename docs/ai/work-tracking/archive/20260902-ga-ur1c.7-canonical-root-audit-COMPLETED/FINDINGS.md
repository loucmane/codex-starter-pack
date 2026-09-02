# Findings

- 2026-09-02 — The continuity snapshot omitted the registered canonical checkout itself. It could therefore report `ok=true` while `/home/loucmane/gas-city-ops` `main` was 23 commits behind its existing local `refs/remotes/origin/main` and carried two tracked sync-log records.
- 2026-09-02 — The two local sync-log records are append-only evidence, not source edits to discard: both bind `ga-ur1c.6.4` to plan SHA-256 `4af9dd5...` and tracker SHA-256 `69b5eefe...`, at `2026-09-01T22:30:08.245598+02:00` and `2026-09-02T09:32:55.686530+02:00`.
- 2026-09-02 — Registered HPFetcher, Blog, and Gas City canonical roots intentionally have non-base branches checked out. Their exact divergence must remain visible without treating operator workspaces as stale `main` checkouts or mutating them.
- 2026-09-02 — RED proof: `test_report_blocks_a_stale_canonical_project_root_once` failed because the pre-repair report returned `ok=true`.
- 2026-09-02 — Live repaired-source proof: snapshot SHA-256 `b13998ba3144e258ed5348a0ad658df58a281ed3cbe5e9eddd5fa16f0968618d` produced report SHA-256 `8f565a59394617310a6112a10c74449541e5600a2f627749b948d22ca7f07f52`, with one blocking `canonical-root-behind-base` finding for Operations and bounded warnings for deliberate feature branches or tracked dirt.
- 2026-09-02 — Archive preconditions were satisfied and the completed bundle was preserved.
