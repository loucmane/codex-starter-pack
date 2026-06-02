# Task 148 Add inert reconcile mutation-candidate preview contract – Implementation Notes

## Implemented Workstreams
- `scripts/_aegis_installer.py` now supports an opt-in
  `preview_candidates` reconcile mode. Default reconcile reports remain
  observational; the preview adds a `mutation_candidate_preview` section only
  when requested.
- Candidate preview records are inert data: `executable: false`,
  `apply_path_exists: false`, and `blocked_reason: report-only per Task 147
  contract`. They avoid command-shaped keys and values, include predicted
  blast-radius paths only as predictions, and point back to the Task 147
  rollback contract plus the Task 145 side-effect oracle.
- Candidate eligibility is restricted to `merged_but_not_done` findings with
  `git_ancestor` proof. Other findings are emitted as manual-only contract
  exclusions in preview mode.
- `aegis_foundation/cli.py`, `scripts/codex-task`, and `aegis_mcp/server.py`
  expose the preview as an explicit read-only opt-in:
  `--preview-candidates` / `preview_candidates`.
- Packaged script assets were synchronized byte-for-byte:
  `scripts/_aegis_installer.py` with
  `aegis_foundation/assets/scripts/_aegis_installer.py`, and
  `scripts/codex-task` with `aegis_foundation/assets/scripts/codex-task`.
- Added `docs/aegis/reconcile-mutation-candidate-preview-contract.md` and
  updated the promotion, precision-corpus, and rollback-contract docs so the
  preview is documented as an inert bridge, not an execution API.
- Added
  `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py`
  covering opt-in behavior, inert markers, action-shape rejection, eligibility
  boundary reuse, no writer consumption, and gate refusal for out-of-band
  Taskmaster status mutation.
