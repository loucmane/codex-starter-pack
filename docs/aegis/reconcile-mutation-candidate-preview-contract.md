# Aegis Reconcile Mutation-Candidate Preview Contract

**Status:** active Task 148/149 contract.
**Scope:** opt-in, report-only candidate preview for future reconcile mutation. This
contract does not add mutation behavior and does not make reconcile an execution surface.

## Inertness Target

The consumer of reconcile output may be an autonomous agent. For that reason, a
machine-readable candidate preview must be inert: it cannot look like an instruction an
agent should execute and it cannot be consumed by a writer path.

The preview is opt-in through `preview_candidates` / `--preview-candidates`. Default
reconcile output remains observational and does not include `mutation_candidate_preview`.

## Candidate Boundary

Task 148 admits exactly one candidate class:

- finding kind: `merged_but_not_done`
- proof: `git_ancestor`

The preview is still non-mutating. It only says that a candidate is eligible for operator
review under the existing Task 146 precision corpus and Task 147 rollback/blast-radius
contract.

Task 149 may reference this preview as input to a future apply-path proposal contract. That
reference does not change this contract: preview records remain non-executable and are not
consumed by writer functions in Task 149.

Excluded classes remain contract-excluded or manual-only:

- `merged_but_not_done` with `github_pr_merged`
- `done_but_not_merged`
- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- `git_only_non_ancestor_or_missing_base`

Exclusion records are phrased as contract exclusions. They are not TODOs and not a roadmap
for an agent to handle.

## Preview Shape

Each candidate entry must use `record_type: mutation_candidate`. It must never use
`proposed_action`.

Every candidate and the preview section itself must include:

- `executable: false`
- `apply_path_exists: false`
- `blocked_reason: "report-only per Task 147 contract"`

Every candidate must also include:

- task id
- finding kind
- proof source
- predicted blast-radius paths:
  - `.taskmaster/tasks/tasks.json`
  - `.taskmaster/tasks/task_<id>.md`
- rollback contract reference:
  - `docs/aegis/reconcile-mutation-rollback-contract.md`
- operator confirmation requirement
- statement that actual blast radius is verified by the Task 145 side-effect oracle at
  mutation time

The preview must not include:

- shell commands
- tool names
- MCP call suggestions
- Taskmaster status commands
- git or GitHub write commands
- closeout or repair calls
- `--apply`, `--auto`, `--fix`, or status-setting flags

## Enforcement Map

| Contract clause | Enforcing test |
| --- | --- |
| Default reconcile output remains observational without preview data | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_reconcile_default_output_stays_observational_without_candidate_preview` |
| Opt-in candidate preview is read-only and inert | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_reconcile_preview_candidate_is_opt_in_inert_data` |
| Candidate eligibility reuses the Task 146 precision corpus boundary | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_preview_builder_reuses_precision_corpus_boundary` |
| Human-readable summary remains report-only and non-executable | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_preview_summary_is_report_only_and_non_executable` |
| Preview data is not consumed by writer functions | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_preview_data_is_not_consumed_by_writer_functions` |
| Out-of-band Taskmaster completion for a non-active previewed task is blocked by the installed gate | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_preview_cannot_be_executed_out_of_band_by_taskmaster_gate` |
| CLI parser mutation flags remain rejected while `--preview-candidates` is explicitly read-only | `tests/meta_workflow_guard/test_aegis_installer.py::test_reconcile_cli_parsers_reject_mutation_flags` |
| MCP schema keeps mutation parameters out while allowing read-only `preview_candidates` | `tests/meta_workflow_guard/test_aegis_mcp_server.py::test_reconcile_mcp_schema_keeps_report_only_contract` |
| Reconcile preview execution remains side-effect free | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_reconcile_preview_candidate_is_opt_in_inert_data` |

## Non-Goals

- No `--apply`, `--auto`, `--fix`, `--set-status`, `--done`, `--closeout`, `--mutate`,
  `--write`, or `--push` reconcile flag.
- No Taskmaster status mutation.
- No git ref, branch, PR, Aegis closeout, repair, or workflow-state mutation.
- No executable command output.
- No automatic rollback command.
- No default candidate preview in normal reconcile reports.
