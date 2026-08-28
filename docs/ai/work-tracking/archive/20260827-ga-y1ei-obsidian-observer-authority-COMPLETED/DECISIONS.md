# Decisions

- 2026-08-27 — _Pending_ — capture decisions with context.



## Progress Log

- **2026-08-27 15:20** — [S:20260827|W:ga-y1ei|H:aegis:authority-boundary|E:docs/operations/codex-wsl-reboot-readiness.md;docs/aegis/beads-first-authority-and-obsidian-gate.md] Decided that filesystem vault gates remain authoritative and GUI-independent, while only host WSL may provide negative host-IPC evidence.
- **2026-08-27 15:34** — [S:20260827|W:ga-y1ei|H:aegis:publish-boundary|E:obsidian-cli:reload;vault-gates:readiness,closeout,publication] Kept vault reload outside the doctor: it is an optional host-side publication action after authoritative filesystem success, never a readiness mutation or substitute for vault integrity checks.
- 2026-08-28 — Archived through the supported archive helper; no evidence was deleted.
