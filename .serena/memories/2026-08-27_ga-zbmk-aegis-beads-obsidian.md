# ga-zbmk — Aegis beads-first authority and Obsidian closeout gate

- Primary authority: Gas City bead `ga-zbmk` in the `gascity` rig store.
- Working branch: `codex/ga-zbmk-aegis-beads-obsidian`.
- Working tree: `/home/loucmane/codex/.worktrees/ga-zbmk-aegis-beads-obsidian`.
- Preserve legacy Taskmaster-backed Aegis records; do not allocate a shadow Taskmaster task.
- Keep Obsidian a deterministic, atomic, read-only projection. The real WSL vault is `/home/loucmane/vaults/main`, but publication there is a separate validated boundary.
- S:W:H:E remains the compact evidence grammar: session, work identity, validated handler, and reproducible evidence.
- Gate freshness at readiness, closeout, and explicit vault publication—not after every edit.
- Gate-B attempt 12 passed before this slice began; its signed commit, receipt, and completion evidence remain preserved in the parent workspace scratchpad and must not be cleaned up by this work.
- Implementation: `work_authority.py` normalizes explicit bead JSON/JSONL or legacy Taskmaster; `obsidian_vault.py` renders authority-aware work/evidence and gates readiness/closeout/publication; CLI exposes `--beads-json` and `vault gate`.
- Verification: 657 Claude/Aegis adapter tests passed, 27 focused tests passed, Ruff clean.
- Dogfood: exact `ga-zbmk` snapshot built 2,527 files under `/tmp/ga-zbmk-aegis-vault`, idempotent repeat, passing closeout gate, stale snapshot blocked, source digest `38c062dcacccd896d65344794033c4a33edbd3e14860a2a1f7c09f98ebb9cbb2`.
- Default replicated content excludes bead titles, descriptions, labels, and assignee/owner identity; explicit opt-in is required.
- Real-vault publication was intentionally not performed. After merge, target only a new Aegis-owned subtree below `/home/loucmane/vaults/main/GasCity/<stable-project-key>/Aegis`.
