# 2026-06-11 Task 197 observation size budgets

Report-size-only fix (detection unchanged): baseline -> .aegis/state/observation-baseline.json
(current-work carries baseline_ref + summary; stop hydrates in memory); report stores
capped summaries (sample+by_prefix+truncated) for allowed_runtime_changes/final status,
unexpected_changes keeps actionable sample+total; full lists in
.aegis/reports/observation-report-detail.json. Budgets via brief.json observation.*.
An ignore-glob detection filter was tried and reverted (changed detected deltas).
Acceptance: 4000 blobs -> <100KB report.
