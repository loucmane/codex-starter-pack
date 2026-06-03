# Task ID: 157

**Title:** Harden read-only access and tracking classification

**Status:** pending

**Dependencies:** 156

**Priority:** high

**Description:** Provide sanctioned read-only Aegis accessors and fix shared read/write classification so read-only inspection is not blocked or mislabeled while write sinks remain blocked.

**Details:**

Scope: address the HPFetcher acceptance-test rough edges where read-only jq/compound Bash was blocked while readiness was BLOCKED and a post-kickoff read-only jq command created a pending implementation event. Add sanctioned read-only accessors for Aegis-owned structured outputs such as reconcile reports, doctor/status output, and reports; do not create arbitrary repo-read APIs. Ensure genuine read-only access succeeds while readiness is blocked and produces zero pending tracking. Auto-inference must never label ambiguous or read-only events as plan-step-implement; use a neutral label or require explicit resolution. Preserve conservative shell behavior: near-identical commands that add write sinks, redirects, tee, sed -i, pipe-to-writer, or python open(..., 'w') remain blocked or tracked. Acceptance: shared classifier behavior is used consistently by pretooluse gating and posttooluse tracking; jq/read-only accessor path is allowed with zero pending events; write-sink variants are refused/tracked; real implementation edits still infer implement when confidently detected; all guard and Aegis safety tests remain green.
<info added on 2026-06-03T17:15:01.618Z>
Refine the sanctioned accessor design so it is structurally read-only: implement a narrow Aegis-owned projection surface for structured outputs from scripts/_aegis_installer.py and aegis_mcp/server.py, such as reconcile/status/doctor/report payloads, rather than allowing arbitrary Bash commands that merely appear to read. Keep the existing .claude/scripts/gate_lib.py Bash classifier conservative: do not broaden general jq or shell pipeline allowances, and preserve write-sink detection in redirect_targets, protected_bash_violations, bash_is_read_only, and record_pending_tracking_event. Add paired boundary tests in tests/claude_adapter/test_pretooluse_gates.py and installed-project coverage in tests/meta_workflow_guard/test_aegis_installer.py or test_aegis_mcp_e2e_targets.py proving an Aegis-owned report projection is allowed while readiness is BLOCKED and creates no .aegis/state/pending-tracking.json event, while near-identical variants using tee, output redirection, sed -i, pipe-to-writer, or python open(..., 'w') are still blocked by PreToolUse or tracked by PostToolUse as mutations.
</info added on 2026-06-03T17:15:01.618Z>

**Test Strategy:**

No test strategy provided.
