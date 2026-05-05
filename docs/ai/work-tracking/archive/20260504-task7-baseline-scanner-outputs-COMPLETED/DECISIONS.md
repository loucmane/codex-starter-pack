# Decisions

- 2026-05-04 - Treat Task 7 scanner output paths and schemas as historical until current scanner evidence confirms them. The first implementation step is a scope audit, not direct output generation.
- 2026-05-04 - Use the existing Task 7 branch and active work-tracking folder until the Task 7 PR is merged and branch cleanup is confirmed. Daily sessions remain separate from task work tracking.
- 2026-05-04 - Keep raw scanner `output/data/` and generated fix scripts ignored as runtime artifacts. Commit durable Task 7 evidence under the work-tracking reports folder instead.
- 2026-05-04 - Add `baseline_summary.py` and wire `baseline_summary.json` into the scanner runner so Task 7 metrics are generated consistently instead of being hand-calculated from separate JSON files.
- 2026-05-05 - Continue in the same Task 7 active work-tracking folder across days. Do not archive or recreate it; only add fresh May 5 entries and finish final verification.
- 2026-05-05 - Archive Task 7 work tracking only after confirming the Task 7 PR merge on `main` and confirming that no local or remote Task 7 branches remain.
