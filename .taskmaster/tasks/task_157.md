# Task ID: 157

**Title:** Harden read-only access and tracking classification

**Status:** pending

**Dependencies:** 156

**Priority:** high

**Description:** Provide sanctioned read-only Aegis accessors and fix shared read/write classification so read-only inspection is not blocked or mislabeled while write sinks remain blocked.

**Details:**

Scope: address the HPFetcher acceptance-test rough edges where read-only jq/compound Bash was blocked while readiness was BLOCKED and a post-kickoff read-only jq command created a pending implementation event. Add sanctioned read-only accessors for Aegis-owned structured outputs such as reconcile reports, doctor/status output, and reports; do not create arbitrary repo-read APIs. Ensure genuine read-only access succeeds while readiness is blocked and produces zero pending tracking. Auto-inference must never label ambiguous or read-only events as plan-step-implement; use a neutral label or require explicit resolution. Preserve conservative shell behavior: near-identical commands that add write sinks, redirects, tee, sed -i, pipe-to-writer, or python open(..., 'w') remain blocked or tracked. Acceptance: shared classifier behavior is used consistently by pretooluse gating and posttooluse tracking; jq/read-only accessor path is allowed with zero pending events; write-sink variants are refused/tracked; real implementation edits still infer implement when confidently detected; all guard and Aegis safety tests remain green.

**Test Strategy:**

No test strategy provided.
