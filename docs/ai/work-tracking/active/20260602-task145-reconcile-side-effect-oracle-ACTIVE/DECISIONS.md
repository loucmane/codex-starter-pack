# Decisions

- 2026-06-02 — Keep Task 145 strictly test-side. No reconcile mutation behavior, flags, CLI writes, or MCP mutation paths are introduced.
- 2026-06-02 — Use exact allowed-delta paths for intentional report outputs instead of excluding broad directories.
- 2026-06-02 — Protect `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`, while tolerating `.git/FETCH_HEAD` and `.git/logs/**` as read-only discovery churn in whole-tree mode.
