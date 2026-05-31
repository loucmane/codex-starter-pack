# Task 130 Aegis Normal-Language Workflow Acceptance and First-Pass Closeout Hardening – Implementation Notes

## Planned Workstreams
- Align public MCP onboarding with `aegis.init -> aegis.start` for normal-language tasks.
- Direct handoff-only closeout failures to deterministic `aegis.handoff_repair`.
- Require a read-only post-closeout `aegis.doctor` health check before the final user report.

## Progress Log

- **2026-05-29 12:31** — [S:20260529|W:task130-aegis-normal-language-workflow-acceptance|H:codex:implement|E:scripts/_aegis_installer.py] Aligned Aegis next-action and init guidance with the public normal-language MCP flow.
- **2026-05-29 13:15** — [S:20260529|W:task130-aegis-normal-language-workflow-acceptance|H:codex:implement|E:scripts/_aegis_installer.py] Changed failed closeout next-action guidance so handoff-only failures point directly to aegis.handoff_repair apply=true.
- **2026-05-30 11:58** — [S:20260530|W:task130-aegis-normal-language-workflow-acceptance|H:codex:implement|E:scripts/_aegis_installer.py] Changed successful final closeout next-action guidance to `run_post_closeout_doctor`, suggesting read-only MCP `aegis.doctor` before the final user report.
- **2026-05-30 11:58** — [S:20260530|W:task130-aegis-normal-language-workflow-acceptance|H:codex:implement|E:aegis_mcp/server.py] Updated MCP workflow prompts so Claude should report completion only after closeout passes and doctor reports the completed state.
