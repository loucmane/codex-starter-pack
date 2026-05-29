# Decisions

- 2026-05-28 — Make `aegis.start` the primary local-work recommendation in `aegis next`, MCP prompts, and public docs. Keep `aegis.kickoff` for projects that provide an explicit external numeric task id.
- 2026-05-28 — Keep MCP tool responses structured, but make CLI closeout output concise by default. Add `--json` to the package CLI and repo wrapper so tests, scripts, and automation can still consume the complete closeout report.
- 2026-05-28 — On successful final closeout, mark both `.aegis/state/current-work.json.status` and `.aegis/state/current-work.json.task.status` as `completed`, while retaining `closeout_passed_at` and `closeout_report`.
- 2026-05-28 — Make closeout idempotent after completion: a completed current-work payload with `closeout_passed_at` is valid closeout readiness evidence, so repeated closeout readiness checks do not report a false blocker.
- 2026-05-28 — Treat `aegis.start` and `aegis.kickoff` as explicit readiness-bootstrap operations across both Bash and MCP hook payloads. Non-bootstrap Aegis operations such as `aegis.verify` remain blocked until readiness is READY.
