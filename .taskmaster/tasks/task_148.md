# Task ID: 148

**Title:** Add inert reconcile mutation-candidate preview contract

**Status:** done

**Dependencies:** 147 ✓

**Priority:** medium

**Description:** Add an opt-in, report-only preview contract for future Aegis reconcile mutation candidates, limited to `merged_but_not_done` findings with `git_ancestor` proof. The preview must remain inert for autonomous agents: non-executable, not action-shaped, not consumed by writers, and unable to mutate Taskmaster, git, PR, Aegis closeout, or workflow state.

**Details:**

Build this as a contract/test/docs extension on top of the current Aegis reconcile stack: core report generation in `scripts/_aegis_installer.py::reconcile`, package CLI handling in `aegis_foundation/cli.py::handle_reconcile`, wrapper parser in `scripts/codex-task`, and MCP exposure in `aegis_mcp/server.py::aegis_reconcile`. Use the existing precision corpus in `tests/meta_workflow_guard/reconcile_precision_corpus.py` and `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py`, plus Task 147's rollback/blast-radius helper in `tests/meta_workflow_guard/reconcile_mutation_rollback_contract.py` and `docs/aegis/reconcile-mutation-rollback-contract.md`.

Implement the preview as an explicit, opt-in report surface only if the task deliberately chooses to expose it; otherwise keep default reconcile output unchanged and observational. Do not add mutation behavior, Taskmaster writes, git writes, PR writes, closeout writes, or new reconcile flags such as `--apply`, `--auto`, `--fix`, `--status`, `--set-status`, `--done`, `--closeout`, `--mutate`, `--write`, or `--push`. Preserve the existing denylist in `tests/meta_workflow_guard/test_aegis_installer.py::RECONCILE_MUTATION_FLAGS` and MCP mutation parameter denylist in `tests/meta_workflow_guard/test_aegis_mcp_server.py::RECONCILE_MUTATION_PARAMETER_NAMES`.

Create a small preview-contract helper, likely under `tests/meta_workflow_guard/reconcile_mutation_candidate_preview_contract.py`, that derives inert preview entries from reconcile findings or precision-corpus `FindingKey` values without calling any writer. Candidate entries must be named `mutation_candidate` or `preview`; never use `proposed_action`. Each candidate must include `executable=false`, `apply_path_exists=false`, `blocked_reason="report-only per Task 147 contract"`, proof source, task id, predicted blast-radius paths from the Task 147 `BlastRadiusContract`, a rollback contract reference, and a statement that actual blast radius is verified by the Task 145 side-effect oracle at mutation time. Ensure the structure is deliberately not command-shaped: no command strings, no tool names, no suggested CLI/MCP mutation call, no `apply`, no `auto`, no `fix`, no `set_status`, and no status-transition instruction.

Scope candidate creation strictly to `merged_but_not_done` with `git_ancestor` proof. Treat `merged_but_not_done` with `github_pr_merged`, `done_but_not_merged`, manual-only classes (`multi_pr_epic_ambiguity`, `abandoned_in_progress_branch`, `stale_local_stub`, `local_ad_hoc_stub`), and squash/offline unknown truth (`git_only_non_ancestor_or_missing_base`) as excluded. Excluded records should be phrased as manual-only or contract-excluded records with `class`, `reason`, and `would_require` fields; do not phrase them as TODOs or pending work.

Add no-consumer tests proving no production writer path reads preview data to drive mutation. At minimum, assert that `scripts/_aegis_installer.py::reconcile`, `format_reconcile_summary`, `aegis_foundation/cli.py::handle_reconcile`, `scripts/codex-task aegis reconcile`, and MCP `aegis.reconcile` do not dispatch Taskmaster status changes, closeout writes, git/PR writes, repair/install/start/kickoff/log calls, or any apply-like path based on preview/candidate keys. Prefer focused static contract tests plus side-effect oracle execution tests over broad brittle source snapshots.

Add documentation, likely `docs/aegis/reconcile-mutation-candidate-preview-contract.md`, mapping every inertness clause to concrete pytest tests. Cross-reference `docs/aegis/reconcile-mutation-rollback-contract.md`, the Task 146 precision corpus docs, and the Task 145 side-effect oracle. If any human-readable reconcile summary mentions preview data, it must clearly say report-only/manual-review only and must not include executable commands.

**Test Strategy:**

Add focused pytest coverage for the preview contract, for example `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py`.

Cover positive and negative classification cases: only `merged_but_not_done` with `git_ancestor` yields one inert candidate; `merged_but_not_done` with `github_pr_merged`, `done_but_not_merged`, manual-only findings, and squash/offline unknown truth yield zero candidates and/or explicit contract exclusions.

Add schema/shape tests asserting candidate entries use `mutation_candidate` or `preview`, never `proposed_action`, and include `executable=false`, `apply_path_exists=false`, the Task 147 blocked reason, proof source, task id, predicted blast-radius paths, rollback contract reference, and the Task 145 actual-blast-radius verification statement.

Add no-consumer tests proving preview data cannot drive writes, plus side-effect oracle tests confirming reconcile preview runs leave filesystem and git control-plane state unchanged except explicitly allowed report output paths. Add gate coverage showing an out-of-band `task-master set-status` attempt for a non-active proposed task remains blocked by installed pre-mutation enforcement or the relevant classifier contract.

Re-run existing related gates: `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py`, `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py`, focused installer reconcile tests in `tests/meta_workflow_guard/test_aegis_installer.py`, MCP reconcile tests in `tests/meta_workflow_guard/test_aegis_mcp_server.py`, side-effect oracle tests, `python3 scripts/codex-task guard validate`, work-tracking audit, and `python3 scripts/codex-task taskmaster health`. Confirm Task 144 mutation-flag denylist and MCP schema tests still pass unchanged.
