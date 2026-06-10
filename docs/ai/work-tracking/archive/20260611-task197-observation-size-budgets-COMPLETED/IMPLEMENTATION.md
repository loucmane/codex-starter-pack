# Task 197 Aegis observation report size budgets – Implementation Notes

- Baseline relocated: start_observation writes the full baseline to
  .aegis/state/observation-baseline.json; current-work.json carries baseline_ref + a
  capped baseline_summary. stop_observation hydrates it in memory
  (_load_observation_baseline) so all existing delta-comparison readers are unchanged,
  then strips the hydrated lists before persisting completed state.
- _summarize_path_lines (total + capped sample + counts-by-prefix + truncation markers)
  applied to allowed_runtime_changes and final git status; unexpected_changes keeps an
  actionable capped sample + total + truncated flag. Full enumerations written to
  .aegis/reports/observation-report-detail.json (detail_ref).
- Budgets via brief.json observation.sample_cap/prefix_cap (defaults 50/20). New report
  files added to _observation_allowed_prefixes so a clean stop stays clean.
- Detection semantics deliberately unchanged (the !!-ignored runtime mechanism already
  classifies .wrangler-class deltas) — an earlier ignore-glob detection filter was
  reverted after it changed which deltas were caught.
- Acceptance: 4000-blob runtime dir -> observation-report.json <100KB and
  current-work.json <100KB, with counts preserved and the full list in detail_ref.
