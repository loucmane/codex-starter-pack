# Findings

- 2026-06-02 — Precision must be measured from recomputed fixture output, not static prose. The corpus now reruns reconcile and compares normalized observed findings to structured labels.
- 2026-06-02 — Boundary leakage is the critical failure mode: a manual-only ambiguity labelled auto-eligible must fail before any future mutation task can use the corpus.
- 2026-06-02 — Non-findings are part of the contract. Squash/offline unknown merge truth is explicitly labelled as a non-finding and must keep the expected proof.
