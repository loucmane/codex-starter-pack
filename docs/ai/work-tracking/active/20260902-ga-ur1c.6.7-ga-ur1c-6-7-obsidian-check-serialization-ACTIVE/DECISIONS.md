# Decisions

- 2026-09-02 — Serialize readers behind the existing registry-cycle writer lock with a finite
  monotonic deadline; do not add retry loops to `codex-wsl-readiness` and do not weaken the
  freshness or live-index gates.
- 2026-09-02 — Keep the writer path nonblocking and expose the read bound as
  `--lock-timeout-seconds`, defaulting to 60 seconds so the installed 120-second doctor command
  retains time to evaluate the completed snapshot.
