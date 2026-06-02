# Aegis Reconcile Mutation Rollback Contract

**Status:** active Task 147 proposal contract.
**Scope:** report/contract only. `aegis reconcile` remains read-only and does not gain
mutation flags, Taskmaster writes, git writes, PR writes, or closeout automation.

## First Candidate Boundary

Task 147 registers exactly one future mutation proposal candidate:

- finding kind: `merged_but_not_done`
- merge-truth proof: `git_ancestor`
- first proposed action: mark the matching Taskmaster task `done`

This candidate is still only a proposal. It remains subject to the Task 146 precision
corpus and an explicit operator confirmation. `github_pr_merged`,
`done_but_not_merged`, multi-PR ambiguity, abandoned branches, stale local stubs, ad hoc
local stubs, and squash/offline unknown merge truth are non-goals for this first mutation
contract.

## Required Proposal Shape

Any future mutation proposal must carry all of these fields before execution:

- **High-confidence finding:** the finding must be `merged_but_not_done` with
  `git_ancestor` proof and must be classified `auto_eligible` by the Task 146 corpus
  classifier.
- **Operator confirmation:** the operator must explicitly confirm the task id, proof
  source, current state, proposed state, and changed-path inventory.
- **Before audit breadcrumb:** an audit record exists before mutation with handler, task id,
  finding kind, proof, planned changed paths, timestamp, and intended outcome.
- **After audit breadcrumb:** an audit record exists after mutation with the same task id
  and proof plus outcome.
- **Blast-radius inventory:** every changed path must appear in an exact registered path
  set. A changed path outside the inventory fails the contract.
- **Rollback handle:** every registered changed path has a captured before state or an
  equivalent restoration source.
- **Rollback verification:** after rollback, the registered paths and the isolated fixture
  tree must match the before snapshot.

## Observed Taskmaster Done Cascade

The Task 147 fixture runs the real Taskmaster status path in an isolated temp repository:

```bash
task-master set-status --id=42 --status=done
task-master generate
```

The repo-specific `python3 scripts/codex-task taskmaster generate-one --id 42` helper is
not used in the isolated fixture because it resolves to this source checkout. The native
Taskmaster `generate` command is the fixture-local generated-file refresh.

Observed changed-path inventory:

- `.taskmaster/tasks/tasks.json`
- `.taskmaster/tasks/task_042.md`

Observed unchanged control-plane surface:

- `.taskmaster/state.json` exists after the pre-snapshot fixture setup, but the done
  cascade does not change it. It is deliberately not a registered rollback path because the
  exact-delta contract registers actual deltas only.

No `docs/ai/work-tracking/**`, `sessions/**`, `plans/**`, `.plan_state/**`, `.git/HEAD`,
`.git/refs/**`, or `.git/packed-refs` deltas are part of the first candidate's observed
Taskmaster-only cascade in this fixture.

## Enforcing Tests

| Contract clause | Enforcing test |
| --- | --- |
| First candidate is only `merged_but_not_done` with `git_ancestor` proof | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_first_mutation_candidate_requires_git_ancestor_confirmation_and_audits` |
| `github_pr_merged`, `done_but_not_merged`, manual-only classes, and squash/offline unknown merge truth cannot enter the proposal set | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_manual_ambiguous_and_non_first_auto_findings_cannot_enter_proposal_set` |
| Operator confirmation and before/after audit breadcrumbs are mandatory | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_proposal_contract_rejects_missing_confirmation_or_audits` |
| Real Taskmaster done cascade has an exact registered blast radius | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_real_taskmaster_done_cascade_has_exact_registered_blast_radius` |
| Unregistered changed paths fail the blast-radius contract | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_blast_radius_contract_rejects_unregistered_changed_path` |
| Rollback restores registered paths and verifies the whole isolated tree | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_rollback_handle_restores_registered_paths_and_verifies_tree` |
| Every registered path needs a restoration step | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_rollback_contract_requires_restoration_for_each_registered_path` |
| Rollback capture handles missing paths, directories, symlinks, and type restoration | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_rollback_handle_restores_missing_files_directories_and_symlinks` |

## Non-Goals

- No `--apply`, `--auto`, `--fix`, `--set-status`, `--done`, `--closeout`, `--mutate`,
  `--write`, or `--push` reconcile flag.
- No mutation implementation in `scripts/_aegis_installer.py::reconcile`.
- No behavior change in `scripts/codex-task aegis reconcile`.
- No behavior change in `aegis_foundation/cli.py::handle_reconcile`.
- No behavior change in MCP `aegis.reconcile`.
- No automatic rollback command.
- No mutation for squash/GitHub-only proof, open PR drift, stale stubs, local ad hoc stubs,
  abandoned in-progress branches, or multi-PR ambiguity.
