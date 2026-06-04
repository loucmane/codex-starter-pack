# Task ID: 157

**Title:** Harden read-only access and tracking classification

**Status:** in-progress

**Dependencies:** 156 ✓

**Priority:** high

**Description:** Provide sanctioned read-only Aegis accessors and fix shared read/write classification so read-only inspection is not blocked or mislabeled while write sinks remain blocked.

**Details:**

Scope: address the HPFetcher acceptance-test rough edges where read-only jq/compound Bash was blocked while readiness was BLOCKED and a post-kickoff read-only jq command created a pending implementation event. Add sanctioned read-only accessors for Aegis-owned structured outputs such as reconcile reports, doctor/status output, and reports; do not create arbitrary repo-read APIs. Ensure genuine read-only access succeeds while readiness is blocked and produces zero pending tracking. Auto-inference must never label ambiguous or read-only events as plan-step-implement; use a neutral label or require explicit resolution. Preserve conservative shell behavior: near-identical commands that add write sinks, redirects, tee, sed -i, pipe-to-writer, or python open(..., 'w') remain blocked or tracked. Acceptance: shared classifier behavior is used consistently by pretooluse gating and posttooluse tracking; jq/read-only accessor path is allowed with zero pending events; write-sink variants are refused/tracked; real implementation edits still infer implement when confidently detected; all guard and Aegis safety tests remain green.
<info added on 2026-06-03T17:15:01.618Z>
Refine the sanctioned accessor design so it is structurally read-only: implement a narrow Aegis-owned projection surface for structured outputs from scripts/_aegis_installer.py and aegis_mcp/server.py, such as reconcile/status/doctor/report payloads, rather than allowing arbitrary Bash commands that merely appear to read. Keep the existing .claude/scripts/gate_lib.py Bash classifier conservative: do not broaden general jq or shell pipeline allowances, and preserve write-sink detection in redirect_targets, protected_bash_violations, bash_is_read_only, and record_pending_tracking_event. Add paired boundary tests in tests/claude_adapter/test_pretooluse_gates.py and installed-project coverage in tests/meta_workflow_guard/test_aegis_installer.py or test_aegis_mcp_e2e_targets.py proving an Aegis-owned report projection is allowed while readiness is BLOCKED and creates no .aegis/state/pending-tracking.json event, while near-identical variants using tee, output redirection, sed -i, pipe-to-writer, or python open(..., 'w') are still blocked by PreToolUse or tracked by PostToolUse as mutations.
</info added on 2026-06-03T17:15:01.618Z>
<info added on 2026-06-04T09:01:20.820Z>
Before adding or endorsing sanctioned read-only accessors, first close the live read-surface and classifier-divergence risks. In aegis_mcp/server.py and scripts/_aegis_installer.py, confine read-only Aegis tool target_dir resolution for aegis.status, aegis.inspect, aegis.reconcile, and aegis.doctor to the governed project root/current target; reject absolute paths or .. traversal outside that root with a structured invalid_target response, and add tests proving these tools cannot inspect /etc or sibling repositories. Prefer zero-argument MCP resources/projections over caller-supplied target paths wherever practical.

Treat .claude/scripts/gate_lib.py degraded fallback classification as a third classifier that must not drift from the main PreToolUse and PostToolUse verdicts: either route all three through one shared verdict helper or add a tested invariant that degraded allow is a non-mutation subset of main allow and PostToolUse non-tracking. Add degraded-path parity tests covering Bash, Aegis MCP read-only tools, generic jq/pipelines, and write sinks. Delete substring-based plan-step-implement inference in scripts/_aegis_installer.py; infer plan-step-implement only from a positive file-mutation/write classification or an explicit plan-step argument, while read-only or ambiguous events create no pending event or only a neutral pending classification that never clears as implementation.

Harden reconcile base_ref handling in scripts/_aegis_installer.py by validating it as a ref-like value, rejecting leading dash/option-shaped values, or using -- before git rev-parse calls. Preserve conservative Bash behavior in redirect_targets, protected_bash_violations, bash_is_read_only, degraded_bash_is_non_destructive, and record_pending_tracking_event; do not generally allow jq or shell pipelines. Acceptance tests must include paired positives and negatives: sanctioned Aegis-owned projection allowed while readiness is BLOCKED with zero pending-tracking.json event and byte-identical tree; generic jq still blocked; tee, output redirection, sed -i, pipe-to-writer, and python open(..., 'w') variants remain blocked by PreToolUse or tracked by PostToolUse; reconcile preview_candidates remains inert and byte-identical at the execution layer. Review implementation internally in this order: target_dir confinement first, classifier/inference hardening second, accessor/projection polish last.
</info added on 2026-06-04T09:01:20.820Z>

**Test Strategy:**

No test strategy provided.
