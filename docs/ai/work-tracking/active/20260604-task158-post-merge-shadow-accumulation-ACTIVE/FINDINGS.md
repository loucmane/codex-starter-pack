# Findings

- 2026-06-04 — Full pytest initially exposed a coupling regression: changing `_predicted_paths` globally made the live apply apparatus treat legitimate `state.json` writes as live path mismatches. The fix split prediction behavior so shadow can use optional dynamic `state.json` while existing live apply callers keep the legacy required-state path.
- 2026-06-04 — The existing CI workflow already writes `reports/ci` artifacts in the workspace, so Task 158 preserves that pattern while wrapping the new accumulation step with a whole-tree side-effect oracle allowing only the declared accumulation artifact delta.
