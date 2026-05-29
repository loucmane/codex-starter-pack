# Task 128 Aegis closeout output and local workflow follow-up – Implementation Notes

## Implemented Workstreams

- Updated Aegis next-action guidance so installed projects with no current work suggest `aegis.start` / MCP `aegis.start apply=true`, not `aegis.kickoff` with placeholder numeric ids.
- Updated the MCP `aegis.start_task` prompt to tell agents to use `aegis.start` for normal-language local work and reserve `aegis.kickoff` for explicit external numeric task ids.
- Added concise CLI closeout summaries through `format_closeout_summary()`. Default `aegis closeout` output now shows status, dry-run/final mode, failed required count, warnings, pending tracking count, closeout report state, failed gate ids, first repair command when available, and the next suggested command.
- Added `--json` to `aegis closeout` in both `aegis_foundation/cli.py` and `scripts/codex-task` so automation can still parse the full structured report.
- Changed successful final closeout to update current-work state from `in-progress` to `completed`, including the nested task payload.
- Allowed strict current-work checks and closeout readiness to accept completed current-work state when it has `closeout_passed_at`, making post-closeout checks idempotent.
- Updated the installed Claude gate classifier so `aegis start` and MCP `mcp__aegis__aegis_start` are both recognized as bootstrap operations before readiness is READY, while non-bootstrap mutations like `aegis verify` still block.
- Mirrored runtime script and docs changes into `aegis_foundation/assets/` so newly installed projects receive the corrected behavior and guidance.
- Updated public docs and release docs to describe `aegis start` as the default local workflow, closeout's concise default output, and `--json` for automation.
