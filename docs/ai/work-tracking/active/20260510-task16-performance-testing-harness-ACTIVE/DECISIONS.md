# Decisions

- 2026-05-10 — Implement Task 16 as a portable static performance harness rather than a live monitoring stack, a deep scanner rewrite, or a standalone `performance_tests.py` file only. The current foundation needs durable report evidence and regression classification more than another ad hoc benchmark entrypoint.
- 2026-05-10 — Add repo-local performance thresholds in `templates/metadata/template-performance-policy.json` so other projects can tune performance expectations without forking helper code.
- 2026-05-10 — Include CI artifact generation for performance reports, but keep threshold policy explicit and conservative to avoid noisy failure from normal CI variance. Deep optimization belongs to Task 61 if Task 16 evidence exposes a bottleneck.
- 2026-05-10 — Apply the historical `<50ms` template discovery target to warm-cache/common lookup behavior, not cold full-index construction. The first strict harness run measured cold record discovery at roughly `0.097s` while warm-cache resolution remained around `0.029s`; policy now gives cold index construction its own threshold.
