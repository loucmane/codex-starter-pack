# Findings

- 2026-08-27 — _Pending_ — document new findings here.



## Progress Log

- **2026-08-27 15:03** — [S:20260827|W:ga-y1ei|H:host-wsl:obsidian-readiness|E:sandbox-doctor:obsidian.host_ipc=UNKNOWN;host-wsl-doctor:obsidian.host_ipc=PASS;vault=main] Proved the observer split live: the Codex sandbox reported observer-limited UNKNOWN for Obsidian IPC, while host WSL read the managed ga-zbmk note and reported host-wsl-live-ipc PASS; all four rigs remained suspended.
- **2026-08-27 15:34** — [S:20260827|W:ga-y1ei|H:host-wsl:obsidian-index-refresh|E:vault-source:cfc1bf6eece89cf60a172d6e6967452dffe34a25208381c57dd61c5917026d00;obsidian-read:Beads/ga-y1ei.md] Found that Obsidian's Windows-side watcher can retain its prior index after the managed WSL subtree is atomically replaced. The filesystem gates remained PASS; one supported host-side vault reload made the new note immediately readable.
- 2026-08-28 — Archive preconditions were satisfied and the completed bundle was preserved.
