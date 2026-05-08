# Findings

- 2026-05-08 — Historical Task 45 wording is broader than the current scanner foundation needs. Task 3 already rejected multiprocessing/caching without a measured bottleneck because the cleaned full runner was fast enough.
- 2026-05-08 — Current `template_scan_results.json` metadata stats report zeros even when `scan_metadata.total_files` and `total_lines` are populated. That weakens scanner baseline comparisons and is a current-state reporting gap.
- 2026-05-08 — `collect_scannable_files()` currently walks the same directory once per supported suffix. A deterministic single traversal is the smallest safe large-scale optimization available without changing scanner output semantics.
- 2026-05-08 — The first formal profile capture generated full scanner JSON output plus a duplicate default raw output. The duplicate raw default output was removed; final evidence keeps the full metadata-wrapped profile output, the command log, and a compact `scanner-profile-summary-2026-05-08.json` for reviewability.
