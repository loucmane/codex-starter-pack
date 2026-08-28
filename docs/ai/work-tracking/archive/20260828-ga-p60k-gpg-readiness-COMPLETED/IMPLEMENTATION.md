# Bead ga-p60k Pin personal GPG readiness to the intended signing subkey – Implementation Notes

## Implemented

- Added `scripts/codex-gpg-readiness` with a read-only `check` path using
  `gpg-connect-agent --no-autostart` and an attended `unlock` path pinned to
  `FD5585922F5335BC378AD8D42ECF4432C7E7982D!`.
- Accepts either the exact agent cache or a successful exact-key signing proof bound to the
  current WSL boot, GPG-agent PID, and 30-day expiry. The latter is a mode-`0600` runtime
  marker containing no secret or passphrase and closes GnuPG 2.4.4's `KEYINFO cached=-`
  false-negative without weakening identity binding.
- Added an idempotent zsh integration and user-level atomic installer without passphrase
  storage or changes to SSH agent behavior.
- Added exact-schema/fingerprint/keygrip validation to the reboot doctor. Cold or absent
  agent state is `WARN`; contradictory or wrong-identity evidence fails closed.
- Preserved the Windows read-only bootstrap contract: `DEGRADED`/exit 1 remains accepted, so
  a normal cold GPG cache after reboot is recorded rather than treated as machine failure.
- Added fake-agent, PTY, exact-cache/agent-epoch, expiry-binding, installer-mode,
  reload-idempotence, and doctor-contract regressions.
