# Findings

- **2026-09-02 00:04 CEST — Scope and authority**: implement a local, versioned,
  fail-closed Codex Desktop transport-retest attestation consumed only by the
  read-only reboot doctor. The attestation must bind the exact Desktop package
  version, current Windows Codex config SHA-256, rollback backup path and
  SHA-256, successful new-task and resumed-task checks, completion time, and a
  passing outcome. It must not mutate Codex configuration, restart Windows or
  WSL, install packages, or weaken the known-affected-build requirement.
- **2026-09-02 00:04 CEST — Live predecessor**: Desktop version
  `26.825.5331.0` is newer than the local affected table; the current Windows
  config is already workaround-free at SHA-256
  `40e8307b7f86825dbc7291279316fc3a4f0dd338cc9860989c67e24d54dad727`.
  The external rollback backup remains
  `/mnt/c/Users/smoki/.codex/config.toml.bak-pre-codex-app-transport-test-20260829`
  at SHA-256
  `1a6a7bb837e906403c76eb6112184639f12464ac3b472b5e724a7560516d95b4`.
- **2026-09-02 00:04 CEST — Safety decision**: attestation can promote only an
  exact newer build/config pair from `candidate_retest` to verified. A known
  affected build ignores every attestation and still fails when the disabled
  `codex_app` workaround is absent. Malformed, stale, mismatched, failed, or
  incomplete attestations remain warnings and never become authority for a
  configuration change.
