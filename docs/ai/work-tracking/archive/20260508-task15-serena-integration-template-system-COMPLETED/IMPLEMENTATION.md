# Task 15 Enforce Serena Integration for Template System – Implementation Notes

## Planned Workstreams
- [x] Scope reconciliation: document why Task 15 should not replace deterministic template registry/scanner discovery with live Serena calls.
- [x] Project MCP parity: add Serena to `.mcp.json` so project/Claude sessions have the same core Serena server entry as Codex.
- [x] Helper enforcement: add `python3 scripts/codex-task serena status --strict [--report-file <path>]` to verify `.codex/config.toml`, `.mcp.json`, and `.serena/memories/` readiness.
- [x] Regression coverage: add parser/status tests for the Serena helper and strict missing-config failure.
- [x] Documentation alignment: update Serena guide, tool routing, work-tracking enforcement, memory patterns, and tooling inventory.
- [x] Verification evidence: capture status, pytest, plan-sync, audit, guard, and diff-check reports.
- [x] Taskmaster closure: mark subtasks complete after verification and refresh only Task 15 generated output.

## Evidence
- Serena status: `reports/serena-integration-template-system/serena-status-2026-05-08-final.txt`
- Focused tests: `reports/serena-integration-template-system/tests-2026-05-08-focused-final.txt` (`49 passed`)
- Plan sync: `reports/serena-integration-template-system/plan-sync-2026-05-08.txt`
- Work-tracking audit: `reports/serena-integration-template-system/work-tracking-audit-2026-05-08.txt`
- Guard: `reports/serena-integration-template-system/guard-2026-05-08.txt`
- Diff check: `reports/serena-integration-template-system/diff-check-2026-05-08.txt`
- Serena memory: `2026-05-08_task15_serena_integration`
