# Task 146 Add Reconcile Precision Corpus and Boundary-Leakage Gate – Implementation Notes

## Planned Workstreams
- Added `tests/meta_workflow_guard/reconcile_precision_corpus.py` for finding normalization, pre-registered auto/manual eligibility, label validation, and precision contract assertions.
- Added `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py` to rebuild labeled fixture repositories, rerun `reconcile(...)`, reuse Task 145 whole-tree side-effect snapshots, and compute precision/boundary checks from observed output.
- Added negative tests proving manual-only labels cannot be marked auto-eligible, unlabelled auto-eligible findings fail as false positives, and expected non-findings must match observed merge-truth proof.
- Added `docs/aegis/reconcile-precision-corpus.md` and updated `docs/aegis/reconcile-promotion-contract.md` so the precision contract maps to concrete enforcing tests.
