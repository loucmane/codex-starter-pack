# Decisions

- 2026-05-10 13:34 CEST — Complete Task 24 as a repo-local cost policy and static report generator. Do not implement fake live billing integrations, API client wrappers, alert delivery, caching layers, or automatic throttling without a real telemetry source and separate authorization.
- 2026-05-10 13:45 CEST — Treat missing usage input as `not-measured` warning, not as pass or fail. This keeps reports honest while allowing `--strict` to fail only on actual budget overruns supplied by a usage ledger.
