# Task 128 Aegis closeout output and local workflow follow-up – Changelog

- 2026-05-28 13:10 CEST — Initialized active work-tracking folder.
- 2026-05-28 13:29 CEST — Updated Aegis local-work guidance to prefer `aegis.start` and explicit-id `aegis.kickoff`, including MCP prompts and packaged docs.
- 2026-05-28 13:29 CEST — Added concise closeout CLI output and `--json` opt-in for full structured reports.
- 2026-05-28 13:29 CEST — Made passed closeout mark current work and nested task state as `completed`.
- 2026-05-28 13:29 CEST — Fixed post-closeout closeout-readiness idempotency so completed closeout state does not fail its own re-check.
- 2026-05-28 13:29 CEST — Mirrored changed scripts and docs into `aegis_foundation/assets/`.
- 2026-05-28 15:30 CEST — Fixed the installed Claude gate classifier so `aegis.start` is an explicit bootstrap exception through both CLI and MCP, matching the expected normal-language local workflow.
