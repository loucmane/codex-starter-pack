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
  config is already workaround-free. The full SHA-256 values originally
  expanded here from abbreviated relay prefixes were not authoritative and are
  superseded by the direct pre-install readback below.
  <!-- superseded non-authoritative values:
  `40e8307b7f86825dbc7291279316fc3a4f0dd338cc9860989c67e24d54dad727`.
  The external rollback backup remains
  `/mnt/c/Users/smoki/.codex/config.toml.bak-pre-codex-app-transport-test-20260829`
  at SHA-256
  `1a6a7bb837e906403c76eb6112184639f12464ac3b472b5e724a7560516d95b4`.
  -->
- **2026-09-02 00:04 CEST — Safety decision**: attestation can promote only an
  exact newer build/config pair from `candidate_retest` to verified. A known
  affected build ignores every attestation and still fails when the disabled
  `codex_app` workaround is absent. Malformed, stale, mismatched, failed, or
  incomplete attestations remain warnings and never become authority for a
  configuration change.
- **2026-09-02 00:28 CEST — Append-forward digest correction**: direct
  pre-install hashing established Windows config SHA-256
  `40e8307bf63ac50fbbb4a6175498ab2efba14d47fce9ed6043498219e4b9ce05`
  and rollback backup SHA-256
  `1a6a7bb05ee77e1f743cf63de8894c039a2b7fd6c7e2c5d6d27ded8eb4ea6dc3`.
  This entry explicitly supersedes the two full strings expanded from truncated
  prefixes above; the recorder and doctor bind only these direct disk reads.
- **2026-09-02 00:44 CEST — Live acceptance**: the local attestation at
  `/home/loucmane/.config/gas-city/codex-desktop-transport-retest.json` is mode
  0600 and SHA-256
  `b871be3659f52964b0c3b83b4b8f56c1ba9f7e59b33770bd81930314c7483722`.
  The installed doctor is version `2026.09.02.1` and SHA-256
  `4792405845b70df1f7d50feab22649e5312852fb9bf026a9e8711b6fb410877e`;
  its exact recorder replay returned `changed=false`. Host evidence
  `doctor-stable-pass.json` is SHA-256
  `ef868e47e21cf7c5b4da86c78ed5200c79a4969442b76a8d353467895d29d67d`
  with overall READY, pass=20, warn=0, fail=0. Desktop version and absent
  workaround both PASS through the verified exact attestation.
- **2026-09-02 00:44 CEST — Independent race finding**: the first host doctor
  overlapped `aegis-obsidian-reconcile.timer` and preserved report SHA-256
  `d161eeddece9a391d835f716af008790a8b4bf74c9d419c87c3dae781387cd7a`.
  It had 19 PASS and one false reconciler failure (`status=already-running`).
  The exact check passed all four projects and the dashboard after the cycle,
  and the stable doctor then passed 20/20. Repair Bead `ga-ur1c.6.7` owns the
  bounded check/reconciliation serialization defect; no retry or warning was
  erased.
- 2026-09-02 — Archive preconditions were satisfied and the completed bundle was preserved.
