# Task 146 - Reconcile Precision Corpus and Boundary-Leakage Gate

Task 146 added a report/contract-only precision corpus for Aegis reconcile.

Key changes:
- Added `tests/meta_workflow_guard/reconcile_precision_corpus.py` with pre-registered auto-eligible proof classes, manual-only finding classes, label validation, finding normalization, and precision contract assertions.
- Added `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py` to rebuild labeled fixture repos, rerun `scripts/_aegis_installer.py::reconcile`, reuse Task 145 whole-tree snapshots, and compute precision/boundary checks from observed output.
- Added negative tests proving manual-only labels cannot be marked auto-eligible, unlabelled auto-eligible findings fail as false positives, and expected non-findings must match observed merge-truth proof.
- Added `docs/aegis/reconcile-precision-corpus.md` and updated `docs/aegis/reconcile-promotion-contract.md` to include Task 146 as the precision and boundary-leakage gate.

Verification completed:
- `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py` -> 9 passed.
- `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py tests/meta_workflow_guard/test_aegis_installer.py -k 'reconcile or precision_corpus' tests/meta_workflow_guard/test_aegis_mcp_server.py -k reconcile` -> 20 passed, 94 deselected.
- `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py` -> 113 passed, 1 skipped.

Next cleanup: log the memory in tracker with `serena/memory`, run `python3 scripts/codex-task plan sync`, then `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-guard validate`, and `python3 scripts/codex-task work-tracking audit`; mark Taskmaster Task 146 done if guards pass.