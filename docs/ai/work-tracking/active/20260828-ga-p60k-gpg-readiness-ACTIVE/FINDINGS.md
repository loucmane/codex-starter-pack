# Findings

- 2026-08-28 — The historical readiness probe accepted any cached GPG key, so revoked
  subkey `5BF9…113F` could suppress the intended `FD55…982D` prompt.
- 2026-08-28 — Public keyring metadata independently binds `FD55…982D` to keygrip
  `640406DD1B34A5EA0BB7CB46F21071BB3DB370FA`; retired `5BF9…113F` has a distinct keygrip.
- 2026-08-28 — The prior shell snippet was not safe to source twice because it redeclared a
  read-only variable. The corrected snippet is idempotent and fails on helper-path drift.
- 2026-08-28 — Pinentry must be retargeted with `updatestartuptty` before an attended unlock;
  relying only on inherited `GPG_TTY` can make a healthy prompt invisible after shell changes.
- 2026-08-28 — Live GnuPG 2.4.4 completed an exact `FD55…982D!` signing proof while
  `KEYINFO` continued to report `cached=-`; treating that implementation detail as the only
  readiness authority caused a false failure loop. Readiness now accepts either the exact
  agent cache or a non-secret proof bound to the exact key, WSL boot, agent PID, and expiry.
