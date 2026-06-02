# Task 148 - Inert reconcile mutation-candidate preview contract

Branch: `feat/task-148-inert-reconcile-preview-contract`.

Implemented an opt-in reconcile candidate preview that remains inert to autonomous agents:
- Default reconcile output stays observational.
- `--preview-candidates` / MCP `preview_candidates=true` emits `mutation_candidate_preview` only when explicitly requested.
- Candidate records are non-executable (`executable: false`, `apply_path_exists: false`, `blocked_reason: report-only per Task 147 contract`).
- Eligibility is limited to `merged_but_not_done` with `git_ancestor` proof; other findings are emitted as manual-only contract exclusions.
- Preview records include predicted blast-radius paths but defer actual blast-radius authority to the Task 145 side-effect oracle and rollback semantics to the Task 147 rollback contract.

Touched runtime surfaces:
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `scripts/codex-task`
- `aegis_mcp/server.py`
- packaged script assets under `aegis_foundation/assets/scripts/`

Docs/tests:
- Added `docs/aegis/reconcile-mutation-candidate-preview-contract.md`.
- Updated reconcile promotion, precision corpus, and rollback contract docs.
- Added `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py`.

Verification completed:
- Focused reconcile suite: 63 passed, 94 deselected.
- Full `tests/meta_workflow_guard`: 665 passed, 4 skipped.
- Black check passed for touched Python files.
- Ruff passed for the new Task 148 test module.
- Packaged assets are byte-identical to their source copies.