# ga-y1ei Obsidian observer-authority hardening

- Authority: Gas City bead `ga-y1ei` on branch `codex/ga-y1ei-obsidian-observer-authority`.
- Root cause: a Codex sandbox could not reach host-WSL Obsidian IPC and an ad-hoc probe incorrectly translated that observer limitation into “the GUI is not running.”
- Contract: environment-sensitive readiness reports carry an observer and authority. Sandbox or container negatives are `UNKNOWN(observer-limited)`; only host WSL may assert host service or application state.
- Obsidian boundary: filesystem-native Aegis vault build/check/gate remains authoritative and GUI-independent. The live CLI check is an optional host-WSL smoke over the configured vault and one managed note.
- Reuse: Gas City, HPFetcher, Blog, and new projects use the same shared doctor with project-specific managed-note paths; workers never infer cross-UID, systemd, socket, or host-app absence from restricted views.
- Verification: 2,215 repository tests passed with 21 intentional skips; Ruff passed; live sandbox evidence reported `obsidian.host_ipc=unknown`; host WSL reported `pass` and read the managed `ga-zbmk` note.
- Installed doctor: version `2026.08.27.1`, SHA-256 `407e6badd81f735cb569a5bc99fca7c9cf97a5eb79b8bb41618b82eab0aa0fd8`, byte-identical at `/home/loucmane/.local/bin/codex-wsl-readiness`.
- Historical correction: closed bead `ga-zbmk` retains its original note plus an append-forward correction documenting the sandbox/host distinction.
