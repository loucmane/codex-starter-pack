# TM #197 scope — observation report size budgets

Task text: prevent observation/runtime reports ballooning on generated local-runtime
artifacts (the HP-Coach 8MB observation-report / 69MB next output dominated by
worker/.wrangler KV blob paths). Replace raw enumeration with capped samples, counts by
prefix/classification, truncation markers, explicit artifact links. Acceptance: large
runtime directories produce <100KB guidance payloads while preserving auditability.

## Implemented design (report-size only; detection semantics UNCHANGED)
- Baseline moved out of current-work.json into a linked artifact
  (.aegis/state/observation-baseline.json); current-work carries baseline_ref +
  a capped baseline_summary. stop_observation hydrates the full baseline in memory via
  _load_observation_baseline so every existing comparison reader is untouched.
- The stop report stores capped summaries (_summarize_path_lines: total + capped sample
  + counts-by-prefix + truncation markers) for allowed_runtime_changes and final git
  status; unexpected_changes keeps an actionable capped sample plus total + truncated
  flag. The FULL enumerations move to .aegis/reports/observation-report-detail.json
  (detail_ref) so nothing is silently dropped.
- Budgets configurable via brief.json {"observation": {"sample_cap", "prefix_cap"}}
  (defaults 50 / 20). New report files added to the observation allowed-prefix set so a
  clean stop stays clean.
- Deliberately NOT done: ignore-glob filtering of detection (the existing !!-ignored
  runtime mechanism already classifies .wrangler-class deltas as allowed; filtering
  before comparison would change which deltas are detected — out of scope and unsafe).
