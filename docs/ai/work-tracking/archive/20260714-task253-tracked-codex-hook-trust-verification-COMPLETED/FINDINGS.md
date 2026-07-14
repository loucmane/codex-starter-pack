# Findings

- 2026-07-14 — Strict `codex.hook_trust_guidance` read `.aegis/reports/install-report.json`, an intentionally ignored runtime report. A clean clone could therefore contain every correct tracked managed asset and still fail strict delivery verification.
- 2026-07-14 — The tracked `codex.hook_trust` manifest gate already carries the complete no-bypass contract: optional policy gate, Codex adapter scope, `.codex/hooks.json`, exact unsupported reason, manual verification, unsupported failure mode, and no expected automated value.
- 2026-07-14 — Exact gate validation is safer than accepting partial fields from generated evidence: a missing, duplicate, or semantically altered gate now yields no guidance and fails the existing strict check closed.
- 2026-07-14 — Blog Task 70 proved the corrected verifier passes strict verification from tracked state after the ignored install report is absent, while preserving the manual `/hooks` trust review boundary.
