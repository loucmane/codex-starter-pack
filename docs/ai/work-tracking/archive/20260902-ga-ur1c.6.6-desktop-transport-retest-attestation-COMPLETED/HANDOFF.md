# Bead ga-ur1c.6.6 Record verified Codex Desktop transport retests – Handoff Summary

## Current State
- PASS. Source implementation merged through PR #364 as merge commit
  `b67c79a455b5fedc302c13737ea9a7c1d5ba8977`, with byte-identical reviewed
  tree `e6f630d13569ab6ce081905a32786bc83111bf73`. The append-forward digest
  correction merged through PR #365 as `d46192b866a3651e8ad8158ba5e5e7d7b11402aa`,
  tree `380226b48a725dad6e1705906cad6dfd5e6f062e`.
- The private retest attestation is installed at SHA-256
  `b871be3659f52964b0c3b83b4b8f56c1ba9f7e59b33770bd81930314c7483722`.
  The user-level doctor is version `2026.09.02.1`, SHA-256
  `4792405845b70df1f7d50feab22649e5312852fb9bf026a9e8711b6fb410877e`,
  and exact replay is idempotent.
- Host doctor evidence is READY with 20 PASS, 0 WARN, 0 FAIL at SHA-256
  `ef868e47e21cf7c5b4da86c78ed5200c79a4969442b76a8d353467895d29d67d`.
  Both Desktop checks consume the exact verified attestation. The supervisor
  remained PID 813835 with zero restarts and every project rig remained
  suspended.

## Next Steps
- Close `ga-ur1c.6.6` after supported source-workflow archival and terminal
  Obsidian projection.
- Continue the independently tracked `ga-ur1c.6.7` repair for the discovered
  reconciler-cycle health-check race; it does not invalidate this Desktop
  transport acceptance.
- Archived on 2026-09-02 00:52 CEST — Folder moved to archive and tracker marked COMPLETED.
