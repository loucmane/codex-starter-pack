# Task 144 Codify Aegis Reconcile Read-Only Contract – Implementation Notes

## Planned Workstreams
- Added `docs/aegis/reconcile-promotion-contract.md` to make the Task 143 promotion criteria durable:
  reconcile remains read-only/report-only until a separate future task proves operator confirmation,
  audit breadcrumb, rollback evidence, high-confidence proof, and manual-only finding rules.
- Added CLI parser regression coverage in `tests/meta_workflow_guard/test_aegis_installer.py`:
  both `scripts/codex-task aegis reconcile` and packaged `aegis reconcile` accept only the current
  read-only options and reject mutation-shaped flags.
- Added MCP contract coverage in `tests/meta_workflow_guard/test_aegis_mcp_server.py`: schema is
  limited to `target_dir`, `base_ref`, and `use_github`; execution returns `read_only=True`; git
  status remains unchanged after a reconcile smoke.

## Progress Log
- **2026-06-02 13:43 CEST** — [S:20260602|W:task144-reconcile-readonly-contract|H:codex:scope|E:docs/ai/work-tracking/active/20260602-task144-reconcile-readonly-contract-ACTIVE/designs/wizard-flow.md] Confirmed this task is a contract/test gate only; no reconcile mutation mode is in scope.
- **2026-06-02 13:45 CEST** — [S:20260602|W:task144-reconcile-readonly-contract|H:codex:apply_patch|E:docs/aegis/reconcile-promotion-contract.md] Added the reconcile promotion contract with Task 143 evidence link and future mutation criteria.
- **2026-06-02 13:45 CEST** — [S:20260602|W:task144-reconcile-readonly-contract|H:codex:apply_patch|E:tests/meta_workflow_guard/test_aegis_installer.py] Added CLI parser tests that reject reconcile mutation flags for both repo helper and packaged CLI.
- **2026-06-02 13:45 CEST** — [S:20260602|W:task144-reconcile-readonly-contract|H:codex:apply_patch|E:tests/meta_workflow_guard/test_aegis_mcp_server.py] Added MCP schema and execution tests for the read-only reconcile contract.
