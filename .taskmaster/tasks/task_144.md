# Task ID: 144

**Title:** Codify Aegis Reconcile Read-Only Contract

**Status:** done

**Dependencies:** 143 ✓

**Priority:** medium

**Description:** Encode Task 143 reconcile promotion criteria as an explicit documented contract and regression test gate while preserving report-only behavior for CLI and MCP reconcile surfaces.

**Details:**

Add a read-only contract document for Aegis reconcile that references Task 143 evidence in `docs/ai/work-tracking/active/20260602-task143-reconcile-promotion-criteria-ACTIVE/reports/reconcile-promotion-criteria/promotion-criteria-summary.md` and the existing read-only implementation from Task 141. The contract should state that `python3 scripts/codex-task aegis reconcile`, package CLI `aegis_foundation/cli.py::handle_reconcile`, core `scripts/_aegis_installer.py::reconcile`, and MCP tool `aegis_mcp/server.py::aegis_reconcile` are report-only and must not mutate Taskmaster status, Aegis workflow state, git refs, PR state, closeout artifacts, or local task stubs. Document future promotion criteria for any separate reconcile auto-mutation task: explicit operator confirmation, an audit breadcrumb before and after every proposed mutation, rollback evidence or a reversible operation plan, high-confidence proof requirements for each mutation class, manual-only finding kinds, and separate future-task ownership. Treat `multi_pr_epic_ambiguity`, `abandoned_in_progress_branch`, `stale_local_stub`, `local_ad_hoc_stub`, and squash/offline unknown merge truth as manual-only unless a future task proves otherwise. Do not implement mutation behavior, mutation helpers, status-setting paths, closeout automation, git write commands, PR writes, or Taskmaster mutation from reconcile. Add focused parser/contract tests in the existing patterns used by `tests/meta_workflow_guard/test_aegis_installer.py` and `tests/meta_workflow_guard/test_aegis_mcp_server.py`. For `scripts/codex-task` reconcile parser and `aegis_foundation/cli.py` reconcile parser, assert only current read-only options are accepted (`--target-dir`, `--base-ref`, `--no-github`, `--json`) and that mutating options such as `--apply`, `--auto`, `--fix`, `--set-status`, `--closeout`, `--mutate`, or equivalent status/write aliases fail parsing for the reconcile subcommand. For MCP `aegis.reconcile`, assert its tool schema exposes only `target_dir`, `base_ref`, and `use_github`, its description continues to identify it as read-only/report-first, its execution result is marked `read_only=True`, and no apply/auto/fix/status/closeout/mutate parameter appears. If adding a reusable denylist, keep it local to tests or a clearly named read-only contract helper so other Aegis mutating commands like `install --apply`, `repair --apply`, and `closeout` remain unaffected.

**Test Strategy:**

Run focused pytest covering reconcile read-only contract and parser/MCP surfaces, including the existing reconcile tests and any new tests added for denied mutating flags. Verify `python3 scripts/codex-task aegis reconcile --target-dir . --no-github` and MCP `aegis.reconcile` remain report-only and do not create or modify Taskmaster, Aegis state, git, PR, or closeout artifacts beyond intentional task evidence. Run `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-guard validate`, and `python3 scripts/codex-task work-tracking audit`. Also compare `git status --short` before and after reconcile smoke commands to confirm no mutation behavior was introduced.
