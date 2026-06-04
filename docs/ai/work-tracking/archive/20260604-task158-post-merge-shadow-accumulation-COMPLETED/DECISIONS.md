# Decisions

- 2026-06-04 — Shadow `state.json` prediction is dynamic only on the shadow evidence path; the live apply runtime keeps its existing required-state prediction until a later enablement-hardening task changes that path deliberately.
- 2026-06-04 — PR CI accumulation artifacts are diagnostics only and carry `valid_for_shadow=false`; only `push` to `refs/heads/main` can produce post-merge shadow accumulation evidence.
- 2026-06-04 — Mismatch triage is reporting-only. The accumulation job must never auto-extend canonicalization exemptions or update canonicalization versions.
- 2026-06-04 — Precision promotion evidence is keyed by `(finding_kind, proof_source)` so `git_ancestor` observations cannot imply coverage for `github_pr_merged`.
