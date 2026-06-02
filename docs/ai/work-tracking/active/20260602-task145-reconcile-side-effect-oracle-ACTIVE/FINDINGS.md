# Findings

- 2026-06-02 — Reconcile read-only proof needs both whole-tree isolated fixtures and focused control-plane checks. Whole-tree mode catches unknown-location writes; focused mode protects crown-jewel workflow surfaces in larger/noisy repos.
- 2026-06-02 — `.aegis/reports/` must not be blanket-excluded. Future report-output tests should allow only the exact declared report path so unexpected report-folder writes still fail.
- 2026-06-02 — Temp git fixtures inherited global GPG signing, which made pytest commits depend on the developer passphrase cache. The fixture now disables signing locally.
