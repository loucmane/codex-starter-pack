# Aegis Reconcile Precision Corpus

**Status:** active Task 146-148 contract.
**Scope:** keep `aegis reconcile` report-only while measuring whether any finding class is precise enough to be considered by a separate future mutation task. Task 147 adds a rollback/blast-radius proposal contract for the first candidate only. Task 148 adds an opt-in inert candidate preview. Neither task promotes reconcile into mutation.

## Contract

The precision corpus is recomputed by tests. It is not a hand-maintained prose table.

The test corpus rebuilds fixture repositories, reruns `scripts/_aegis_installer.py::reconcile`, normalizes emitted findings by stable fields (`kind`, `task_id`, merge-truth `proof`), and compares observed output with human-reviewed labels stored as structured pytest data.

## Eligibility Bar

Auto-eligible labels are pre-registered before measurement:

- `merged_but_not_done` with `git_ancestor`
- `merged_but_not_done` with `github_pr_merged`
- `done_but_not_merged` with `github_pr_open`
- `done_but_not_merged` with `github_pr_closed_unmerged`

Manual-only findings remain manual:

- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- git-only squash/offline unknown merge truth (`git_only_non_ancestor_or_missing_base`)

Acceptance for future mutation remains stricter than report usefulness: auto-eligible classes must have zero false positives and zero auto/manual boundary leaks on the labeled corpus. Manual-only ambiguity must never be labelled as auto-eligible.

Task 147 narrows the first proposal candidate further than this corpus: only
`merged_but_not_done` with `git_ancestor` proof may enter the first rollback contract.
Other auto-eligible labels, including `merged_but_not_done` with `github_pr_merged` and
`done_but_not_merged`, remain outside the first proposal set until a later task defines
their own blast-radius and rollback evidence.

Task 148 uses the same boundary for `mutation_candidate_preview`: only
`merged_but_not_done` with `git_ancestor` appears as a candidate. Other findings may appear
only as contract exclusions or manual-only records.

## Enforcing Tests

| Contract clause | Enforcing test |
| --- | --- |
| Corpus labels are recomputed from fixture execution | `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py::test_reconcile_precision_corpus_recomputes_labels_and_blocks_boundary_leaks` |
| Auto/manual boundary leaks fail | `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py::test_precision_gate_rejects_manual_only_labelled_auto_eligible` |
| Auto-eligible false positives fail | `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py::test_precision_gate_rejects_unlabelled_auto_false_positive` |
| Non-finding labels must match observed merge-truth proof | `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py::test_precision_gate_requires_non_finding_proof_labels` |
| Corpus fixture execution is read-only | Task 146 corpus test via `tests/meta_workflow_guard/reconcile_side_effect_oracle.py::snapshot_whole_tree` |
| Task 147 first mutation proposal cannot admit non-first or manual-only labels | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py::test_manual_ambiguous_and_non_first_auto_findings_cannot_enter_proposal_set` |
| Task 148 candidate preview admits only the first candidate boundary | `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py::test_preview_builder_reuses_precision_corpus_boundary` |

## Non-Goals

- No `--apply`, `--auto`, `--fix`, `--set-status`, `--done`, `--closeout`, `--mutate`, `--write`, or `--push` reconcile flag.
- No Taskmaster status mutation from reconcile.
- No git ref, branch, PR, Aegis closeout, or workflow-state mutation from reconcile.
- No auto-mutation implementation in Task 146, Task 147, or Task 148.
