# Task ID: 147

**Title:** Define Reconcile Mutation Rollback and Blast-Radius Proposal Contract

**Status:** done

**Dependencies:** 146 ✓

**Priority:** medium

**Description:** Add a report/contract-only proposal for future Aegis reconcile auto-mutation rollback safety, scoped to the first candidate class `merged_but_not_done` with `git_ancestor` proof. Keep reconcile itself strictly read-only with no new mutation flags, no Taskmaster writes, and no behavior changes to CLI, MCP, or core reconcile surfaces.

**Details:**

Implement this as tests, fixtures, reports, and documentation only. Do not modify behavior in `scripts/_aegis_installer.py::reconcile`, `scripts/codex-task aegis reconcile`, `aegis_foundation/cli.py::handle_reconcile`, or MCP `aegis.reconcile`, and do not add `--apply`, `--auto`, `--fix`, `--status`, `--set-status`, or equivalent reconcile flags.

Build on the existing Task 146 precision corpus in `tests/meta_workflow_guard/reconcile_precision_corpus.py` and `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py`, where auto/manual labels are recomputed from actual `scripts/_aegis_installer.py::reconcile` output. Define the future mutation proposal set as a separate test/support concept, not as reconcile behavior. Its first and only candidate class for this task should be `merged_but_not_done` with merge-truth proof `git_ancestor`, and it must remain subject to Task 146 precision eligibility plus explicit operator confirmation. Ensure `github_pr_merged`, `done_but_not_merged`, and all manual-only classes remain outside this first proposal contract unless deliberately documented as non-goals.

Add a new focused contract helper/test module under `tests/meta_workflow_guard/`, for example `reconcile_mutation_rollback_contract.py` and `test_aegis_reconcile_mutation_rollback_contract.py`. Reuse fixture helpers from `tests/meta_workflow_guard/test_aegis_installer.py` such as `init_git_repo`, `write_taskmaster_tasks`, `commit_file`, and `git`. Reuse the Task 145 whole-tree snapshot oracle from `tests/meta_workflow_guard/reconcile_side_effect_oracle.py::snapshot_whole_tree` or an equivalent whole-tree before/after snapshot that captures path existence, type, mode, symlink target, content digest, and git/control-plane paths.

Create an isolated fixture that inventories the actual cascade of manually marking a Taskmaster task done for a `merged_but_not_done` / `git_ancestor` case. The test should run the real Taskmaster completion path available in this repo where feasible, including `task-master set-status --id=<id> --status=done` and the targeted generated-file refresh `python3 scripts/codex-task taskmaster generate-one --id <id>`, inside a temp fixture. Capture before/after whole-tree snapshots and produce a stable changed-path inventory covering `.taskmaster/tasks/tasks.json`, generated task markdown such as `.taskmaster/tasks/task_<id>.md` or the fixture's actual generated naming, any Taskmaster state files observed, active work-tracking/session/plan surfaces such as `docs/ai/work-tracking/**`, `sessions/**`, `plans/**`, `.plan_state/**`, and git/control-plane effects such as `.git/HEAD`, `.git/refs/**`, `.git/packed-refs`, and tolerated discovery churn.

Define a rollback contract as structured data and docs rather than executable reconcile mutation: before snapshot, audit breadcrumb before the proposed mutation, audit breadcrumb after the proposed mutation, rollback handle, restoration procedure, and rollback verification for every registered changed path. The contract should require exact path registration: any changed path not present in the blast-radius inventory fails. The restoration procedure should explain how each path class is restored from the before snapshot or known rollback handle, and rollback verification should prove the restored tree matches the before snapshot for all registered paths.

Add negative tests proving manual-only or ambiguous findings from the existing corpus, including `multi_pr_epic_ambiguity`, `abandoned_in_progress_branch`, `stale_local_stub`, `local_ad_hoc_stub`, and git-only squash/offline unknown merge truth, cannot enter the mutation proposal set. Add a negative test that injects or simulates an unregistered changed path and proves the blast-radius contract fails. Add a negative test that omits operator confirmation or either audit breadcrumb and proves the proposal contract fails.

Update `docs/aegis/reconcile-promotion-contract.md` and/or add a focused document such as `docs/aegis/reconcile-mutation-rollback-contract.md`. The documentation must tie every rollback, audit, operator-confirmation, and blast-radius clause to concrete enforcing pytest test names. Keep `docs/aegis/reconcile-precision-corpus.md` aligned with the statement that this task is still proposal/report-only and does not promote reconcile into mutation.

**Test Strategy:**

Run the new focused rollback contract tests, for example `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py`.

Run the existing precision and corpus gate: `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py`.

Run existing reconcile read-only and parser/MCP coverage, including `uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -k reconcile` and `uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py -k reconcile`.

Run the Task 145 oracle tests: `uv run python -m pytest tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py`.

Verify repository health and workflow gates with `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task guard validate`, and `python3 scripts/codex-task work-tracking audit`. Acceptance requires no behavior change to reconcile, no new reconcile mutation flags, exact changed-path blast-radius proof in isolated fixtures, rollback verification for every registered path, and documentation mapping each contract clause to enforcing tests.
